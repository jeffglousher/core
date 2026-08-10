"""RFC 8628 device authorization helpers for SpaceXAI."""

import asyncio
from dataclasses import dataclass
import time
from typing import Any

from aiohttp import ClientError, ClientResponse, ClientTimeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DEVICE_CODE_MAX_POLL_SECONDS,
    DEVICE_CODE_URL,
    HTTP_TIMEOUT_SECONDS,
    OAUTH_SCOPES,
    TOKEN_URL,
)
from .errors import (
    AuthenticationRejectedError,
    ConnectionFailureError,
    ErrorContext,
    MalformedProviderResponseError,
    Operation,
    PermanentProviderError,
    RateLimitedError,
    RequestTimeoutError,
    SpaceXAIError,
    TransientProviderError,
)

DEVICE_CODE_GRANT = "urn:ietf:params:oauth:grant-type:device_code"
_HTTP_TIMEOUT = ClientTimeout(total=HTTP_TIMEOUT_SECONDS)
_MIN_POLL_INTERVAL = 1
_MAX_POLL_INTERVAL = 30
_SLOW_DOWN_INCREMENT = 5


@dataclass(frozen=True, slots=True)
class DeviceAuthorization:
    """Values returned by the SpaceXAI device authorization endpoint."""

    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str
    expires_in: int
    interval: int


async def async_request_device_authorization(
    hass: HomeAssistant,
    *,
    client_id: str,
    scope: str = " ".join(OAUTH_SCOPES),
) -> DeviceAuthorization:
    """Start an RFC 8628 device authorization request."""
    session = async_get_clientsession(hass)
    context = ErrorContext(operation=Operation.DEVICE_AUTH)
    try:
        async with session.post(
            DEVICE_CODE_URL,
            data={"client_id": client_id, "scope": scope},
            headers={"Accept": "application/json"},
            timeout=_HTTP_TIMEOUT,
        ) as response:
            payload = await _async_json_payload(response, context)
            if response.status >= 400:
                _raise_device_http_error(response.status, payload, context)
    except SpaceXAIError:
        raise
    except TimeoutError as err:
        raise RequestTimeoutError(
            "Device authorization request timed out", context=context
        ) from err
    except ClientError as err:
        raise ConnectionFailureError(
            "Could not reach the SpaceXAI device authorization endpoint",
            context=context,
        ) from err

    try:
        return DeviceAuthorization(
            device_code=str(payload["device_code"]),
            user_code=str(payload["user_code"]),
            verification_uri=str(payload["verification_uri"]),
            verification_uri_complete=str(
                payload.get("verification_uri_complete") or payload["verification_uri"]
            ),
            expires_in=int(payload["expires_in"]),
            interval=max(_MIN_POLL_INTERVAL, int(payload.get("interval", 5))),
        )
    except (KeyError, TypeError, ValueError) as err:
        raise MalformedProviderResponseError(
            "Device authorization response was incomplete",
            context=context,
        ) from err


async def async_poll_device_token(
    hass: HomeAssistant,
    *,
    client_id: str,
    device_code: str,
    expires_in: int,
    interval: int,
) -> dict[str, Any]:
    """Poll the token endpoint until the user approves the device code."""
    session = async_get_clientsession(hass)
    context = ErrorContext(operation=Operation.DEVICE_AUTH)
    deadline = time.monotonic() + max(1, min(expires_in, DEVICE_CODE_MAX_POLL_SECONDS))
    poll_interval = max(_MIN_POLL_INTERVAL, interval)

    while time.monotonic() < deadline:
        try:
            async with session.post(
                TOKEN_URL,
                data={
                    "grant_type": DEVICE_CODE_GRANT,
                    "client_id": client_id,
                    "device_code": device_code,
                },
                headers={"Accept": "application/json"},
                timeout=_HTTP_TIMEOUT,
            ) as response:
                payload = await _async_json_payload(response, context)
                if response.status == 200:
                    return _validated_token_payload(payload, context)

                error_code = str(payload.get("error") or "")
                if error_code == "authorization_pending":
                    await asyncio.sleep(poll_interval)
                    continue
                if error_code == "slow_down":
                    poll_interval = min(
                        _MAX_POLL_INTERVAL,
                        poll_interval + _SLOW_DOWN_INCREMENT,
                    )
                    await asyncio.sleep(poll_interval)
                    continue
                if error_code in {"access_denied", "authorization_denied"}:
                    raise AuthenticationRejectedError(
                        "The SpaceXAI account denied device authorization",
                        context=context,
                    )
                if error_code == "expired_token":
                    raise RequestTimeoutError(
                        "The SpaceXAI device code expired before approval",
                        context=context,
                    )
                _raise_device_http_error(response.status, payload, context)
        except SpaceXAIError:
            raise
        except TimeoutError as err:
            raise RequestTimeoutError(
                "Device token polling timed out", context=context
            ) from err
        except ClientError as err:
            raise ConnectionFailureError(
                "Could not reach the SpaceXAI token endpoint",
                context=context,
            ) from err

    raise RequestTimeoutError(
        "The SpaceXAI device code expired before approval",
        context=context,
    )


async def _async_json_payload(
    response: ClientResponse, context: ErrorContext
) -> dict[str, Any]:
    """Parse a JSON object body, allowing empty error bodies."""
    try:
        payload = await response.json(content_type=None)
    except ValueError as err:
        raise MalformedProviderResponseError(
            "Device authorization response was not JSON",
            context=context,
        ) from err
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise MalformedProviderResponseError(
            "Device authorization response was not an object",
            context=context,
        )
    return payload


def _validated_token_payload(
    payload: dict[str, Any], context: ErrorContext
) -> dict[str, Any]:
    """Require access and refresh tokens from a successful device grant."""
    access_token = payload.get("access_token")
    refresh_token = payload.get("refresh_token")
    expires_in = payload.get("expires_in")
    if (
        not isinstance(access_token, str)
        or not access_token
        or not isinstance(refresh_token, str)
        or not refresh_token
    ):
        raise MalformedProviderResponseError(
            "Device token response omitted required tokens",
            context=context,
        )
    if expires_in is None:
        raise MalformedProviderResponseError(
            "Device token response omitted expires_in",
            context=context,
        )
    try:
        expires_in_int = int(expires_in)
    except (TypeError, ValueError) as err:
        raise MalformedProviderResponseError(
            "Device token response omitted expires_in",
            context=context,
        ) from err
    token = dict(payload)
    token["expires_in"] = expires_in_int
    token["expires_at"] = time.time() + expires_in_int
    token.setdefault("token_type", "Bearer")
    return token


def _raise_device_http_error(
    status: int, payload: dict[str, Any], context: ErrorContext
) -> None:
    """Map device-authorization HTTP failures to typed errors."""
    provider_code = payload.get("error")
    enriched = ErrorContext(
        operation=context.operation,
        status=status,
        provider_code=str(provider_code) if provider_code is not None else None,
    )
    if status in {401, 403} or provider_code in {
        "invalid_client",
        "unauthorized_client",
    }:
        raise AuthenticationRejectedError(
            "SpaceXAI rejected the Home Assistant OAuth client",
            context=enriched,
        )
    if status == 429:
        raise RateLimitedError(
            "SpaceXAI rate limited the device authorization request",
            context=enriched,
        )
    if status == 408 or status >= 500:
        raise TransientProviderError(
            "SpaceXAI device authorization is temporarily unavailable",
            context=enriched,
        )
    raise PermanentProviderError(
        "SpaceXAI rejected the device authorization request",
        context=enriched,
    )
