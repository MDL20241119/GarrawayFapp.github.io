"""Offline tests for token renewal and its storage contract."""

from contextlib import redirect_stderr, redirect_stdout
from io import BytesIO, StringIO
import json
import os
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

import instagram_credentials as auth


NOW = 1_794_725_333
LIFETIME = 5_183_944
USER_ID = "17841409300998765"
ORIGINAL = "original-test-token-secret"
RENEWED = "renewed-test-token-secret"
WRITER = "github-test-writer-secret"


def response(payload):
    return BytesIO(json.dumps(payload).encode())


def http_error(request, status, code=None, retry_after=None):
    headers = {} if retry_after is None else {"Retry-After": retry_after}
    data = {"error": {"code": code, "message": f"private {ORIGINAL} {RENEWED} {WRITER}", "is_transient": True}}
    return HTTPError(request.full_url, status, f"private {ORIGINAL}", headers, response(data))


class MockGraph:
    def __init__(self):
        self.requests = []
        self.refresh = {"access_token": RENEWED, "token_type": "bearer", "expires_in": LIFETIME}
        self.profile = {"user_id": USER_ID, "username": auth.ACCOUNT}
        self.failure = None

    def open(self, request, timeout):
        url = urlsplit(request.full_url)
        self.requests.append((request.get_method(), url.scheme, url.netloc, url.path, parse_qs(url.query), timeout))
        if self.failure:
            raise self.failure(request)
        return response(self.refresh if url.path == "/refresh_access_token" else self.profile)


