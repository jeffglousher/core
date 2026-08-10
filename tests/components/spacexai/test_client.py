"""Tests for the typed SpaceXAI client boundary."""

import base64
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import ClientConnectionError
import httpx
import openai
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAIError,
    PermissionDeniedError,
)
from openai.types import Model
from openai.types.responses import ResponseErrorEvent
from pydantic import ValidationError
import pytest

from homeassistant.components.spacexai.client import (
    AccountInfo,
    OAuthAccessTokenProvider,
    ProviderSnapshot,
    SpaceXAIClient,
    StaticAccessTokenProvider,
)
from homeassistant.components.spacexai.const import (
    DEVELOPER_API_BASE_URL,
    IMAGES_URL,
    REVOCATION_URL,
    STT_URL,
    TTS_URL,
    USERINFO_URL,
    VIDEOS_URL,
)
from homeassistant.components.spacexai.errors import (
    AuthenticationRejectedError,
    ConnectionFailureError,
    ErrorCategory,
    ErrorContext,
    MalformedProviderResponseError,
    ModelNotEntitledError,
    Operation,
    PermanentProviderError,
    QuotaLimitedError,
    RateLimitedError,
    ReauthenticationRequiredError,
    RefreshRejectedError,
    RequestTimeoutError,
    SpaceXAIError,
    TransientProviderError,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    OAuth2TokenRequestError,
    OAuth2TokenRequestReauthError,
    OAuth2TokenRequestTransientError,
)
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session

from . import EventStream

from tests.test_util.aiohttp import AiohttpClientMocker


def _client(hass: HomeAssistant, *, runtime: bool = False) -> SpaceXAIClient:
    """Create a test client."""
    return SpaceXAIClient(
        hass,
        StaticAccessTokenProvider("access-token"),
        runtime_session=runtime,
    )


