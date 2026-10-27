"""Fetch the approved Instagram feed without exposing credentials or losing a good snapshot.

Only a validated bundle is installed. Git commits publish that bundle atomically;
the separate sync status may be committed even when this command exits nonzero.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = 50_000_000
ACCOUNT = "garrawayf_lounge"
HOST = "https://graph.instagram.com"
FIELDS = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp"
MIN_POSTS, MAX_POSTS, MAX_ATTEMPTS = 4, 6, 3
FEED = Path("data/instagram.json")
STATUS = Path("data/instagram-sync-status.json")
IMAGES = Path("images/instagram")


def utcnow():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def sanitize(value, secrets=()):
    text = str(value or "")
    for secret in secrets:
        if secret:
            for form in {secret, urllib.parse.quote(secret, safe=""), urllib.parse.quote_plus(secret)}:
                text = text.replace(form, "[redacted]")
    text = re.sub(r"https?://[^\s<>\"']+", "[URL redacted]", text, flags=re.I)
    text = re.sub(r"(?i)(access_token|input_token|client_secret|authorization)\s*[:=]\s*[^\s,;]+", r"\1=[redacted]", text)
    text = re.sub(r"(?i)bearer\s+\S+", "Bearer [redacted]", text)
    text = re.sub(r"\b[A-Za-z0-9_\-]{32,}\b|\b\d{9,}\b", "[redacted]", text)
    return re.sub(r"[\x00-\x1f\x7f]", " ", text)[:500]


class FeedError(Exception):
    def __init__(self, category, stage, *, http_status=None, error=None, secrets=()):
        error = error if isinstance(error, dict) else {}
        self.info = {"stage": stage, "category": category, "http_status": http_status}
        for key in ("code", "error_subcode"):
            self.info[key] = error.get(key) if type(error.get(key)) is int else None
        self.info["is_transient"] = error.get("is_transient") if type(error.get("is_transient")) is bool else None
        for key in ("type", "fbtrace_id"):
            value = error.get(key)
            self.info[key] = sanitize(value, secrets) if isinstance(value, str) and re.fullmatch(r"[\w.\-]{1,100}", value) else None
        self.info["message"] = sanitize(error.get("message", category.replace("_", " ")), secrets)
        self.info["action_required"] = category in {"authentication", "permission", "configuration", "account_mismatch"}
        self.retryable = category in {"timeout", "network", "rate_limit", "server", "transient"}
        super().__init__(category)  # Never attach an HTTPError, URL, body, or header.


def api_error(status, payload, stage, secrets):
    error = payload.get("error", {}) if isinstance(payload, dict) else {}
    error = error if isinstance(error, dict) else {}
    code = error.get("code")
    if code in {102, 190} or status == 401:
        category = "authentication"
    elif code in {10, 200, 294} or status == 403:
        category = "permission"
    elif code in {4, 17, 32, 613} or status == 429:
        category = "rate_limit"
    elif status is not None and status >= 500:
        category = "server"
    elif error.get("is_transient") is True:
        category = "transient"
    elif code == 100:
        category = "request"
    else:
        category = "api"
    return FeedError(category, stage, http_status=status, error=error, secrets=secrets)


class Client:
    def __init__(self, token, uid, *, opener=urllib.request.urlopen, sleep=time.sleep, log=print):
        self.token, self.uid = token, uid
        self.secrets = (token, uid)
        self.opener, self.sleep, self.log = opener, sleep, log
        self.versions = set()

    def read(self, url, stage, *, timeout, limit, api):
        for attempt in range(1, MAX_ATTEMPTS + 1):
            retry_after = 0
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "GarrawayF-feed/3.0"})
                with self.opener(request, timeout=timeout) as response:
                    content = response.read(limit + 1)
                    if api:
                        version = response.headers.get("facebook-api-version", response.headers.get("instagram-api-version", ""))
                        if re.fullmatch(r"v\d{1,3}\.\d{1,2}", version):
                            self.versions.add(version)
                if len(content) > limit:
                    raise FeedError("oversized_response", stage)
                return content
            except urllib.error.HTTPError as error:
                # Read only a bounded error object. Never log the exception or raw body.
                try:
                    payload = json.loads(error.read(65_536)) if api else {}
                except (ValueError, UnicodeError, OSError):
                    payload = {}
                try:
                    retry_after = min(60, max(0, int(error.headers.get("Retry-After", "0"))))
                except (ValueError, TypeError, AttributeError):
                    retry_after = 0
                failure = api_error(error.code, payload, stage, self.secrets)
                error.close()
            except (TimeoutError, socket.timeout):
                failure = FeedError("timeout", stage)
            except urllib.error.URLError as error:
                failure = FeedError("timeout" if isinstance(error.reason, TimeoutError) else "network", stage)
            except OSError:
                failure = FeedError("network", stage)
            self.log(json.dumps({"attempt": attempt, **failure.info}, ensure_ascii=False))
            if not failure.retryable or attempt == MAX_ATTEMPTS:
                raise failure from None
            self.sleep(max(2 ** attempt, retry_after))
        raise AssertionError("unreachable")

    def get(self, path, **query):
        # Keep the working authentication transport and unversioned endpoint.
        # Query strings and response bodies must never be printed.
        query["access_token"] = self.token
        raw = self.read(f"{HOST}/{path}?{urllib.parse.urlencode(query)}", path.rsplit("/", 1)[-1], timeout=30, limit=2_000_000, api=True)
        try:
            payload = json.loads(raw)
        except (ValueError, UnicodeError):
            raise FeedError("invalid_json", path.rsplit("/", 1)[-1]) from None
        if not isinstance(payload, dict):
            raise FeedError("invalid_response", path.rsplit("/", 1)[-1])
        if "error" in payload:
            raise api_error(200, payload, path.rsplit("/", 1)[-1], self.secrets)
        return payload

    def media(self, edge):
        payload = self.get(f"{self.uid}/{edge}", fields=FIELDS, limit="25")
        if not isinstance(payload.get("data"), list):
            raise FeedError("invalid_response", edge)
        return payload["data"]

    def account(self):
        payload = self.get("me", fields="user_id,username")
        identities = {str(payload.get(key, "")) for key in ("id", "user_id")}
        if self.uid not in identities or str(payload.get("username", "")).lower() != ACCOUNT:
            raise FeedError("account_mismatch", "account")
        return {"account_verified": True, "api_host": "graph.instagram.com", "endpoint_family": "instagram_login"}


def valid_url(value, hosts, stage):
    if not isinstance(value, str):
        raise FeedError("invalid_response", stage)
    parsed = urllib.parse.urlsplit(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in {None, 443} or not any(host == h or host.endswith("." + h) for h in hosts):
        raise FeedError("invalid_response", stage)
    return value


def selected_posts(candidates):
    unique = {}
    for post in candidates:
        if not isinstance(post, dict):
            raise FeedError("invalid_response", "media")
        identity = post.get("id")
        if not isinstance(identity, str) or not re.fullmatch(r"\d{1,30}", identity):
            raise FeedError("invalid_response", "media")
        if post.get("media_type") not in {"IMAGE", "VIDEO", "CAROUSEL_ALBUM"} or post.get("is_story") is True or post.get("media_product_type") == "STORY":
            raise FeedError("invalid_response", "media")
        try:
            stamp = datetime.fromisoformat(post["timestamp"].replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                raise ValueError("missing timezone")
        except (KeyError, TypeError, ValueError, AttributeError):
            raise FeedError("invalid_response", "timestamp") from None
        valid_url(post.get("permalink"), ["instagram.com"], "permalink")
        if "caption" in post and not isinstance(post["caption"], str):
            raise FeedError("invalid_response", "caption")
        unique.setdefault(identity, (stamp, post))
    posts = [pair[1] for pair in sorted(unique.values(), key=lambda pair: pair[0], reverse=True)[:MAX_POSTS]]
    if len(posts) < MIN_POSTS:
        raise FeedError("empty_or_incomplete_response", "media")
    return posts


def optimized_image(client, post):
    url = valid_url(post.get("thumbnail_url") or post.get("media_url"), ["cdninstagram.com", "fbcdn.net"], "image_url")
    raw = client.read(url, "image", timeout=45, limit=5_000_000, api=False)
    try:
        with Image.open(BytesIO(raw)) as source:
            image = ImageOps.exif_transpose(source)
            image.thumbnail((1080, 1080), Image.Resampling.LANCZOS)
            if image.mode != "RGB":
                image = image.convert("RGB")
            output = BytesIO()
            image.save(output, format="JPEG", quality=82, optimize=True, progressive=True)
            return output.getvalue()
    except Exception:
        raise FeedError("invalid_image", "image") from None


def validate_bundle(root, feed):
    posts = feed.get("posts", [])
    if not MIN_POSTS <= len(posts) <= MAX_POSTS:
        raise FeedError("invalid_bundle", "validation")
    timestamps = []
    for post in posts:
        expected = f"images/instagram/{post['id']}.jpg"
        if post.get("image") != expected or not re.fullmatch(r"\d{1,30}", str(post["id"])):
            raise FeedError("invalid_bundle", "validation")
        content = (root / expected).read_bytes()
        if post.get("image_version") != hashlib.sha256(content).hexdigest()[:12]:
            raise FeedError("image_hash_mismatch", "validation")
        with Image.open(BytesIO(content)) as image:
            image.verify()
        timestamps.append(datetime.fromisoformat(post["timestamp"].replace("Z", "+00:00")))
    if timestamps != sorted(timestamps, reverse=True):
        raise FeedError("invalid_bundle", "validation")


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_bytes(content)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def install_bundle(root, stage, feed):
    validate_bundle(stage, feed)
    targets = [FEED] + [IMAGES / p.name for p in (stage / IMAGES).iterdir()]
    existing_images = list((root / IMAGES).glob("*"))
    backup = {path: (root / path).read_bytes() if (root / path).is_file() else None for path in targets}
    backup.update({path.relative_to(root): path.read_bytes() for path in existing_images if path.is_file()})
    try:
        # Images precede JSON; remove old images only after every new reference validates.
        for path in targets[1:] + targets[:1]:
            atomic_write(root / path, (stage / path).read_bytes())
        validate_bundle(root, feed)
        kept = {post["image"] for post in feed["posts"]}
        for path in existing_images:
            if path.is_file() and path.relative_to(root).as_posix() not in kept:
                path.unlink()
    except Exception:
        for path, content in backup.items():
            if content is None:
                (root / path).unlink(missing_ok=True)
            else:
                # Independent restoration also works if atomic_write was the failing operation.
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                (root / path).write_bytes(content)
        raise


def read_dict(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError, UnicodeError):
        return {}


def update(root, client, *, now=None):
    now = now or utcnow()
    previous = read_dict(root / FEED)
    prior_status = read_dict(root / STATUS)
    status = {"checked_at": now, "state": "failure", "content_updated_at": previous.get("updated_at"),
              "last_fetch_succeeded_at": prior_status.get("last_fetch_succeeded_at"),
              "api_host": "graph.instagram.com", "api_version": "unversioned (existing configuration)"}
    try:
        if not client.token or not re.fullmatch(r"\d{1,30}", client.uid):
            raise FeedError("configuration", "secrets")
        candidates = client.media("media")
        # Empty/malformed normal media must not be hidden by optional data.
        selected_posts(candidates)
        status["authentication"] = client.account()
        collaborative_available = False
        try:
            collaborative = client.media("collaborative_media")
            selected_posts(candidates + collaborative)
            candidates.extend(collaborative)
            collaborative_available = True
            status["collaborative_media"] = {"state": "available"}
        except FeedError as error:
            status["collaborative_media"] = {"state": "unavailable", "error": error.info}
            client.log(json.dumps({"optional_edge": True, **error.info}, ensure_ascii=False))

        with tempfile.TemporaryDirectory(prefix=".instagram-stage-", dir=root) as directory:
            stage = Path(directory)
            (stage / IMAGES).mkdir(parents=True)
            posts = []
            for post in selected_posts(candidates):
                content = optimized_image(client, post)
                image = (IMAGES / f"{post['id']}.jpg").as_posix()
                (stage / image).write_bytes(content)
                posts.append({"id": post["id"], "caption": post.get("caption", ""), "media_type": post["media_type"],
                              "is_story": False, "image": image, "image_version": hashlib.sha256(content).hexdigest()[:12],
                              "permalink": post["permalink"], "timestamp": post["timestamp"]})
            changed = posts != previous.get("posts", [])
            feed = {"account": ACCOUNT, "sort": "newest_first", "includes_collaborative_posts": collaborative_available,
                    "includes_tagged_posts": False, "includes_stories": False,
                    "updated_at": now if changed else previous.get("updated_at", now), "posts": posts}
            serialized = encode(feed)
            secret_forms = {form for secret in client.secrets if secret for form in (secret, urllib.parse.quote(secret, safe=""), urllib.parse.quote_plus(secret))}
            if any(form.encode() in serialized for form in secret_forms):
                raise FeedError("credential_in_response", "validation")
            (stage / FEED).parent.mkdir(parents=True)
            (stage / FEED).write_bytes(serialized)
            install_bundle(root, stage, feed)
        status.update(state="success", last_fetch_succeeded_at=now, content_updated_at=feed["updated_at"], content_changed=changed,
                      posts=len(posts), feed_sha256=hashlib.sha256(serialized).hexdigest())
        code = 0
    except FeedError as error:
        status["error"] = error.info
        # A separate identity probe distinguishes bad tokens from media field / UID errors.
        if error.info["stage"] != "secrets":
            try:
                status["authentication"] = client.account()
            except FeedError as identity_error:
                status["authentication"] = {"account_verified": False, "error": identity_error.info}
        code = 1
    except Exception:
        # Unexpected parser, image, filesystem, and transport errors must not leak URLs or bodies.
        status["error"] = FeedError("internal", "update").info
        code = 1
    status["observed_api_versions"] = sorted(client.versions)
    atomic_write(root / STATUS, encode(status))
    client.log(json.dumps(status, ensure_ascii=False))
    return code, status


def main():
    root = Path(__file__).resolve().parents[1]
    client = Client(os.environ.get("INSTAGRAM_ACCESS_TOKEN", ""), os.environ.get("INSTAGRAM_USER_ID", ""))
    code, status = update(root, client)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as output:
            output.write("## Instagram feed sync\n\n```json\n" + encode(status).decode() + "```\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
