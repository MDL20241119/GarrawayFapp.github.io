from __future__ import annotations

import copy
import hashlib
import json
import socket
import tempfile
import unittest
import urllib.error
import urllib.parse
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import update_instagram as sync

TOKEN = "secret-access-token-must-never-appear-123456789"
UID = "12345678901234567"
T0, T1 = "2026-10-26T00:00:00Z", "2026-10-28T00:00:00Z"


def image_bytes(color="red"):
    out = BytesIO()
    Image.new("RGB", (1400, 1200), color).save(out, format="PNG")
    return out.getvalue()


class Response(BytesIO):
    def __init__(self, content, headers=None):
        super().__init__(content)
        self.headers = headers or {"facebook-api-version": "v25.0"}


def http_error(status, code=100, **extra):
    # Deliberately hostile error/URL/header contents exercise the logging boundary.
    error = {"type": "OAuthException", "code": code, "error_subcode": 463,
             "fbtrace_id": "safeTrace-123", "is_transient": False,
             "message": f"Problem for {UID}, access_token={TOKEN} https://example.test/?access_token={TOKEN}", **extra}
    return urllib.error.HTTPError(f"https://graph.instagram.com/{UID}/media?access_token={TOKEN}", status,
                                  TOKEN, {"Authorization": f"Bearer {TOKEN}"}, BytesIO(json.dumps({"error": error}).encode()))


class API:
    def __init__(self):
        self.posts = [{"id": str(1000 + i), "timestamp": f"2026-10-{20 + i:02d}T01:00:00+0000",
                       "caption": f"Post {i}", "media_type": "IMAGE",
                       "permalink": f"https://www.instagram.com/p/post{i}/",
                       "media_url": f"https://scontent.cdninstagram.com/{1000+i}.png"} for i in range(6)]
        self.media_failure = None
        self.media_payload = None
        self.image_failure = None
        self.image_calls = 0
        self.collaborative = []
        self.collaborative_failure = None
        self.username = sync.ACCOUNT
        self.calls = []
        self.image = image_bytes()
        self.failures_left = None

    def __call__(self, request, timeout):
        url = urllib.parse.urlsplit(request.full_url)
        self.calls.append((url.path, timeout))
        if url.hostname.endswith("cdninstagram.com"):
            self.image_calls += 1
            if self.image_failure and self.image_calls >= 2:
                raise self.image_failure()
            return Response(self.image)
        if url.path.endswith("/collaborative_media"):
            if self.collaborative_failure:
                raise self.collaborative_failure()
            return Response(json.dumps({"data": self.collaborative}).encode())
        if url.path == "/me":
            return Response(json.dumps({"user_id": UID, "username": self.username}).encode())
        if url.path.endswith("/media"):
            if self.media_failure and self.failures_left != 0:
                if self.failures_left is not None:
                    self.failures_left -= 1
                raise self.media_failure()
            return Response(self.media_payload if self.media_payload is not None else json.dumps({"data": self.posts}).encode())
        raise AssertionError("unexpected API route")


class FeedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.api = API()
        self.logs, self.sleeps = [], []
        self.client = sync.Client(TOKEN, UID, opener=self.api, sleep=self.sleeps.append, log=self.logs.append)
        code, _ = sync.update(self.root, self.client, now=T0)
        self.assertEqual(code, 0)
        self.logs.clear()
        self.api.calls.clear()
        self.api.image_calls = 0
        self.baseline = self.snapshot()

    def tearDown(self):
        self.tmp.cleanup()

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*")
                if p.is_file() and p.relative_to(self.root) != sync.STATUS}

    def run_update(self):
        code, status = sync.update(self.root, self.client, now=T1)
        for secret in [TOKEN, UID, urllib.parse.quote(TOKEN, safe="")]:
            self.assertNotIn(secret, "\n".join(self.logs))
            self.assertNotIn(secret, (self.root / sync.STATUS).read_text())
        self.assertNotIn("Authorization", "\n".join(self.logs))
        return code, status

    def preserved_failure(self, category):
        code, status = self.run_update()
        self.assertEqual(code, 1)
        self.assertEqual(status["state"], "failure")
        self.assertEqual(status["error"]["category"], category)
        self.assertEqual(status["last_fetch_succeeded_at"], T0)
        self.assertEqual(self.snapshot(), self.baseline)
        self.assertEqual(list(self.root.glob(".instagram-stage-*")), [])
        return status

    def test_success_newest_six_and_optimized_hashes(self):
        self.api.posts.append({**self.api.posts[-1], "id": "2000", "timestamp": "2026-10-28T03:00:00+0000"})
        code, status = self.run_update()
        self.assertEqual(code, 0)
        feed = json.loads((self.root / sync.FEED).read_text())
        self.assertEqual(feed["posts"][0]["id"], "2000")
        self.assertEqual(len(feed["posts"]), 6)
        self.assertEqual(feed["updated_at"], T1)
        self.assertEqual(status["last_fetch_succeeded_at"], T1)
        self.assertEqual(status["observed_api_versions"], ["v25.0"])
        self.assertFalse((self.root / sync.IMAGES / "1000.jpg").exists())
        for p in feed["posts"]:
            raw = (self.root / p["image"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest()[:12], p["image_version"])
            with Image.open(BytesIO(raw)) as image:
                self.assertLessEqual(max(image.size), 1080)
                self.assertEqual(image.format, "JPEG")
                self.assertEqual(image.mode, "RGB")
        self.assertFalse(feed["includes_tagged_posts"])
        self.assertFalse(feed["includes_stories"])

    def test_unchanged_content_preserves_updated_at_but_advances_success(self):
        code, status = self.run_update()
        self.assertEqual(code, 0)
        self.assertEqual(self.snapshot(), self.baseline)
        self.assertFalse(status["content_changed"])
        self.assertEqual(status["content_updated_at"], T0)
        self.assertEqual(status["last_fetch_succeeded_at"], T1)

    def test_caption_only_change_updates_content_time(self):
        self.api.posts[-1]["caption"] = "Changed caption"
        self.assertEqual(self.run_update()[0], 0)
        self.assertEqual(json.loads((self.root / sync.FEED).read_text())["updated_at"], T1)

    def test_image_content_hash_changes_without_id_change(self):
        self.api.image = image_bytes("blue")
        before = json.loads((self.root / sync.FEED).read_text())["posts"][0]["image_version"]
        self.assertEqual(self.run_update()[0], 0)
        after = json.loads((self.root / sync.FEED).read_text())["posts"][0]["image_version"]
        self.assertNotEqual(before, after)

    def test_authentication_error_is_not_retried(self):
        self.api.media_failure = lambda: http_error(400, 190, is_transient=True)
        status = self.preserved_failure("authentication")
        self.assertTrue(status["error"]["action_required"])
        self.assertEqual(status["error"]["code"], 190)
        self.assertEqual(status["error"]["error_subcode"], 463)
        self.assertEqual(status["error"]["fbtrace_id"], "safeTrace-123")
        self.assertEqual(self.sleeps, [])
        self.assertEqual(sum(path.endswith("/media") for path, _ in self.api.calls), 1)

    def test_permission_error_is_not_retried(self):
        self.api.media_failure = lambda: http_error(403, 10)
        self.assertTrue(self.preserved_failure("permission")["error"]["action_required"])
        self.assertEqual(self.sleeps, [])

    def test_timeout_has_bounded_backoff(self):
        self.api.media_failure = lambda: socket.timeout(TOKEN)
        self.preserved_failure("timeout")
        self.assertEqual(self.sleeps, [2, 4])

    def test_urlerror_does_not_log_its_url_or_reason(self):
        self.api.media_failure = lambda: urllib.error.URLError(f"https://example.test/?access_token={TOKEN}")
        self.preserved_failure("network")
        self.assertEqual(self.sleeps, [2, 4])

    def test_rate_limit_has_bounded_backoff(self):
        self.api.media_failure = lambda: http_error(429, 4)
        self.preserved_failure("rate_limit")
        self.assertEqual(self.sleeps, [2, 4])

    def test_server_errors_have_bounded_backoff(self):
        self.api.media_failure = lambda: http_error(503, 2)
        self.preserved_failure("server")
        self.assertEqual(self.sleeps, [2, 4])

    def test_transient_400_has_bounded_backoff(self):
        self.api.media_failure = lambda: http_error(400, 2, is_transient=True)
        self.preserved_failure("transient")
        self.assertEqual(self.sleeps, [2, 4])

    def test_transient_failure_can_recover(self):
        self.api.media_failure = lambda: http_error(502, 2)
        self.api.failures_left = 1
        self.assertEqual(self.run_update()[0], 0)
        self.assertEqual(self.sleeps, [2])

    def test_empty_and_incomplete_normal_feed_preserved(self):
        for payload in [{"data": []}, {"data": self.api.posts[:3]}]:
            with self.subTest(count=len(payload["data"])):
                self.api.media_payload = json.dumps(payload).encode()
                self.preserved_failure("empty_or_incomplete_response")

    def test_invalid_json_and_response_shapes_preserved(self):
        for payload, category in [(b"not-json", "invalid_json"), (b"", "invalid_json"),
                                  (b"[]", "invalid_response"), (b"{}", "invalid_response"),
                                  (b'{"data":null}', "invalid_response"), (b'{"data":[null]}', "invalid_response")]:
            with self.subTest(payload=payload):
                self.api.media_payload = payload
                self.preserved_failure(category)

    def test_image_failure_after_one_staged_image_preserves_all(self):
        self.api.image = image_bytes("green")
        self.api.image_failure = lambda: http_error(404)
        self.preserved_failure("api")
        self.assertEqual(self.api.image_calls, 2)

    def test_invalid_image_preserves_all(self):
        self.api.image = b"not-an-image-" + TOKEN.encode()
        self.preserved_failure("invalid_image")

    def test_missing_image_url_preserves_all(self):
        self.api.posts[-1].pop("media_url")
        self.preserved_failure("invalid_response")

    def test_unsupported_collaborative_edge_does_not_block_normal(self):
        self.api.collaborative_failure = lambda: http_error(400, 100, message="Unsupported edge collaborative_media")
        self.api.posts[-1]["caption"] = "New normal content"
        code, status = self.run_update()
        self.assertEqual(code, 0)
        self.assertEqual(status["collaborative_media"]["state"], "unavailable")
        self.assertFalse(json.loads((self.root / sync.FEED).read_text())["includes_collaborative_posts"])
        self.assertEqual(self.sleeps, [])

    def test_empty_collaborative_edge_is_valid(self):
        self.assertEqual(self.run_update()[0], 0)

    def test_collaborative_posts_deduplicated_and_sorted(self):
        self.api.collaborative = [self.api.posts[-1], {**self.api.posts[-1], "id": "3000", "timestamp": "2026-10-28T04:00:00+0000"}]
        self.assertEqual(self.run_update()[0], 0)
        posts = json.loads((self.root / sync.FEED).read_text())["posts"]
        self.assertEqual(posts[0]["id"], "3000")
        self.assertEqual(len({post["id"] for post in posts}), 6)

    def test_wrong_account_preserves_all(self):
        self.api.username = "another_account"
        self.preserved_failure("account_mismatch")

    def test_invalid_fields_and_story_rejected(self):
        for key, value in [("id", "../bad"), ("timestamp", "yesterday"), ("timestamp", "2026-10-28"),
                           ("caption", {}), ("is_story", True), ("media_type", "STORY"),
                           ("permalink", "https://example.test/redirect")]:
            with self.subTest(key=key, value=value):
                original = copy.deepcopy(self.api.posts)
                self.api.posts[-1][key] = value
                self.preserved_failure("invalid_response")
                self.api.posts = original

    def test_reflected_token_in_caption_is_never_published(self):
        self.api.posts[-1]["caption"] = TOKEN
        self.preserved_failure("credential_in_response")

    def test_reflected_account_secret_is_never_published(self):
        self.api.posts[-1]["caption"] = UID
        self.preserved_failure("credential_in_response")

    def test_oversized_image_preserves_all(self):
        self.api.image = b"x" * 5_000_001
        self.preserved_failure("oversized_response")

    def test_http_400_field_error_is_not_retried(self):
        self.api.media_failure = lambda: http_error(400, 100)
        self.preserved_failure("request")
        self.assertEqual(self.sleeps, [])

    def test_retry_after_is_respected_and_capped(self):
        def failure():
            error = http_error(429, 4)
            error.headers["Retry-After"] = "9999"
            return error
        self.api.media_failure = failure
        self.preserved_failure("rate_limit")
        self.assertEqual(self.sleeps, [60, 60])

    def test_optional_server_failure_is_bounded_and_normal_updates(self):
        self.api.collaborative_failure = lambda: http_error(503, 2)
        code, status = self.run_update()
        self.assertEqual(code, 0)
        self.assertEqual(status["collaborative_media"]["error"]["category"], "server")
        self.assertEqual(self.sleeps, [2, 4])

    def test_invalid_staged_hash_never_installs(self):
        def fail_validation(root, feed):
            raise sync.FeedError("image_hash_mismatch", "validation")
        self.api.image = image_bytes("green")
        with patch.object(sync, "validate_bundle", side_effect=fail_validation):
            self.preserved_failure("image_hash_mismatch")

    def test_expired_identity_probe_cannot_log_secrets(self):
        self.api.media_failure = lambda: http_error(400, 190)
        original = self.client.account
        self.client.account = lambda: (_ for _ in ()).throw(sync.api_error(400, {"error": {"code": 190, "message": TOKEN}}, "me", (TOKEN, UID)))
        status = self.preserved_failure("authentication")
        self.assertFalse(status["authentication"]["account_verified"])
        self.client.account = original

    def test_missing_secrets_fail_without_network(self):
        self.client.token = ""
        self.preserved_failure("configuration")
        self.assertEqual(self.api.calls, [])

    def test_promotion_failure_restores_json_and_images(self):
        self.api.image = image_bytes("blue")
        original = sync.atomic_write
        count = 0

        def fail_second(path, content):
            nonlocal count
            if str(path).endswith(".jpg"):
                count += 1
                if count == 2:
                    raise OSError(TOKEN)
            return original(path, content)

        with patch.object(sync, "atomic_write", side_effect=fail_second):
            self.preserved_failure("internal")

    def test_no_raw_body_logged_on_non_json_api_error(self):
        def bad_response():
            return urllib.error.HTTPError("https://example.test/" + TOKEN, 400, TOKEN, {}, BytesIO(TOKEN.encode()))
        self.api.media_failure = bad_response
        self.preserved_failure("api")

    def test_first_failure_does_not_invent_last_success(self):
        (self.root / sync.STATUS).unlink()
        self.api.media_failure = lambda: http_error(400, 190)
        self.assertIsNone(self.preserved_first_failure()["last_fetch_succeeded_at"])

    def preserved_first_failure(self):
        code, status = self.run_update()
        self.assertEqual(code, 1)
        self.assertEqual(self.snapshot(), self.baseline)
        return status


if __name__ == "__main__":
    unittest.main()