async def test_account_identity(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Parse account identity exactly once at the boundary."""
    aioclient_mock.get(
        USERINFO_URL,
        json={
            "sub": "account-123",
            "name": "Home User",
            "email": "home@example.com",
        },
    )
    account = await _client(hass).async_get_account()
    assert account.subject == "account-123"
    assert account.display_name == "Home User"
    request = aioclient_mock.mock_calls[0]
    assert request[3]["Authorization"] == "Bearer access-token"


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param([], id="not-an-object"),
        pytest.param({"name": "Missing subject"}, id="missing-subject"),
        pytest.param({"sub": "id", "email": 42}, id="invalid-email"),
    ],
)
async def test_malformed_account(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    payload: object,
) -> None:
    """Reject malformed provider identity data."""
    aioclient_mock.get(USERINFO_URL, json=payload)
    with pytest.raises(MalformedProviderResponseError):
        await _client(hass).async_get_account()


async def test_account_invalid_json(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Reject a non-JSON identity response."""
    aioclient_mock.get(
        USERINFO_URL,
        text="not json",
        headers={"Content-Type": "application/json"},
    )
    with pytest.raises(MalformedProviderResponseError):
        await _client(hass).async_get_account()


@pytest.mark.parametrize(
    ("status", "error_type"),
    [
        pytest.param(401, AuthenticationRejectedError, id="authentication"),
        pytest.param(402, QuotaLimitedError, id="quota"),
        pytest.param(403, PermanentProviderError, id="permission"),
        pytest.param(429, RateLimitedError, id="rate-limit"),
    ],
)
async def test_account_status_classification(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    status: int,
    error_type: type[SpaceXAIError],
) -> None:
    """Classify failed account requests precisely."""
    aioclient_mock.get(USERINFO_URL, status=status)
    with pytest.raises(error_type):
        await _client(hass).async_get_account()


async def test_runtime_unauthorized_requires_reauth(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Distinguish runtime expiry from initial authentication rejection."""
    aioclient_mock.get(USERINFO_URL, status=401)
    with pytest.raises(ReauthenticationRequiredError):
        await _client(hass, runtime=True).async_get_account()


async def test_model_discovery_and_filtering(hass: HomeAssistant) -> None:
    """Return only entitled Grok language models, including request aliases."""
    page = MagicMock(
        data=[
            Model(
                id="grok-4.5",
                created=1,
                object="model",
                owned_by="xai",
                completion_text_token_price=25000,
            ),
            Model(
                id="latest",
                created=1,
                object="model",
                owned_by="xai",
                output_modalities=["text"],
                aliases=["grok-4.3-latest", "grok-latest"],
            ),
            Model(
                id="grok-imagine-1",
                created=1,
                object="model",
                owned_by="xai",
                image_price=1,
            ),
            Model(id="unrelated", created=1, object="model", owned_by="other"),
        ]
    )
    with patch(
        "openai.resources.models.AsyncModels.list",
        new_callable=AsyncMock,
        return_value=page,
    ):
        models = await _client(hass).async_get_models()
    assert [model.id for model in models] == ["grok-4.5", "latest"]
    assert models[1].aliases == ("grok-4.3-latest", "grok-latest")
    snapshot = ProviderSnapshot(
        account=AccountInfo("sub", "Name", None),
        models=models,
    )
    assert snapshot.has_model("grok-4.3-latest")
    assert not snapshot.has_model("grok-imagine-1")


async def test_empty_model_catalog_is_allowed(hass: HomeAssistant) -> None:
    """Allow an empty catalog; setup falls back to the default chat model."""
    with patch(
        "openai.resources.models.AsyncModels.list",
        new_callable=AsyncMock,
        return_value=MagicMock(data=[]),
    ):
        models = await _client(hass).async_get_models()
    assert models == ()


async def test_sdk_error_classification(hass: HomeAssistant) -> None:
    """Classify SDK authentication failures."""
    error = AuthenticationError(
        message="bad token",
        response=MagicMock(status_code=401, headers={}),
        body={"error": {"code": "invalid_token"}},
    )
    with (
        patch(
            "openai.resources.models.AsyncModels.list",
            new_callable=AsyncMock,
            side_effect=error,
        ),
        pytest.raises(AuthenticationRejectedError) as raised,
    ):
        await _client(hass).async_get_models()
    assert raised.value.context.provider_code == "invalid_token"


async def test_refresh_rejected() -> None:
    """Map a rejected refresh grant separately from inference authentication."""
    session = MagicMock(spec=OAuth2Session)
    session.async_ensure_token_valid = AsyncMock(
        side_effect=OAuth2TokenRequestReauthError(
            request_info=MagicMock(),
            history=(),
            status=400,
            message="invalid_grant",
            headers=None,
            domain="spacexai",
        )
    )
    provider = OAuthAccessTokenProvider(session)
    with pytest.raises(RefreshRejectedError) as raised:
        await provider.async_get_access_token()
    assert raised.value.category is ErrorCategory.REFRESH_REJECTED


async def test_stream_request_options(hass: HomeAssistant) -> None:
    """Use streaming, local history, parallel tools, caching, and explicit limits."""
    stream = EventStream(
        [
            ResponseErrorEvent(
                message="unused",
                sequence_number=0,
                type="error",
            )
        ]
    )
    with patch(
        "openai.resources.responses.AsyncResponses.create",
        new_callable=AsyncMock,
        return_value=stream,
    ) as create:
        returned = await _client(hass).async_stream_response(
            model="grok-4.5",
            input=[],
            tools=[],
            max_output_tokens=3000,
            prompt_cache_key="conversation-id",
            temperature=1.0,
            top_p=1.0,
            service_tier="priority",
        )
    assert returned is stream
    assert create.call_args.kwargs["stream"] is True
    assert create.call_args.kwargs["store"] is False
    assert create.call_args.kwargs["temperature"] == 1.0
    assert create.call_args.kwargs["top_p"] == 1.0
    assert create.call_args.kwargs["service_tier"] == "priority"
    assert create.call_args.kwargs["include"] == ["reasoning.encrypted_content"]
    assert create.call_args.kwargs["parallel_tool_calls"] is True
    assert create.call_args.kwargs["prompt_cache_key"] == "conversation-id"
    assert create.call_args.kwargs["timeout"] == 300.0
    assert "text" not in create.call_args.kwargs

    with patch(
        "openai.resources.responses.AsyncResponses.create",
        new_callable=AsyncMock,
        return_value=stream,
    ) as create_structured:
        await _client(hass).async_stream_response(
            model="grok-4.5",
            input=[],
            tools=[],
            max_output_tokens=2048,
            prompt_cache_key="conversation-id",
            text={
                "format": {
                    "type": "json_schema",
                    "name": "task",
                    "schema": {"type": "object", "properties": {}},
                }
            },
        )
    assert create_structured.call_args.kwargs["text"] == {
        "format": {
            "type": "json_schema",
            "name": "task",
            "schema": {"type": "object", "properties": {}},
        }
    }


async def test_sdk_client_is_reused(hass: HomeAssistant) -> None:
    """Reuse the injected SDK client while updating OAuth authorization."""
    page = MagicMock(
        data=[
            Model(
                id="grok-4.5",
                created=1,
                object="model",
                owned_by="xai",
                completion_text_token_price=25000,
            )
        ]
    )
    stream = EventStream([])
    client = _client(hass)
    with (
        patch(
            "homeassistant.components.spacexai.client.openai.AsyncOpenAI",
            wraps=openai.AsyncOpenAI,
        ) as constructor,
        patch(
            "openai.resources.models.AsyncModels.list",
            new_callable=AsyncMock,
            return_value=page,
        ),
        patch(
            "openai.resources.responses.AsyncResponses.create",
            new_callable=AsyncMock,
            return_value=stream,
        ),
    ):
        await client.async_get_models()
        await client.async_stream_response(
            model="grok-4.5",
            input=[],
            tools=[],
            max_output_tokens=1,
            prompt_cache_key="conversation-id",
        )
    constructor.assert_called_once()


def test_error_category_values_match_translation_keys() -> None:
    """Ensure every closed error category value is a strings.json exception key."""
    assert {category.value for category in ErrorCategory} == {
        "authentication_rejected",
        "refresh_rejected",
        "reauthentication_required",
        "account_mismatch",
        "subscription_not_entitled",
        "model_not_entitled",
        "rate_limited",
        "quota_limited",
        "timeout",
        "connection_failure",
        "transient_provider_failure",
        "malformed_provider_response",
        "invalid_model_tool_request",
        "home_assistant_tool_failure",
        "tool_loop_limit",
        "output_limit",
        "permanent_provider_failure",
    }


def test_permission_status_classification(hass: HomeAssistant) -> None:
    """Do not infer consumer subscription state from permission denial."""
    provider_error = PermissionDeniedError(
        message="Permission denied",
        response=httpx.Response(
            status_code=403,
            request=httpx.Request("GET", "https://api.x.ai/v1/models"),
        ),
        body={"error": {"code": "permission_denied"}},
    )
    classified = _client(hass).translate_sdk_error(
        provider_error,
        ErrorContext(operation=Operation.RESPONSE, model="grok-4.5"),
    )
    assert isinstance(classified, PermanentProviderError)
    assert classified.context.provider_code == "permission_denied"


def test_account_display_name_fallbacks() -> None:
    """Use only legitimate identity fields as config-entry titles."""
    assert (
        AccountInfo("id", None, "user@example.com").display_name == "user@example.com"
    )
    assert AccountInfo("id", None, None).display_name == "SpaceXAI"


@pytest.mark.parametrize(
    ("side_effect", "error_type"),
    [
        pytest.param(
            OAuth2TokenRequestTransientError(
                request_info=MagicMock(),
                history=(),
                status=503,
                message="temporary",
                headers=None,
                domain="spacexai",
            ),
            TransientProviderError,
            id="transient",
        ),
        pytest.param(ClientConnectionError(), ConnectionFailureError, id="connection"),
        pytest.param(
            OAuth2TokenRequestError(
                request_info=MagicMock(),
                history=(),
                status=418,
                message="transport",
                headers=None,
                domain="spacexai",
            ),
            ConnectionFailureError,
            id="oauth-error",
        ),
    ],
)
async def test_refresh_failure_classification(
    side_effect: Exception, error_type: type[Exception]
) -> None:
    """Classify refresh transport failures."""
    session = MagicMock(spec=OAuth2Session)
    session.async_ensure_token_valid = AsyncMock(side_effect=side_effect)
    with pytest.raises(error_type):
        await OAuthAccessTokenProvider(session).async_get_access_token()


async def test_refresh_success_and_malformed_token() -> None:
    """Return refreshed access tokens and reject malformed token state."""
    session = MagicMock(spec=OAuth2Session)
    session.async_ensure_token_valid = AsyncMock()
    session.token = {"access_token": "fresh"}
    assert await OAuthAccessTokenProvider(session).async_get_access_token() == "fresh"
    session.token = {}
    with pytest.raises(MalformedProviderResponseError):
        await OAuthAccessTokenProvider(session).async_get_access_token()


async def test_account_connection_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Map account endpoint transport errors."""
    aioclient_mock.get(USERINFO_URL, exc=ClientConnectionError())
    with pytest.raises(ConnectionFailureError):
        await _client(hass).async_get_account()


async def test_validate_combines_account_and_models(hass: HomeAssistant) -> None:
    """Return a provider snapshot from account identity and model discovery."""
    client = _client(hass)
    models = [
        Model(
            id="grok-4.5",
            created=1,
            object="model",
            owned_by="xai",
            output_modalities=["text"],
        ),
        Model(
            id="grok-imagine-image-quality",
            created=1,
            object="model",
            owned_by="xai",
            output_modalities=["image"],
        ),
        Model(
            id="grok-imagine-video-1.5",
            created=1,
            object="model",
            owned_by="xai",
            output_modalities=["video"],
        ),
    ]
    with (
        patch.object(
            client,
            "async_get_account",
            new_callable=AsyncMock,
            return_value=MagicMock(subject="account"),
        ),
        patch.object(
            client,
            "_async_list_provider_models",
            new_callable=AsyncMock,
            return_value=models,
        ),
    ):
        snapshot = await client.async_validate()
    assert snapshot.account.subject == "account"
    assert [model.id for model in snapshot.models] == ["grok-4.5"]
    assert [model.id for model in snapshot.image_models] == [
        "grok-imagine-image-quality"
    ]
    assert [model.id for model in snapshot.video_models] == ["grok-imagine-video-1.5"]


async def test_validate_propagates_model_list_auth_failures(
    hass: HomeAssistant,
) -> None:
    """Do not treat chat-proxy auth failures as an empty optional catalog."""
    client = _client(hass)
    with (
        patch.object(
            client,
            "async_get_account",
            new_callable=AsyncMock,
            return_value=MagicMock(subject="account"),
        ),
        patch.object(
            client,
            "_async_list_provider_models",
            new_callable=AsyncMock,
            side_effect=AuthenticationRejectedError(
                "auth rejected",
                context=ErrorContext(operation=Operation.MODELS, status=401),
            ),
        ),
        pytest.raises(AuthenticationRejectedError),
    ):
        await client.async_validate()


@pytest.mark.parametrize(
    ("error", "error_type"),
    [
        pytest.param(
            APITimeoutError(request=httpx.Request("POST", "https://api.x.ai")),
            RequestTimeoutError,
            id="timeout",
        ),
        pytest.param(
            APIConnectionError(request=httpx.Request("POST", "https://api.x.ai")),
            ConnectionFailureError,
            id="connection",
        ),
    ],
)
async def test_stream_sdk_errors(
    hass: HomeAssistant,
    error: OpenAIError,
    error_type: type[Exception],
) -> None:
    """Translate SDK errors raised while starting a response stream."""
    with (
        patch(
            "openai.resources.responses.AsyncResponses.create",
            new_callable=AsyncMock,
            side_effect=error,
        ),
        pytest.raises(error_type),
    ):
        await _client(hass).async_stream_response(
            model="grok-4.5",
            input=[],
            tools=[],
            max_output_tokens=1,
            prompt_cache_key="id",
        )


async def test_revoke(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """Send refresh-token revocation data and classify failure."""
    aioclient_mock.post(REVOCATION_URL, status=200)
    await _client(hass).async_revoke("refresh", "client", "secret")
    assert aioclient_mock.mock_calls[0][2]["token"] == "refresh"
    assert aioclient_mock.mock_calls[0][2]["client_secret"] == "secret"

    aioclient_mock.clear_requests()
    aioclient_mock.post(REVOCATION_URL, status=500)
    with pytest.raises(TransientProviderError):
        await _client(hass).async_revoke("refresh", "client")


@pytest.mark.parametrize(
    ("status", "model", "body", "error_type"),
    [
        pytest.param(
            404,
            "grok-4.5",
            {"code": "provider_code"},
            ModelNotEntitledError,
            id="model",
        ),
        pytest.param(
            408, None, {"code": "provider_code"}, RequestTimeoutError, id="timeout"
        ),
        pytest.param(
            500, None, {"code": "provider_code"}, TransientProviderError, id="provider"
        ),
        pytest.param(
            400, None, {"code": "provider_code"}, PermanentProviderError, id="permanent"
        ),
        pytest.param(
            400,
            None,
            {
                "code": "invalid-argument",
                "error": "Incorrect API key provided. You can obtain an API key from https://console.x.ai.",
            },
            AuthenticationRejectedError,
            id="invalid-bearer",
        ),
    ],
)
def test_additional_sdk_statuses(
    hass: HomeAssistant,
    status: int,
    model: str | None,
    body: dict[str, str],
    error_type: type[Exception],
) -> None:
    """Classify the remaining provider status families."""
    provider_error = APIStatusError(
        message="failure",
        response=httpx.Response(
            status,
            request=httpx.Request("POST", "https://api.x.ai/v1/responses"),
        ),
        body=body,
    )
    error = _client(hass).translate_sdk_error(
        provider_error,
        ErrorContext(operation=Operation.RESPONSE, model=model),
    )
    assert isinstance(error, error_type)


def test_invalid_bearer_requires_reauthentication(hass: HomeAssistant) -> None:
    """Map invalid runtime Bearer tokens to reauthentication."""
    provider_error = APIStatusError(
        message="failure",
        response=httpx.Response(
            400,
            request=httpx.Request("GET", "https://api.x.ai/v1/models"),
        ),
        body={
            "code": "invalid-argument",
            "error": "Incorrect API key provided. You can obtain an API key from https://console.x.ai.",
        },
    )
    error = _client(hass, runtime=True).translate_sdk_error(
        provider_error,
        ErrorContext(operation=Operation.MODELS),
    )
    assert isinstance(error, ReauthenticationRequiredError)


def test_unknown_sdk_error(hass: HomeAssistant) -> None:
    """Treat unknown SDK failures as permanent failures."""
    error = _client(hass).translate_sdk_error(
        OpenAIError("unknown"),
        ErrorContext(operation=Operation.RESPONSE),
    )
    assert error.category is ErrorCategory.PERMANENT_PROVIDER_FAILURE


async def test_revoke_connection_failure(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Surface a transport failure while revoking a refresh token."""
    aioclient_mock.post(REVOCATION_URL, exc=ClientConnectionError("offline"))
    with pytest.raises(ConnectionFailureError):
        await _client(hass).async_revoke("refresh-token", "client-id")


async def test_sdk_schema_violation_is_malformed(hass: HomeAssistant) -> None:
    """Treat an SDK schema violation as a malformed provider response."""
    with (
        patch(
            "openai.resources.responses.AsyncResponses.create",
            new_callable=AsyncMock,
            side_effect=ValidationError.from_exception_data("Response", []),
        ),
        pytest.raises(MalformedProviderResponseError),
    ):
        await _client(hass).async_stream_response(
            model="grok-4.5",
            input=[],
            tools=[],
            max_output_tokens=2048,
            prompt_cache_key="conversation-id",
        )


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        pytest.param(
            {"error": {"code": "rate_limited"}}, "rate_limited", id="nested-code"
        ),
        pytest.param({"error": {"type": "overloaded"}}, "overloaded", id="nested-type"),
        pytest.param({"code": "flat"}, "flat", id="flat-code"),
        pytest.param({"error": {"code": 42}}, None, id="non-string"),
        pytest.param("not-a-mapping", None, id="not-a-mapping"),
    ],
)
async def test_provider_error_code_parsing(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    body: object,
    expected: str | None,
) -> None:
    """Extract the provider error code from the shapes SpaceXAI returns."""
    aioclient_mock.get(USERINFO_URL, json=body, status=429)
    with pytest.raises(RateLimitedError) as raised:
        await _client(hass).async_get_account()
    assert raised.value.context.provider_code == expected


@pytest.mark.parametrize(
    "body",
    [
        pytest.param(
            {"error": {"message": "Incorrect API key provided"}}, id="nested-message"
        ),
        pytest.param({"error": "no credentials supplied"}, id="error-string"),
        pytest.param({"message": "Incorrect API key provided"}, id="flat-message"),
    ],
)
async def test_http_400_credential_rejection(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, body: object
) -> None:
    """Classify SpaceXAI's HTTP 400 credential rejections as authentication failures."""
    aioclient_mock.get(USERINFO_URL, json=body, status=400)
    with pytest.raises(AuthenticationRejectedError):
        await _client(hass).async_get_account()


async def test_error_body_that_is_not_json(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Classify by status when the error body cannot be decoded."""
    aioclient_mock.get(
        USERINFO_URL,
        text="<html>gateway</html>",
        headers={"Content-Type": "text/html"},
        status=503,
    )
    with pytest.raises(TransientProviderError):
        await _client(hass).async_get_account()


async def test_http_400_unauthenticated_code(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Classify an HTTP 400 carrying an unauthenticated code as an auth failure."""
    aioclient_mock.get(
        USERINFO_URL, json={"error": {"code": "unauthenticated"}}, status=400
    )
    with pytest.raises(AuthenticationRejectedError):
        await _client(hass).async_get_account()


async def test_http_400_without_credential_hint(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Keep an unrelated HTTP 400 classified as a permanent provider failure."""
    aioclient_mock.get(USERINFO_URL, json={"error": "bad request"}, status=400)
    with pytest.raises(PermanentProviderError):
        await _client(hass).async_get_account()


async def test_http_400_with_non_object_body(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Classify an HTTP 400 whose body is not an object."""
    aioclient_mock.get(USERINFO_URL, json="rejected", status=400)
    with pytest.raises(PermanentProviderError):
        await _client(hass).async_get_account()


@pytest.mark.parametrize(
    ("image_bytes", "mime_type"),
    [
        pytest.param(b"\xff\xd8\xff" + b"jpeg-padding", "image/jpeg", id="jpeg"),
        pytest.param(b"\x89PNG" + b"png-padding", "image/png", id="png"),
    ],
)
async def test_generate_image_success(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    image_bytes: bytes,
    mime_type: str,
) -> None:
    """Return decoded image bytes and sniffed MIME type from the Imagine endpoint."""
    aioclient_mock.post(
        IMAGES_URL,
        json={
            "data": [
                {
                    "b64_json": base64.b64encode(image_bytes).decode(),
                    "revised_prompt": "a red bicycle at sunset",
                }
            ]
        },
    )
    generated = await _client(hass).async_generate_image(
        model="grok-imagine-image-quality", prompt="a red bicycle"
    )
    assert generated.image_data == image_bytes
    assert generated.mime_type == mime_type
    assert generated.model == "grok-imagine-image-quality"
    assert generated.revised_prompt == "a red bicycle at sunset"
    request = aioclient_mock.mock_calls[0][2]
    assert request["response_format"] == "b64_json"
    assert request["n"] == 1


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param("not-an-object", id="not-an-object"),
        pytest.param({"data": []}, id="empty-data"),
        pytest.param({"data": ["nope"]}, id="invalid-entry"),
        pytest.param({"data": [{"b64_json": ""}]}, id="empty-base64"),
        pytest.param({"data": [{"b64_json": "!!!not-base64!!!"}]}, id="invalid-base64"),
    ],
)
async def test_generate_image_malformed(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, payload: object
) -> None:
    """Reject malformed Imagine responses."""
    aioclient_mock.post(IMAGES_URL, json=payload)
    with pytest.raises(MalformedProviderResponseError):
        await _client(hass).async_generate_image(
            model="grok-imagine-image-quality", prompt="a red bicycle"
        )


async def test_generate_image_status_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Classify an Imagine endpoint status failure."""
    aioclient_mock.post(
        IMAGES_URL, json={"error": {"code": "rate_limited"}}, status=429
    )
    with pytest.raises(RateLimitedError):
        await _client(hass).async_generate_image(
            model="grok-imagine-image-quality", prompt="a red bicycle"
        )


async def test_generate_image_invalid_json(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Reject a non-JSON Imagine response."""
    aioclient_mock.post(
        IMAGES_URL, text="not json", headers={"Content-Type": "application/json"}
    )
    with pytest.raises(MalformedProviderResponseError):
        await _client(hass).async_generate_image(
            model="grok-imagine-image-quality", prompt="a red bicycle"
        )


async def test_generate_image_connection_failure(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Surface a transport failure from the Imagine endpoint."""
    aioclient_mock.post(IMAGES_URL, exc=ClientConnectionError("offline"))
    with pytest.raises(ConnectionFailureError):
        await _client(hass).async_generate_image(
            model="grok-imagine-image-quality", prompt="a red bicycle"
        )


async def test_transcribe_success(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Return the transcript from the STT endpoint."""
    aioclient_mock.post(STT_URL, json={"text": "hello world"})
    text = await _client(hass).async_transcribe(
        audio=b"audio",
        filename="speech.wav",
        content_type="audio/wav",
        language="en-US",
    )
    assert text == "hello world"


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param("not-an-object", id="not-an-object"),
        pytest.param({}, id="missing-text"),
        pytest.param({"text": ""}, id="empty-text"),
    ],
)
async def test_transcribe_malformed(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, payload: object
) -> None:
    """Reject malformed STT responses."""
    aioclient_mock.post(STT_URL, json=payload)
    with pytest.raises(MalformedProviderResponseError):
        await _client(hass).async_transcribe(
            audio=b"audio", filename="speech.wav", content_type="audio/wav"
        )


async def test_transcribe_invalid_json(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Reject a non-JSON STT response."""
    aioclient_mock.post(
        STT_URL, text="not json", headers={"Content-Type": "application/json"}
    )
    with pytest.raises(MalformedProviderResponseError):
        await _client(hass).async_transcribe(
            audio=b"audio", filename="speech.wav", content_type="audio/wav"
        )


async def test_transcribe_status_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Classify an STT endpoint status failure."""
    aioclient_mock.post(STT_URL, json={"error": {"code": "quota"}}, status=402)
    with pytest.raises(QuotaLimitedError):
        await _client(hass).async_transcribe(
            audio=b"audio", filename="speech.wav", content_type="audio/wav"
        )


async def test_transcribe_connection_failure(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Surface a transport failure from the STT endpoint."""
    aioclient_mock.post(STT_URL, exc=ClientConnectionError("offline"))
    with pytest.raises(ConnectionFailureError):
        await _client(hass).async_transcribe(
            audio=b"audio", filename="speech.wav", content_type="audio/wav"
        )


async def test_synthesize_speech_success(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Return audio bytes from the TTS endpoint."""
    aioclient_mock.post(TTS_URL, content=b"audio-bytes")
    audio = await _client(hass).async_synthesize_speech(
        text="hello", voice_id="eve", language="en", speed=1.1, codec="mp3"
    )
    assert audio == b"audio-bytes"
    request = aioclient_mock.mock_calls[0][2]
    assert request["voice_id"] == "eve"
    assert request["speed"] == 1.1
    assert request["output_format"] == {"codec": "mp3"}


async def test_synthesize_speech_status_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Classify a TTS endpoint status failure."""
    aioclient_mock.post(TTS_URL, json={"error": {"code": "rate_limited"}}, status=429)
    with pytest.raises(RateLimitedError):
        await _client(hass).async_synthesize_speech(
            text="hello", voice_id="eve", language="en"
        )


async def test_synthesize_speech_connection_failure(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Surface a transport failure from the TTS endpoint."""
    aioclient_mock.post(TTS_URL, exc=ClientConnectionError("offline"))
    with pytest.raises(ConnectionFailureError):
        await _client(hass).async_synthesize_speech(
            text="hello", voice_id="eve", language="en"
        )


async def test_generate_video_refreshes_token_while_polling(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Refresh the OAuth access token on each video status poll."""
    tokens = iter(["token-start", "token-poll-1", "token-poll-2"])
    provider = AsyncMock()
    provider.async_get_access_token = AsyncMock(side_effect=lambda: next(tokens))
    client = SpaceXAIClient(hass, provider, runtime_session=False)

    aioclient_mock.post(VIDEOS_URL, json={"request_id": "req-1"})
    status_url = f"{DEVELOPER_API_BASE_URL}/videos/req-1"
    aioclient_mock.get(status_url, json={"status": "pending"})
    aioclient_mock.get(
        status_url,
        json={"status": "done", "video": {"url": "https://vidgen.example/v.mp4"}},
    )

    with patch(
        "homeassistant.components.spacexai.client.asyncio.sleep",
        new_callable=AsyncMock,
    ):
        generated = await client.async_generate_video(
            model="grok-imagine-video-1.5",
            prompt="ball",
            duration=3,
        )

    assert generated.url == "https://vidgen.example/v.mp4"
    assert provider.async_get_access_token.await_count == 3
    assert aioclient_mock.mock_calls[0][3]["Authorization"] == "Bearer token-start"
    assert aioclient_mock.mock_calls[1][3]["Authorization"] == "Bearer token-poll-1"
    assert aioclient_mock.mock_calls[2][3]["Authorization"] == "Bearer token-poll-2"