class CredentialTests(unittest.TestCase):
    def setUp(self):
        self.api = MockGraph()
        self.saved = []
        self.sleeps = []
        self.raw = auth.load_credentials(ORIGINAL)

    def rotate(self, credentials=None, **options):
        settings = {"clock": lambda: NOW, "opener": self.api.open, "sleep": self.sleeps.append,
                    "save": self.saved.append, **options}
        return auth.rotate_credentials(credentials or self.raw, USER_ID, **settings)

    def assert_safe(self, value):
        for secret in (ORIGINAL, RENEWED, WRITER, USER_ID):
            self.assertNotIn(secret, str(value))

    def test_legacy_and_measured_credentials(self):
        self.assertEqual(self.raw.safe_metadata(), {"expires_at": None, "refreshed_at": None})
        self.assert_safe(repr(self.raw))
        envelope = json.dumps({"access_token": RENEWED, "expires_at": NOW + LIFETIME, "refreshed_at": NOW})
        loaded = auth.load_credentials(envelope)
        self.assertEqual(loaded.access_token, RENEWED)
        self.assertEqual(loaded.safe_metadata(), {"expires_at": NOW + LIFETIME, "refreshed_at": NOW})
        self.assert_safe(repr(loaded))

    def test_malformed_envelope_never_becomes_raw_token(self):
        for raw in ('{"access_token":"x"', '{"access_token":"x"}', '["secret"]',
                    json.dumps({"access_token": ORIGINAL, "expires_at": NOW, "refreshed_at": True}),
                    json.dumps({"access_token": ORIGINAL, "expires_at": NOW, "refreshed_at": NOW + 1})):
            with self.subTest(shape=type(raw)), self.assertRaisesRegex(auth.CredentialError, "^invalid_credentials$"):
                auth.load_credentials(raw)

    def test_safe_schedule_guards(self):
        self.assertIsNone(self.rotate())
        self.assertIsNone(self.rotate(bootstrap_at=NOW - auth.ONE_DAY + 1))
        newer = auth.Credentials(ORIGINAL, NOW + LIFETIME, NOW - auth.ONE_DAY + 1)
        with self.assertRaisesRegex(auth.CredentialError, "^token_too_new$"):
            self.rotate(newer, force=True)
        live = auth.Credentials(ORIGINAL, NOW + auth.RENEWAL_MARGIN + 1, NOW - 30 * auth.ONE_DAY)
        self.assertIsNone(self.rotate(live))
        expired = auth.Credentials(ORIGINAL, NOW, NOW - LIFETIME)
        with self.assertRaisesRegex(auth.CredentialError, "^reauthorization_required$"):
            self.rotate(expired, force=True)
        with self.assertRaisesRegex(auth.CredentialError, "^invalid_bootstrap_time$"):
            self.rotate(bootstrap_at=NOW + 1)
        self.assertEqual(self.api.requests, [])

    def test_due_on_exact_margin_and_saves_after_account_verification(self):
        live = auth.Credentials(ORIGINAL, NOW + auth.RENEWAL_MARGIN, NOW - 30 * auth.ONE_DAY)
        self.api.profile = {"id": int(USER_ID), "username": auth.ACCOUNT.upper()}

        def save(renewed):
            self.assertEqual(len(self.api.requests), 2)
            self.assertEqual(self.api.requests[1][:4], ("GET", "https", "graph.instagram.com", "/v27.0/me"))
            self.saved.append(renewed)

        renewed = self.rotate(live, save=save)
        self.assertEqual(self.saved, [renewed])
        self.assertEqual(renewed.access_token, RENEWED)
        self.assertEqual(renewed.safe_metadata(), {"expires_at": NOW + LIFETIME, "refreshed_at": NOW})
        self.assertEqual(self.api.requests[0], ("GET", "https", "graph.instagram.com", "/refresh_access_token",
                         {"grant_type": ["ig_refresh_token"], "access_token": [ORIGINAL]}, 15))
        self.assertEqual(self.api.requests[1][4]["access_token"], [RENEWED])
        self.assert_safe(renewed)

    def test_bootstrap_only_rotates_when_at_least_one_day_old(self):
        self.api.profile = {"data": [{"id": USER_ID, "username": auth.ACCOUNT}]}
        times = iter((NOW, NOW + 5, NOW + 10))
        renewed = self.rotate(bootstrap_at=NOW - auth.ONE_DAY, clock=lambda: next(times))
        self.assertEqual(renewed.expires_at, NOW + LIFETIME)
        self.assertEqual(renewed.refreshed_at, NOW + 5)
        self.assertEqual(len(self.saved), 1)

    def test_no_rotation_without_explicit_writer(self):
        with self.assertRaisesRegex(auth.CredentialError, "^writer_not_configured$"):
            self.rotate(force=True, save=None)
        self.assertEqual(self.api.requests, [])

    def test_different_identity_is_never_saved(self):
        for identity in ({"user_id": USER_ID, "username": "wrong"}, {"id": "10", "username": auth.ACCOUNT},
                         {"data": [{"id": USER_ID, "username": auth.ACCOUNT}, {"id": "10"}]}):
            self.api.profile = identity
            with self.assertRaisesRegex(auth.CredentialError, "^account_mismatch$"):
                self.rotate(force=True)
        self.assertEqual(self.saved, [])

    def test_missing_or_invalid_refresh_expiry_is_never_saved(self):
        for lifespan in (None, 0, -1, True, "5183944"):
            self.api.refresh["expires_in"] = lifespan
            with self.assertRaisesRegex(auth.CredentialError, "^invalid_api_response$"):
                self.rotate(force=True)
        self.assertEqual(self.saved, [])

    def test_redirects_auth_and_permission_failures_do_not_retry(self):
        for status, code, state in ((302, None, "redirect_rejected"), (400, 190, "reauthorization_required"),
                                    (403, 10, "permission_denied")):
            self.api.requests.clear()
            self.api.failure = lambda request: http_error(request, status, code)
            with self.assertRaisesRegex(auth.CredentialError, f"^{state}$") as caught:
                self.rotate(force=True)
            self.assertEqual(len(self.api.requests), 1)
            self.assert_safe(caught.exception)
            self.assertIsNone(caught.exception.__cause__)
        self.assertEqual(self.sleeps, [])
        self.assertEqual(self.saved, [])
        self.assertIsNone(auth._NoRedirect().redirect_request(None, None, 302, "Found", {}, "https://other.test/"))

    def test_429_5xx_and_failed_network_have_bounded_retries(self):
        cases = ((lambda request: http_error(request, 429, 4, "5"), "rate_limited", [5, 5]),
                 (lambda request: http_error(request, 503, 2), "api_unavailable", [2, 4]),
                 (lambda request: URLError(f"private {ORIGINAL}"), "network_error", [2, 4]),
                 (lambda request: http_error(request, 429, 4, "60"), "rate_limited", []))
        for failure, state, delays in cases:
            self.api.requests.clear()
            self.sleeps.clear()
            self.api.failure = failure
            with self.assertRaisesRegex(auth.CredentialError, f"^{state}$") as caught:
                self.rotate(force=True)
            self.assert_safe(caught.exception)
            self.assertEqual(len(self.api.requests), len(delays) + 1)
            self.assertEqual(self.sleeps, delays)
        self.assertEqual(self.saved, [])

    def test_github_write_is_atomic_stdin_and_distinct_load_is_usable(self):
        renewed = self.rotate(force=True)
        fake_run = Mock(return_value=SimpleNamespace(returncode=0))
        values = {auth.TOKEN_SECRET: ORIGINAL, auth.USER_ID_SECRET: USER_ID, auth.WRITER_SECRET: WRITER,
                  "GH_TOKEN": "inherited", "GITHUB_TOKEN": "inherited", "GH_DEBUG": "api"}
        with patch.dict(os.environ, values):
            auth.save_github_secret(renewed, writer_token=WRITER, run=fake_run)
        argv, kwargs = fake_run.call_args
        self.assertEqual(argv[0], ["gh", "secret", "set", "INSTAGRAM_ACCESS_TOKEN", "--repo", auth.REPOSITORY])
        self.assert_safe(argv)
        self.assertEqual(kwargs["env"]["GH_TOKEN"], WRITER)
        for name in values:
            if name != "GH_TOKEN":
                self.assertNotIn(name, kwargs["env"])
        self.assertEqual(kwargs["stdout"], subprocess.DEVNULL)
        self.assertEqual(kwargs["stderr"], subprocess.DEVNULL)
        self.assertEqual(auth.load_credentials(kwargs["input"].decode()), renewed)

    def test_github_local_login_is_explicit_and_does_not_use_inherited_tokens(self):
        renewed = self.rotate(force=True)
        fake_run = Mock(return_value=SimpleNamespace(returncode=0))
        with patch.dict(os.environ, {"GH_TOKEN": WRITER, "GITHUB_TOKEN": WRITER}):
            auth.save_github_secret(renewed, writer_token=WRITER, use_gh_auth=True, run=fake_run)
        self.assertNotIn("GH_TOKEN", fake_run.call_args.kwargs["env"])
        self.assertNotIn("GITHUB_TOKEN", fake_run.call_args.kwargs["env"])
        with self.assertRaisesRegex(auth.CredentialError, "^secret_write_failed$") as caught:
            auth.save_github_secret(renewed, writer_token=WRITER, run=Mock(side_effect=OSError(WRITER)))
        self.assert_safe(caught.exception)

    def test_cli_outputs_only_safe_states_and_requires_force_for_local_login(self):
        for argv, expected in ((["--use-gh-auth"], "invalid_arguments"), ([ORIGINAL], "invalid_arguments"),
                               (["--force"], "writer_not_configured")):
            out, err = StringIO(), StringIO()
            with patch.dict(os.environ, {auth.TOKEN_SECRET: ORIGINAL, auth.USER_ID_SECRET: USER_ID}, clear=True):
                with redirect_stdout(out), redirect_stderr(err):
                    self.assertEqual(auth.main(argv), 1)
            self.assert_safe(out.getvalue() + err.getvalue())
            self.assertEqual(json.loads(out.getvalue())["state"], expected)


if __name__ == "__main__":
    unittest.main()
