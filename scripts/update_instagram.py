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
from instagram_credentials import CredentialError, load_credentials

Image.MAX_IMAGE_PIXELS = 50_000_000
ACCOUNT = "garrawayf_lounge"
HOST = "https://graph.instagram.com"
DEFAULT_API_VERSION = "v27.0"
FIELDS = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp"
IMAGE_FIELDS = "id,media_type,media_url,thumbnail_url"
CDN_HOSTS = ("cdninstagram.com", "fbcdn.net")
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
        self.info["action_required"] = category in {
            "authentication", "permission", "configuration", "account_mismatch", "caption_unavailable",
        }
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


class InstagramRedirect(urllib.request.HTTPRedirectHandler):
    """Limit redirects before a request can reach another host or plain HTTP."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlsplit(req.full_url).hostname == "graph.instagram.com":
            valid_url(newurl, ("graph.instagram.com",), "redirect", exact_host=True)
        else:
            valid_url(newurl, CDN_HOSTS, "redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class Client:
    def __init__(self, token, uid, *, version=DEFAULT_API_VERSION, opener=None, sleep=time.sleep, log=print):
        self.token, self.uid = token, uid
        self.version = version
        self.secrets = (token, uid)
        self.opener = opener if opener is not None else urllib.request.build_opener(InstagramRedirect()).open
        self.sleep, self.log = sleep, log
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
        if not re.fullmatch(r"v[1-9][0-9]*\.0", self.version):
            raise FeedError("configuration", "api_version")
        # Query strings and response bodies must never be printed.
        query["access_token"] = self.token
        stage = path.rsplit("/", 1)[-1]
        raw = self.read(f"{HOST}/{self.version}/{path}?{urllib.parse.urlencode(query)}", stage,
                        timeout=30, limit=2_000_000, api=True)
        try:
            payload = json.loads(raw)
        except (ValueError, UnicodeError):
            raise FeedError("invalid_json", stage) from None
        if not isinstance(payload, dict):
            raise FeedError("invalid_response", stage)
        if "error" in payload:
            raise api_error(200, payload, stage, self.secrets)
        return payload

    def media(self):
        payload = self.get(f"{self.uid}/media", fields=FIELDS, limit="25")
        if not isinstance(payload.get("data"), list):
            raise FeedError("invalid_response", "media")
        return payload["data"]

    def carousel_cover(self, post_id):
        payload = self.get(f"{post_id}/children", fields=IMAGE_FIELDS, limit="1")
        children = payload.get("data")
        if not isinstance(children, list) or not children or not isinstance(children[0], dict):
            raise FeedError("invalid_response", "children")
        cover = children[0]
        if cover.get("media_type") not in {"IMAGE", "VIDEO"}:
            raise FeedError("invalid_response", "children")
        return cover

    def account(self):
        payload = self.get("me", fields="user_id,username,account_type")
        if "data" in payload:
            records = payload["data"]
            if not isinstance(records, list) or len(records) != 1 or not isinstance(records[0], dict):
                raise FeedError("invalid_response", "me")
            payload = records[0]
        # user_id identifies the professional account. The app-scoped id is
        # distinct and cannot identify the account for the /<IG_ID>/media edge.
        account_id = payload.get("user_id")
        username = payload.get("username")
        if (type(account_id) not in {int, str} or str(account_id) != self.uid
                or not isinstance(username, str) or username.lower() != ACCOUNT):
            raise FeedError("account_mismatch", "account")
        result = {"account_verified": True, "api_host": "graph.instagram.com", "endpoint_family": "instagram_login"}
        if "account_type" in payload:
            account_type = str(payload["account_type"]).upper()
            if account_type not in {"BUSINESS", "MEDIA_CREATOR"}:
                raise FeedError("account_mismatch", "account")
            result["account_type"] = account_type
        return result


def valid_url(value, hosts, stage, *, exact_host=False):
    if not isinstance(value, str) or any(ord(character) < 33 for character in value):
        raise FeedError("invalid_response", stage)
    try:
        parsed = urllib.parse.urlsplit(value)
        host = parsed.hostname or ""
        allowed = host in hosts or (not exact_host and any(host.endswith("." + domain) for domain in hosts))
        if parsed.scheme != "https" or parsed.username is not None or parsed.password is not None or parsed.port not in {None, 443} or not allowed:
            raise ValueError("unexpected origin")
    except ValueError:
        raise FeedError("invalid_response", stage) from None
    return value


def parse_timestamp(value):
    if not isinstance(value, str):
        raise FeedError("invalid_response", "timestamp")
    try:
        stamp = datetime.fromisoformat(value)
        if stamp.tzinfo is None:
            raise ValueError("missing timezone")
        return stamp.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise FeedError("invalid_response", "timestamp") from None


def selected_posts(candidates, minimum):
    unique = {}
    for post in candidates:
        if not isinstance(post, dict):
            raise FeedError("invalid_response", "media")
        identity = post.get("id")
        if not isinstance(identity, str) or not re.fullmatch(r"\d{1,30}", identity):
            raise FeedError("invalid_response", "media")
        if post.get("media_type") not in {"IMAGE", "VIDEO", "CAROUSEL_ALBUM"} or post.get("is_story") is True or post.get("media_product_type") == "STORY":
            raise FeedError("invalid_response", "media")
        stamp = parse_timestamp(post.get("timestamp"))
        valid_url(post.get("permalink"), ["instagram.com"], "permalink")
        if "caption" in post and not isinstance(post["caption"], str):
            raise FeedError("invalid_response", "caption")
        unique.setdefault(identity, {**post, "timestamp": stamp.isoformat().replace("+00:00", "+0000")})
    if len(unique) < minimum:
        raise FeedError("empty_or_incomplete_response", "media")
    if not any("caption" in post for post in unique.values()):
        raise FeedError("caption_unavailable", "media")
    return sorted(unique.values(), key=lambda post: (post["timestamp"], post["id"]), reverse=True)[:MAX_POSTS]


def optimized_image(client, post):
    if post["media_type"] == "CAROUSEL_ALBUM":
        post = client.carousel_cover(post["id"])
    field = "thumbnail_url" if post["media_type"] == "VIDEO" else "media_url"
    url = valid_url(post.get(field), CDN_HOSTS, "image_url")
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
    images = [IMAGES / path.name for path in (stage / IMAGES).iterdir()]
    targets = [*images, FEED, STATUS]
    existing_images = list((root / IMAGES).glob("*"))
    backup = {path: (root / path).read_bytes() if (root / path).is_file() else None for path in targets}
    backup.update({path.relative_to(root): path.read_bytes() for path in existing_images if path.is_file()})
    try:
        # Images precede JSON; remove old images only after every new reference validates.
        for path in [*images, FEED]:
            atomic_write(root / path, (stage / path).read_bytes())
        validate_bundle(root, feed)
        kept = {post["image"] for post in feed["posts"]}
        for path in existing_images:
            if path.is_file() and path.relative_to(root).as_posix() not in kept:
                path.unlink()
        atomic_write(root / STATUS, (stage / STATUS).read_bytes())
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


def update(root, client, *, now=None, credential=None, blocked=None):
    now = now or utcnow()
    previous = read_dict(root / FEED)
    prior_status = read_dict(root / STATUS)
    api_version = client.version if re.fullmatch(r"v[1-9][0-9]*\.0", client.version) else None
    status = {"checked_at": now, "state": "failure", "content_updated_at": previous.get("updated_at"),
              "last_fetch_succeeded_at": prior_status.get("last_fetch_succeeded_at"),
              "api_host": "graph.instagram.com", "api_version": api_version}
    if "publication" in prior_status:
        status["publication"] = prior_status["publication"]
    if credential:
        status["credential"] = credential
    if blocked:
        # An operator can dispatch after fixing authentication. Scheduled runs
        # keep their own heartbeat and don't contact Meta with the same bad token.
        status["job_checked_at"] = now
        status["checked_at"] = prior_status.get("checked_at") or now
        status["api_attempted"] = False
    try:
        if blocked:
            raise blocked
        status["api_attempted"] = True
        if not client.token or not re.fullmatch(r"\d{1,30}", client.uid):
            raise FeedError("configuration", "secrets")
        status["authentication"] = client.account()
        previous_posts = previous.get("posts", [])
        previous_count = len(previous_posts) if isinstance(previous_posts, list) else 0
        minimum = max(MIN_POSTS, min(MAX_POSTS, previous_count))
        candidates = selected_posts(client.media(), minimum)

        with tempfile.TemporaryDirectory(prefix=".instagram-stage-", dir=root) as directory:
            stage = Path(directory)
            (stage / IMAGES).mkdir(parents=True)
            posts = []
            for post in candidates:
                content = optimized_image(client, post)
                image = (IMAGES / f"{post['id']}.jpg").as_posix()
                (stage / image).write_bytes(content)
                posts.append({"id": post["id"], "caption": post.get("caption", ""), "media_type": post["media_type"],
                              "is_story": False, "image": image, "image_version": hashlib.sha256(content).hexdigest()[:12],
                              "permalink": post["permalink"], "timestamp": post["timestamp"]})
            changed = posts != previous_posts
            feed = {"account": ACCOUNT, "sort": "newest_first", "includes_collaborative_posts": False,
                    "includes_tagged_posts": False, "includes_stories": False,
                    "updated_at": now if changed else previous.get("updated_at", now), "posts": posts}
            serialized = encode(feed)
            secret_forms = {form for secret in client.secrets if secret for form in (secret, urllib.parse.quote(secret, safe=""), urllib.parse.quote_plus(secret))}
            if any(form.encode() in serialized for form in secret_forms):
                raise FeedError("credential_in_response", "validation")
            feed_hash = hashlib.sha256(serialized).hexdigest()
            completed = {**status, "state": "success", "last_fetch_succeeded_at": now,
                         "content_updated_at": feed["updated_at"], "content_changed": changed,
                         "posts": len(posts), "feed_sha256": feed_hash,
                         "observed_api_versions": sorted(client.versions),
                         "publication": {
                             "schema_version": 1, "feed_sha256": feed_hash,
                             "latest_post_at": parse_timestamp(posts[0]["timestamp"]).isoformat().replace("+00:00", "Z"),
                         }}
            (stage / FEED).parent.mkdir(parents=True)
            (stage / FEED).write_bytes(serialized)
            (stage / STATUS).write_bytes(encode(completed))
            install_bundle(root, stage, feed)
        status = completed
        code = 0
    except FeedError as error:
        status["error"] = error.info
        if error.info["stage"] in {"me", "account"}:
            status["authentication"] = {"account_verified": False, "error": error.info}
        code = 1
    except Exception:
        # Unexpected parser, image, filesystem, and transport errors must not leak URLs or bodies.
        status["error"] = FeedError("internal", "update").info
        code = 1
    if code:
        status["observed_api_versions"] = sorted(client.versions)
        atomic_write(root / STATUS, encode(status))
    client.log(json.dumps(status, ensure_ascii=False))
    return code, status


def credential_gate(credential, previous, event_name, now):
    if credential.get("expires_at") is not None and credential["expires_at"] <= now:
        return FeedError("authentication", "secrets", error={"message": "Stored expiry passed; reauthorize."})
    if event_name != "schedule":
        return None
    previous_error = previous.get("error", {})
    if previous_error.get("category") not in {"authentication", "permission"}:
        return None
    previous_credential = previous.get("credential", {})
    if any(credential.get(field) != previous_credential.get(field)
           for field in ("refreshed_at", "bootstrap_at")):
        return None
    return FeedError(previous_error["category"], "secrets", http_status=previous_error.get("http_status"),
                     error={**previous_error, "message": "Credential requires a verified manual recovery run."})


def main():
    root = Path(__file__).resolve().parents[1]
    token, metadata = "", {}
    prior_status = read_dict(root / STATUS)
    try:
        credential = load_credentials(os.environ.get("INSTAGRAM_ACCESS_TOKEN", ""))
        token, metadata = credential.access_token, credential.safe_metadata()
        bootstrap = os.environ.get("INSTAGRAM_TOKEN_BOOTSTRAPPED_AT", "")
        if re.fullmatch(r"[0-9]{1,12}", bootstrap):
            metadata["bootstrap_at"] = int(bootstrap)
        blocked = credential_gate(metadata, prior_status, os.environ.get("GITHUB_EVENT_NAME"), time.time())
    except CredentialError as error:
        blocked = FeedError("configuration", "secrets", error={"message": error.state})
    client = Client(token, os.environ.get("INSTAGRAM_USER_ID", ""),
                    version=os.environ.get("INSTAGRAM_API_VERSION") or DEFAULT_API_VERSION)
    code, status = update(root, client, credential=metadata, blocked=blocked)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as output:
            output.write("## Instagram feed sync\n\n```json\n" + encode(status).decode() + "```\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
