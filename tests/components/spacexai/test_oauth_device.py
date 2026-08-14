"""Tests for SpaceXAI device authorization helpers."""

from http import HTTPStatus
from unittest.mock import AsyncMock, patch

from aiohttp import ClientError
import pytest

from homeassistant.components.spacexai.const import DEVICE_CODE_URL, TOKEN_URL
from homeassistant.components.spacexai.errors import (
    AuthenticationRejectedError,
    ConnectionFailureError,
    MalformedProviderResponseError,
    PermanentProviderError,
    RateLimitedError,
    RequestTimeoutError,
    TransientProviderError,
)
from homeassistant.components.spacexai.oauth_device import (
    async_poll_device_token,
    async_request_device_authorization,
)
from homeassistant.core import HomeAssistant

from tests.test_util.aiohttp import AiohttpClientMocker, AiohttpClientMockResponse


async def test_request_device_authorization(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Parse a successful device authorization response."""
    aioclient_mock.post(
        DEVICE_CODE_URL,
        json={
            "device_code": "device-code",
            "user_code": "WXYZ-9876",
            "verification_uri": "https://accounts.x.ai/oauth2/device",
            "verification_uri_complete": (
                "https://accounts.x.ai/oauth2/device?user_code=WXYZ-9876"
            ),
            "expires_in": 1800,
            "interval": 5,
        },
    )
    authorization = await async_request_device_authorization(
        hass, client_id="home-assistant-client"
    )
    assert authorization.user_code == "WXYZ-9876"
    assert authorization.interval == 5
    assert aioclient_mock.mock_calls[0][2] == {
        "client_id": "home-assistant-client",
        "scope": "openid profile email offline_access grok-cli:access api:access",
    }


async def test_poll_device_token_handles_pending_and_success(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Keep polling through authorization_pending until tokens arrive."""
    payloads = [
        ({"error": "authorization_pending"}, HTTPStatus.BAD_REQUEST),
        ({"error": "slow_down"}, HTTPStatus.BAD_REQUEST),
        (
            {
                "access_token": "access",
                "refresh_token": "refresh",
                "expires_in": 3600,
                "token_type": "Bearer",
            },
            HTTPStatus.OK,
        ),
    ]
    payload_iter = iter(payloads)

    async def token_side_effect(
        method: str, url: object, data: object
    ) -> AiohttpClientMockResponse:
        json_body, status = next(payload_iter)
        return AiohttpClientMockResponse(
            method=method,
            url=url,
            status=status,
            json=json_body,
        )

    aioclient_mock.post(TOKEN_URL, side_effect=token_side_effect)
    with patch(
        "homeassistant.components.spacexai.oauth_device.asyncio.sleep",
        new_callable=AsyncMock,
    ):
        token = await async_poll_device_token(
            hass,
            client_id="home-assistant-client",
            device_code="device-code",
            expires_in=30,
            interval=1,
        )
    assert token["access_token"] == "access"
    assert token["refresh_token"] == "refresh"
    assert "expires_at" in token


async def test_poll_device_token_expired(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Surface expired device codes as a timeout."""
    aioclient_mock.post(
        TOKEN_URL,
        json={"error": "expired_token"},
        status=HTTPStatus.BAD_REQUEST,
    )
    with pytest.raises(RequestTimeoutError):
        await async_poll_device_token(
            hass,
            client_id="home-assistant-client",
            device_code="device-code",
            expires_in=30,
            interval=1,
        )


async def test_request_device_authorization_rejects_unknown_client(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Treat unknown OAuth clients as authentication failures."""
    aioclient_mock.post(
        DEVICE_CODE_URL,
        json={"error": "invalid_client"},
        status=HTTPStatus.UNAUTHORIZED,
    )
    with pytest.raises(AuthenticationRejectedError):
        await async_request_device_authorization(
            hass, client_id="00000000-0000-4000-8000-000000000001"
        )


async def test_request_device_authorization_falls_back_verification_uri(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Use verification_uri when the complete URI is omitted."""
    aioclient_mock.post(
        DEVICE_CODE_URL,
        json={
            "device_code": "device-code",
            "user_code": "WXYZ-9876",
            "verification_uri": "https://accounts.x.ai/oauth2/device",
            "expires_in": 1800,
            "interval": 5,
        },
    )
    authorization = await async_request_device_authorization(
        hass, client_id="home-assistant-client"
    )
    assert (
        authorization.verification_uri_complete == "https://accounts.x.ai/oauth2/device"
    )


async def test_request_device_authorization_malformed(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Reject incomplete device authorization payloads."""
    aioclient_mock.post(DEVICE_CODE_URL, json={"device_code": "only-one-field"})
    with pytest.raises(MalformedProviderResponseError):
        await async_request_device_authorization(
            hass, client_id="home-assistant-client"
        )


async def test_request_device_authorization_connection_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Surface transport failures while requesting a device code."""
    aioclient_mock.post(DEVICE_CODE_URL, exc=ClientError("boom"))
    with pytest.raises(ConnectionFailureError):
        await async_request_device_authorization(
            hass, client_id="home-assistant-client"
        )


async def test_poll_device_token_rejects_incomplete_token(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Require both access and refresh tokens."""
    aioclient_mock.post(
        TOKEN_URL,
        json={"access_token": "access", "expires_in": 3600},
    )
    with pytest.raises(MalformedProviderResponseError):
        await async_poll_device_token(
            hass,
            client_id="home-assistant-client",
            device_code="device-code",
            expires_in=30,
            interval=1,
        )


async def test_poll_device_token_server_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Treat upstream 5xx responses as transient failures."""
    aioclient_mock.post(TOKEN_URL, status=HTTPStatus.BAD_GATEWAY, json={})
    with pytest.raises(TransientProviderError):
        await async_poll_device_token(
            hass,
            client_id="home-assistant-client",
            device_code="device-code",
            expires_in=30,
            interval=1,
        )


async def test_poll_device_token_permanent_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Treat unexpected provider errors as permanent failures."""
    aioclient_mock.post(
        TOKEN_URL,
        status=HTTPStatus.BAD_REQUEST,
        json={"error": "invalid_grant"},
    )
    with pytest.raises(PermanentProviderError):
        await async_poll_device_token(
            hass,
            client_id="home-assistant-client",
            device_code="device-code",
            expires_in=30,
            interval=1,
        )


async def test_poll_device_token_connection_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Surface transport failures while polling for tokens."""
    aioclient_mock.post(TOKEN_URL, exc=ClientError("boom"))
    with pytest.raises(ConnectionFailureError):
        await async_poll_device_token(
            hass,
            client_id="home-assistant-client",
            device_code="device-code",
            expires_in=30,
            interval=1,
        )


async def test_request_device_authorization_timeout(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Surface request timeouts while starting device authorization."""
    aioclient_mock.post(DEVICE_CODE_URL, exc=TimeoutError())
    with pytest.raises(RequestTimeoutError):
        await async_request_device_authorization(
            hass, client_id="home-assistant-client"
        )


async def test_request_device_authorization_non_json(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Reject non-JSON device authorization bodies."""
    aioclient_mock.post(DEVICE_CODE_URL, text="not-json")
    with pytest.raises(MalformedProviderResponseError):
        await async_request_device_authorization(
            hass, client_id="home-assistant-client"
        )


async def test_request_device_authorization_non_object(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Reject JSON arrays from the device authorization endpoint."""
    aioclient_mock.post(DEVICE_CODE_URL, json=["not", "an", "object"])
    with pytest.raises(MalformedProviderResponseError):
        await async_request_device_authorization(
            hass, client_id="home-assistant-client"
        )


async def test_request_device_authorization_empty_body(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Treat an empty success body as incomplete."""
    aioclient_mock.post(DEVICE_CODE_URL, text="null")
    with pytest.raises(MalformedProviderResponseError):
        await async_request_device_authorization(
            hass, client_id="home-assistant-client"
        )


async def test_request_device_authorization_defaults_interval(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Default the poll interval when the provider omits it."""
    aioclient_mock.post(
        DEVICE_CODE_URL,
        json={
            "device_code": "device-code",
            "user_code": "WXYZ-9876",
            "verification_uri": "https://accounts.x.ai/oauth2/device",
            "expires_in": 1800,
        },
    )
    authorization = await async_request_device_authorization(
        hass, client_id="home-assistant-client"
    )
    assert authorization.interval == 5


@pytest.mark.parametrize(
    ("status", "payload", "expected"),
    [
        pytest.param(
            HTTPStatus.FORBIDDEN,
            {"error": "unauthorized_client"},
            AuthenticationRejectedError,
            id="unauthorized_client",
        ),
        pytest.param(
            HTTPStatus.TOO_MANY_REQUESTS,
            {"error": "slow_down"},
            RateLimitedError,
            id="rate_limited",
        ),
        pytest.param(
            HTTPStatus.REQUEST_TIMEOUT,
            {},
            TransientProviderError,
            id="request_timeout",
        ),
        pytest.param(
            HTTPStatus.BAD_REQUEST,
            {"error": "invalid_scope"},
            PermanentProviderError,
            id="invalid_scope",
        ),
    ],
)
async def test_request_device_authorization_http_errors(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    status: HTTPStatus,
    payload: dict[str, str],
    expected: type[Exception],
) -> None:
    """Map device authorization HTTP failures to typed errors."""
    aioclient_mock.post(DEVICE_CODE_URL, json=payload, status=status)
    with pytest.raises(expected):
        await async_request_device_authorization(
            hass, client_id="home-assistant-client"
        )


async def test_poll_device_token_access_denied(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Surface access_denied as authentication rejection."""
    aioclient_mock.post(
        TOKEN_URL,
        json={"error": "access_denied"},
        status=HTTPStatus.BAD_REQUEST,
    )
    with pytest.raises(AuthenticationRejectedError):
        await async_poll_device_token(
            hass,
            client_id="home-assistant-client",
            device_code="device-code",
            expires_in=30,
            interval=1,
        )


async def test_poll_device_token_timeout(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Surface request timeouts while polling for tokens."""
    aioclient_mock.post(TOKEN_URL, exc=TimeoutError())
    with pytest.raises(RequestTimeoutError):
        await async_poll_device_token(
            hass,
            client_id="home-assistant-client",
            device_code="device-code",
            expires_in=30,
            interval=1,
        )


async def test_poll_device_token_deadline_expires(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Expire locally when the provider never returns expired_token."""
    aioclient_mock.post(
        TOKEN_URL,
        json={"error": "authorization_pending"},
        status=HTTPStatus.BAD_REQUEST,
    )

    async def _no_sleep(_delay: float) -> None:
        return None

    with (
        patch(
            "homeassistant.components.spacexai.oauth_device.asyncio.sleep",
            side_effect=_no_sleep,
        ),
        patch(
            "homeassistant.components.spacexai.oauth_device.time.monotonic",
            side_effect=[0.0, 0.5, 2.0],
        ),
        pytest.raises(RequestTimeoutError),
    ):
        await async_poll_device_token(
            hass,
            client_id="home-assistant-client",
            device_code="device-code",
            expires_in=1,
            interval=1,
        )


async def test_poll_device_token_invalid_expires_in(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Require a numeric expires_in on successful token responses."""
    aioclient_mock.post(
        TOKEN_URL,
        json={
            "access_token": "access",
            "refresh_token": "refresh",
            "expires_in": "not-a-number",
        },
    )
    with pytest.raises(MalformedProviderResponseError):
        await async_poll_device_token(
            hass,
            client_id="home-assistant-client",
            device_code="device-code",
            expires_in=30,
            interval=1,
        )


async def test_poll_device_token_missing_expires_in(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Reject successful token responses that omit expires_in."""
    aioclient_mock.post(
        TOKEN_URL,
        json={
            "access_token": "access",
            "refresh_token": "refresh",
        },
    )
    with pytest.raises(MalformedProviderResponseError):
        await async_poll_device_token(
            hass,
            client_id="home-assistant-client",
            device_code="device-code",
            expires_in=30,
            interval=1,
        )


async def test_poll_device_token_sets_default_token_type(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Default token_type to Bearer when the provider omits it."""
    aioclient_mock.post(
        TOKEN_URL,
        json={
            "access_token": "access",
            "refresh_token": "refresh",
            "expires_in": 3600,
        },
    )
    token = await async_poll_device_token(
        hass,
        client_id="home-assistant-client",
        device_code="device-code",
        expires_in=30,
        interval=1,
    )
    assert token["token_type"] == "Bearer"
