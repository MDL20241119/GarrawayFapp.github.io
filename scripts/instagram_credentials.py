"""Rotate the Garraway F Instagram Login token without exposing credentials."""

import argparse
from dataclasses import dataclass, field
import getpass
from http.client import HTTPException
import json
import os
import re
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
import warnings


ACCOUNT = "garrawayf_lounge"
HOST = "https://graph.instagram.com"
API_VERSION = "v27.0"
REPOSITORY = "MDL20241119/GarrawayFapp.github.io"
TOKEN_SECRET = "INSTAGRAM_ACCESS_TOKEN"
USER_ID_SECRET = "INSTAGRAM_USER_ID"
WRITER_SECRET = "INSTAGRAM_SECRET_WRITER_TOKEN"
BOOTSTRAP_VARIABLE = "INSTAGRAM_TOKEN_BOOTSTRAPPED_AT"
ONE_DAY = 86_400
RENEWAL_MARGIN = 15 * ONE_DAY
MAX_ATTEMPTS = 3
MAX_RETRY_DELAY = 30
MAX_RESPONSE = 65_536
MAX_TOKEN_LENGTH = 40_000


class CredentialError(Exception):
    """A fixed, non-sensitive operational state."""

    def __init__(self, state):
        super().__init__(state)
        self.state = state


@dataclass(frozen=True)
class Credentials:
    access_token: str = field(repr=False)
    expires_at: int | None = None
    refreshed_at: int | None = None

    def safe_metadata(self):
        return {"expires_at": self.expires_at, "refreshed_at": self.refreshed_at}


def _positive_int(value):
    return type(value) is int and value > 0


def _token(value):
    if not isinstance(value, str) or len(value) > MAX_TOKEN_LENGTH or not re.fullmatch(r"[A-Za-z0-9._~+/-]+=*", value):
        raise CredentialError("invalid_credentials")
    return value


def load_credentials(raw):
    """Read the original raw secret or the atomic token-and-expiration object."""
    if not isinstance(raw, str) or not raw.strip():
        raise CredentialError("missing_credentials")
    raw = raw.strip()
    if not raw.startswith("{"):
        return Credentials(_token(raw))
    try:
        payload = json.loads(raw)
    except (ValueError, RecursionError):
        raise CredentialError("invalid_credentials") from None
    if not isinstance(payload, dict) or set(payload) != {"access_token", "expires_at", "refreshed_at"}:
        raise CredentialError("invalid_credentials")
    expiry, issued = payload["expires_at"], payload["refreshed_at"]
    if not _positive_int(issued) or not _positive_int(expiry) or expiry <= issued:
        raise CredentialError("invalid_credentials")
    return Credentials(_token(payload["access_token"]), expiry, issued)


def _rotation_due(credentials, *, now, force, bootstrap_at):
    if credentials.expires_at is not None and now >= credentials.expires_at:
        raise CredentialError("reauthorization_required")
    issued = credentials.refreshed_at if credentials.refreshed_at is not None else bootstrap_at
    if issued is not None:
        if not _positive_int(issued) or issued > now:
            raise CredentialError("invalid_bootstrap_time")
        if now - issued < ONE_DAY:
            if force:
                raise CredentialError("token_too_new")
            return False
    if force:
        return True
    if credentials.expires_at is not None:
        return now >= credentials.expires_at - RENEWAL_MARGIN
    # The first renewal establishes the actual expiry for a dashboard-issued token.
    return bootstrap_at is not None


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _error_state(status, payload):
    error = payload.get("error", {}) if isinstance(payload, dict) else {}
    code = error.get("code") if isinstance(error, dict) else None
    if 300 <= status < 400:
        return "redirect_rejected"
    if status == 401 or code in (102, 190):
        return "reauthorization_required"
    if status == 429 or code in (4, 17, 32, 613):
        return "rate_limited"
    if status == 403 or code in (10, 200, 294):
        return "permission_denied"
    if status >= 500 or code in (1, 2):
        return "api_unavailable"
    return "api_request_rejected"


def _request_json(path, fields, *, opener, sleep):
    # Meta documents access_token as a request parameter for these Instagram
    # endpoints. The request and HTTP error are never printed or chained.
    request = Request(f"{HOST}/{path}?{urlencode(fields)}", headers={"Accept": "application/json"})
    retryable = {"rate_limited", "api_unavailable", "network_error"}
    for attempt in range(MAX_ATTEMPTS):
        retry_after = 0
        try:
            with opener(request, timeout=15) as response:
                raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:
                raise CredentialError("invalid_api_response")
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise CredentialError("invalid_api_response")
            if "error" not in payload:
                return payload
            state = _error_state(200, payload)
        except HTTPError as error:
            try:
                with error:
                    payload = json.loads(error.read(MAX_RESPONSE))
            except (ValueError, RecursionError, OSError, HTTPException):
                payload = {}
            state = _error_state(error.code, payload)
            if error.headers is not None:
                delay = error.headers.get("Retry-After", "")
                if re.fullmatch(r"[0-9]{1,9}", delay):
                    retry_after = int(delay)
                elif delay:
                    # Defer a retry rather than retry before an HTTP-date or a long delay.
                    retry_after = MAX_RETRY_DELAY + 1
        except (URLError, OSError, HTTPException):
            state = "network_error"
        except (ValueError, RecursionError):
            raise CredentialError("invalid_api_response") from None
        if state not in retryable or attempt == MAX_ATTEMPTS - 1 or retry_after > MAX_RETRY_DELAY:
            raise CredentialError(state) from None
        sleep(max(2 ** (attempt + 1), retry_after))
    raise CredentialError("invalid_api_response")


def _verify_account(payload, user_id):
    if set(payload) == {"data"}:
        payload = payload["data"]
        if isinstance(payload, list) and len(payload) == 1:
            payload = payload[0]
    if not isinstance(payload, dict):
        raise CredentialError("account_mismatch")
    username = payload.get("username")
    identifiers = {
        str(value) for value in (payload.get("user_id"), payload.get("id"))
        if isinstance(value, str) or type(value) is int
    }
    if not isinstance(username, str) or username.lower() != ACCOUNT or user_id not in identifiers:
        raise CredentialError("account_mismatch")


def rotate_credentials(credentials, user_id, *, force=False, bootstrap_at=None,
                       clock=time.time, opener=None, sleep=time.sleep, save=None):
    """Refresh when due, verify the new token's account and atomically save it.

    Force for a raw token with unknown age is the operator's confirmation that it
    was issued at least 24 hours ago. When the age is known, also enforce it here.
    """
    started_at = int(clock())
    if not _rotation_due(credentials, now=started_at, force=force, bootstrap_at=bootstrap_at):
        return None
    if save is None:
        raise CredentialError("writer_not_configured")
    if not isinstance(user_id, str) or not re.fullmatch(r"[0-9]{1,32}", user_id):
        raise CredentialError("invalid_account_id")
    if opener is None:
        opener = build_opener(ProxyHandler({}), _NoRedirect()).open

    response = _request_json("refresh_access_token", {
        "grant_type": "ig_refresh_token",
        "access_token": credentials.access_token,
    }, opener=opener, sleep=sleep)
    lifetime = response.get("expires_in")
    if not _positive_int(lifetime) or response.get("token_type", "bearer") != "bearer":
        raise CredentialError("invalid_api_response")
    try:
        renewed_token = _token(response.get("access_token"))
    except CredentialError:
        raise CredentialError("invalid_api_response") from None
    # The request start gives a conservative expiry. The receipt time ensures
    # a subsequent refresh is never attempted inside Meta's 24-hour minimum.
    renewed = Credentials(renewed_token, started_at + lifetime, int(clock()))
    if renewed.expires_at <= renewed.refreshed_at:
        raise CredentialError("invalid_api_response")
    identity = _request_json(f"{API_VERSION}/me", {
        "fields": "user_id,username",
        "access_token": renewed.access_token,
    }, opener=opener, sleep=sleep)
    _verify_account(identity, user_id)
    if int(clock()) >= renewed.expires_at:
        raise CredentialError("invalid_api_response")
    try:
        save(renewed)
    except OSError:
        raise CredentialError("secret_write_failed") from None
    return renewed


def save_github_secret(credentials, *, writer_token=None, use_gh_auth=False, run=subprocess.run):
    if not writer_token and not use_gh_auth:
        raise CredentialError("writer_not_configured")
    env = os.environ.copy()
    for name in (TOKEN_SECRET, USER_ID_SECRET, WRITER_SECRET, "GH_TOKEN", "GITHUB_TOKEN",
                 "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN", "GH_DEBUG"):
        env.pop(name, None)
    env.update({"GH_HOST": "github.com", "GH_PROMPT_DISABLED": "1"})
    if not use_gh_auth:
        env["GH_TOKEN"] = writer_token
    secret_value = json.dumps({"access_token": credentials.access_token, **credentials.safe_metadata()})
    command = ["gh", "secret", "set", TOKEN_SECRET, "--repo", REPOSITORY]
    try:
        completed = run(command, input=secret_value.encode(), env=env, stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL, timeout=45, check=False)
    except (OSError, subprocess.SubprocessError):
        raise CredentialError("secret_write_failed") from None
    if completed.returncode != 0:
        raise CredentialError("secret_write_failed")


class _SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise CredentialError("invalid_arguments")


def _read_input(name, prompt, *, interactive):
    value = os.environ.get(name, "")
    if value or not interactive:
        return value
    if not sys.stdin.isatty():
        raise CredentialError("secure_input_unavailable")
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        try:
            return getpass.getpass(prompt)
        except (getpass.GetPassWarning, EOFError, KeyboardInterrupt, OSError):
            raise CredentialError("secure_input_unavailable") from None


def main(argv=None):
    parser = _SafeArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Confirm a known valid token is at least 24 hours old.")
    parser.add_argument("--use-gh-auth", action="store_true", help="Use the local GitHub CLI login with --force.")
    credentials = None
    try:
        args = parser.parse_args(argv)
        if args.use_gh_auth and not args.force:
            raise CredentialError("invalid_arguments")
        credentials = load_credentials(_read_input(TOKEN_SECRET, "Current Instagram token: ", interactive=args.use_gh_auth))
        user_id = _read_input(USER_ID_SECRET, "Instagram professional account ID: ", interactive=args.use_gh_auth)
        bootstrap = os.environ.get(BOOTSTRAP_VARIABLE, "")
        if bootstrap and not re.fullmatch(r"[0-9]{1,12}", bootstrap):
            raise CredentialError("invalid_bootstrap_time")
        writer = os.environ.get(WRITER_SECRET, "")
        save = None
        if writer or args.use_gh_auth:
            def save(renewed):
                save_github_secret(renewed, writer_token=writer, use_gh_auth=args.use_gh_auth)

        updated = rotate_credentials(credentials, user_id, force=args.force,
                                     bootstrap_at=int(bootstrap) if bootstrap else None, save=save)
        if updated is not None:
            credentials, state = updated, "rotated"
        else:
            state = "not_due" if credentials.expires_at is not None else "expiry_unverified"
        exit_code = 0
    except CredentialError as error:
        state, exit_code = error.state, 1
    metadata = credentials.safe_metadata() if credentials is not None else {}
    print(json.dumps({"state": state, **metadata}))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
