"""Tests for the typed SpaceXAI client boundary."""

import base64
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import ClientConnectionError
import httpx
from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAIError
from openai.types import Model
from openai.types.responses import ResponseErrorEvent
from pydantic import ValidationError
import pytest

from homeassistant.components.spacexai.client import (
    AccountInfo,
    ModelInfo,
    OAuthAccessTokenProvider,
    ProviderSnapshot,
    SpaceXAIClient,
    StaticAccessTokenProvider,
    _is_permission_denial,
    _is_subscription_denial,
    _safe_json,
)
from homeassistant.components.spacexai.const import (
    DEVELOPER_API_BASE_URL,
    IMAGES_EDIT_URL,
    IMAGES_URL,
    MODELS_URL,
    REVOCATION_URL,
    STT_URL,
    TTS_URL,
    USERINFO_URL,
    VIDEOS_URL,
)
from homeassistant.components.spacexai.errors import (
    AccountMismatchError,
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
    SubscriptionNotEntitledError,
    TransientProviderError,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    OAuth2TokenRequestError,
    OAuth2TokenRequestReauthError,
    OAuth2TokenRequestTransientError,
)
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session

from . import AsyncModelPage, EventStream

from tests.test_util.aiohttp import AiohttpClientMocker, AiohttpClientMockResponse


def _client(hass: HomeAssistant, *, runtime: bool = False) -> SpaceXAIClient:
    """Create a test client."""
    return SpaceXAIClient(
        hass,
        StaticAccessTokenProvider("access-token"),
        runtime_session=runtime,
    )


def _mock_developer_models(
    aioclient_mock: AiohttpClientMocker,
    models: list[dict[str, object]] | None = None,
    *,
    status: int = 200,
) -> None:
    """Stub the developer /models catalog used for Imagine discovery."""
    aioclient_mock.get(
        MODELS_URL,
        status=status,
        json={"object": "list", "data": models or []},
    )


def _status_error(status: int, body: object | None = None) -> APIStatusError:
    """Build an SDK status error for classification tests."""
    return APIStatusError(
        message="failure",
        response=httpx.Response(
            status,
            request=httpx.Request("POST", "https://api.x.ai/v1/responses"),
        ),
        body=body,
    )


async def test_account_identity(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Parse account identity and send a Bearer authorization header."""
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
    assert aioclient_mock.mock_calls[0][3]["Authorization"] == "Bearer access-token"


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


@pytest.mark.parametrize(
    ("side_effect", "error_type"),
    [
        pytest.param(ClientConnectionError(), ConnectionFailureError, id="connection"),
        pytest.param(TimeoutError(), RequestTimeoutError, id="timeout"),
    ],
)
async def test_account_transport_errors(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    side_effect: Exception,
    error_type: type[Exception],
) -> None:
    """Map account endpoint transport failures to typed errors."""
    aioclient_mock.get(USERINFO_URL, exc=side_effect)
    with pytest.raises(error_type):
        await _client(hass).async_get_account()


async def test_model_discovery_and_filtering(hass: HomeAssistant) -> None:
    """Return only entitled Grok language models, including request aliases."""
    page = AsyncModelPage(
        [
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


def test_empty_catalog_allows_known_media_models() -> None:
    """Allow documented Imagine ids when the developer catalog is empty."""
    snapshot = ProviderSnapshot(
        account=AccountInfo("sub", "Name", None),
        models=(ModelInfo(id="grok-4.5", owner="xai"),),
    )
    assert snapshot.has_image_model("grok-imagine-image-2.0")
    assert snapshot.has_image_model("grok-imagine-image-quality")
    assert snapshot.has_image_model("grok-imagine-image")
    assert not snapshot.has_image_model("grok-imagine-image-unknown")
    assert snapshot.has_video_model("grok-imagine-video-1.5")
    assert snapshot.has_video_model("grok-imagine-video")
    assert not snapshot.has_video_model("grok-imagine-video-unknown")
    assert snapshot.selectable_image_models[0] == "grok-imagine-image-2.0"
    assert snapshot.selectable_video_models[0] == "grok-imagine-video-1.5"


def test_documented_imagine_ids_stay_requestable() -> None:
    """Documented Imagine ids stay valid after a partial catalog refresh."""
    snapshot = ProviderSnapshot(
        account=AccountInfo("sub", "Name", None),
        models=(ModelInfo(id="grok-4.5", owner="xai"),),
        image_models=(
            ModelInfo(
                id="grok-imagine-image",
                owner="xai",
                aliases=("grok-imagine-image-2026-03-02",),
            ),
        ),
        video_models=(
            ModelInfo(
                id="grok-imagine-video",
                owner="xai",
                aliases=("grok-imagine-video-1.5-preview",),
            ),
        ),
    )
    assert snapshot.has_image_model("grok-imagine-image")
    assert snapshot.has_image_model("grok-imagine-image-2.0")
    assert snapshot.has_image_model("grok-imagine-image-quality")
    assert snapshot.has_image_model("grok-imagine-image-2026-03-02")
    assert not snapshot.has_image_model("grok-imagine-image-unknown")
    assert snapshot.has_video_model("grok-imagine-video")
    assert snapshot.has_video_model("grok-imagine-video-1.5")
    assert snapshot.selectable_image_models[0] == "grok-imagine-image-2.0"
    assert "grok-imagine-image-2026-03-02" not in snapshot.selectable_image_models
    assert "grok-imagine-video-1.5-preview" not in snapshot.selectable_video_models


def test_recommended_chat_model_stays_entitled() -> None:
    """grok-4.6 remains requestable even when the CLI catalog omits it."""
    snapshot = ProviderSnapshot(
        account=AccountInfo("sub", "Name", None),
        models=(ModelInfo(id="grok-4.3", owner="xai"),),
    )
    assert snapshot.has_model("grok-4.6")
    assert snapshot.selectable_chat_models[0] == "grok-4.6"
    assert "grok-4.3" in snapshot.selectable_chat_models


async def test_model_discovery_iterates_every_page(hass: HomeAssistant) -> None:
    """Discover conversation models beyond the first SDK page."""
    page = AsyncModelPage(
        [
            Model(
                id="grok-page-1",
                created=1,
                object="model",
                owned_by="xai",
                completion_text_token_price=1,
            )
        ],
        [
            Model(
                id="grok-page-2",
                created=1,
                object="model",
                owned_by="xai",
                completion_text_token_price=1,
            )
        ],
    )
    with patch(
        "openai.resources.models.AsyncModels.list",
        new_callable=AsyncMock,
        return_value=page,
    ):
        models = await _client(hass).async_get_models()
    assert [model.id for model in models] == ["grok-page-1", "grok-page-2"]


async def test_model_discovery_translates_pagination_errors(
    hass: HomeAssistant,
) -> None:
    """Keep later-page SDK failures inside the typed client boundary."""

    class _FailingPage:
        data: list[Model] = []

        def __aiter__(self) -> object:
            return self

        async def __anext__(self) -> Model:
            raise _status_error(503)

    with (
        patch(
            "openai.resources.models.AsyncModels.list",
            new_callable=AsyncMock,
            return_value=_FailingPage(),
        ),
        pytest.raises(TransientProviderError),
    ):
        await _client(hass).async_get_models()


async def test_empty_model_catalog_is_allowed(hass: HomeAssistant) -> None:
    """Allow an empty catalog so setup can fall back to the default chat model."""
    with patch(
        "openai.resources.models.AsyncModels.list",
        new_callable=AsyncMock,
        return_value=AsyncModelPage(),
    ):
        models = await _client(hass).async_get_models()
    assert models == ()


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
    with pytest.raises(RefreshRejectedError) as raised:
        await OAuthAccessTokenProvider(session).async_get_access_token()
    assert raised.value.category is ErrorCategory.REFRESH_REJECTED


@pytest.mark.parametrize(
    ("side_effect", "error_type"),
    [
        pytest.param(TimeoutError(), RequestTimeoutError, id="timeout"),
        pytest.param(
            OAuth2TokenRequestTransientError(
                request_info=MagicMock(),
                history=(),
                status=503,
                message="unavailable",
                headers=None,
                domain="spacexai",
            ),
            TransientProviderError,
            id="transient",
        ),
        pytest.param(
            ClientConnectionError(),
            ConnectionFailureError,
            id="client-error",
        ),
        pytest.param(
            OAuth2TokenRequestError(
                request_info=MagicMock(),
                history=(),
                status=500,
                message="failed",
                headers=None,
                domain="spacexai",
            ),
            ConnectionFailureError,
            id="token-request-error",
        ),
    ],
)
async def test_refresh_transport_errors(
    side_effect: Exception,
    error_type: type[SpaceXAIError],
) -> None:
    """Map refresh transport failures to typed connection/transient errors."""
    session = MagicMock(spec=OAuth2Session)
    session.async_ensure_token_valid = AsyncMock(side_effect=side_effect)
    with pytest.raises(error_type):
        await OAuthAccessTokenProvider(session).async_get_access_token()


async def test_refresh_missing_access_token() -> None:
    """Reject a refreshed token payload that omits access_token."""
    session = MagicMock(spec=OAuth2Session)
    session.async_ensure_token_valid = AsyncMock()
    session.token = {"token_type": "Bearer"}
    with pytest.raises(MalformedProviderResponseError):
        await OAuthAccessTokenProvider(session).async_get_access_token()


async def test_refresh_returns_access_token() -> None:
    """Return the access token after a successful OAuth refresh."""
    session = MagicMock(spec=OAuth2Session)
    session.async_ensure_token_valid = AsyncMock()
    session.token = {"access_token": "rotated-token", "token_type": "Bearer"}
    assert (
        await OAuthAccessTokenProvider(session).async_get_access_token()
        == "rotated-token"
    )


async def test_account_http_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Classify account HTTP entitlement failures through the JSON error body."""
    aioclient_mock.get(USERINFO_URL, status=403, json={"error": {"code": "denied"}})
    with pytest.raises(SubscriptionNotEntitledError):
        await _client(hass).async_get_account()


async def test_account_invalid_json(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Treat invalid account JSON as a malformed provider response."""
    aioclient_mock.get(USERINFO_URL, text="not-json")
    with pytest.raises(MalformedProviderResponseError):
        await _client(hass).async_get_account()


async def test_account_http_error_with_unreadable_body(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Classify account HTTP errors even when the body cannot be parsed."""
    aioclient_mock.get(USERINFO_URL, status=401, text="plain")
    with pytest.raises(AuthenticationRejectedError):
        await _client(hass).async_get_account()


async def test_models_sdk_error(hass: HomeAssistant) -> None:
    """Translate SDK failures while listing models."""
    with (
        patch(
            "openai.resources.models.AsyncModels.list",
            new_callable=AsyncMock,
            side_effect=_status_error(403),
        ),
        pytest.raises(SubscriptionNotEntitledError),
    ):
        await _client(hass).async_get_models()


async def test_async_validate(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Compose account identity and model discovery into one snapshot."""
    aioclient_mock.get(
        USERINFO_URL,
        json={"sub": "account-123", "name": "Home User"},
    )
    _mock_developer_models(aioclient_mock)
    page = AsyncModelPage(
        [
            Model(
                id="grok-4.6",
                created=1,
                object="model",
                owned_by="xai",
                completion_text_token_price=1,
            )
        ]
    )
    with patch(
        "openai.resources.models.AsyncModels.list",
        new_callable=AsyncMock,
        return_value=page,
    ):
        snapshot = await _client(hass).async_validate()
    assert snapshot.account.subject == "account-123"
    assert snapshot.has_model("grok-4.6")


async def test_async_validate_allows_catalog_failure(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Keep setup going when model discovery fails after identity succeeds."""
    aioclient_mock.get(
        USERINFO_URL,
        json={"sub": "account-123", "name": "Home User"},
    )
    _mock_developer_models(aioclient_mock, status=503)
    with patch(
        "openai.resources.models.AsyncModels.list",
        new_callable=AsyncMock,
        side_effect=_status_error(503),
    ):
        snapshot = await _client(hass).async_validate()
    assert snapshot.account.subject == "account-123"
    assert snapshot.models == ()
    assert snapshot.image_models == ()
    assert snapshot.video_models == ()


async def test_async_validate_keeps_chat_and_imagine_catalogs_separate(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Use CLI ids for chat and developer ids for Imagine, not a merged list."""
    aioclient_mock.get(
        USERINFO_URL,
        json={"sub": "account-123", "name": "Home User"},
    )
    _mock_developer_models(
        aioclient_mock,
        [
            {
                "id": "grok-imagine-image-2.0",
                "object": "model",
                "created": 1,
                "owned_by": "xai",
            },
            {
                "id": "grok-imagine-image-2026-03-02",
                "object": "model",
                "created": 1,
                "owned_by": "xai",
            },
            {
                "id": "grok-imagine-video-1.5",
                "object": "model",
                "created": 1,
                "owned_by": "xai",
            },
            {
                "id": "grok-4.20-multi-agent-0309",
                "object": "model",
                "created": 1,
                "owned_by": "xai",
            },
        ],
    )
    page = AsyncModelPage(
        [
            Model(
                id="grok-4.6",
                created=1,
                object="model",
                owned_by="xai",
                completion_text_token_price=1,
            )
        ]
    )
    with patch(
        "openai.resources.models.AsyncModels.list",
        new_callable=AsyncMock,
        return_value=page,
    ):
        snapshot = await _client(hass).async_validate()
    assert [model.id for model in snapshot.models] == ["grok-4.6"]
    assert "grok-4.20-multi-agent-0309" not in snapshot.catalog_chat_ids
    assert snapshot.catalog_image_ids == ("grok-imagine-image-2.0",)
    assert snapshot.catalog_video_ids == ("grok-imagine-video-1.5",)
    assert snapshot.has_image_model("grok-imagine-image-2.0")
    assert snapshot.has_image_model("grok-imagine-image-quality")
    assert "grok-imagine-image-2026-03-02" not in snapshot.selectable_image_models


async def test_async_validate_ignores_developer_catalog_failure(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Keep CLI chat discovery when the developer catalog is unavailable."""
    aioclient_mock.get(
        USERINFO_URL,
        json={"sub": "account-123", "name": "Home User"},
    )
    _mock_developer_models(aioclient_mock, status=503)
    page = AsyncModelPage(
        [
            Model(
                id="grok-4.6",
                created=1,
                object="model",
                owned_by="xai",
                completion_text_token_price=1,
            )
        ]
    )
    with patch(
        "openai.resources.models.AsyncModels.list",
        new_callable=AsyncMock,
        return_value=page,
    ):
        snapshot = await _client(hass).async_validate()
    assert snapshot.has_model("grok-4.6")
    assert snapshot.image_models == ()
    assert snapshot.has_image_model("grok-imagine-image-2.0")


async def test_async_validate_checks_subject_before_models(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Fail account mismatch before discovering models for the wrong subject."""
    aioclient_mock.get(
        USERINFO_URL,
        json={"sub": "other-account", "name": "Other"},
    )
    with (
        patch(
            "openai.resources.models.AsyncModels.list",
            new_callable=AsyncMock,
        ) as mock_models,
        pytest.raises(AccountMismatchError),
    ):
        await _client(hass).async_validate(expected_subject="account-123")
    mock_models.assert_not_awaited()


async def test_sdk_client_reuses_and_updates_token(hass: HomeAssistant) -> None:
    """Reuse one SDK client and rotate its API key across requests."""

    class _FakeSDK:
        def __init__(self) -> None:
            self.api_key = "unset"
            self.models = MagicMock()
            self.platform_headers = MagicMock()

    page = AsyncModelPage(
        [
            Model(
                id="grok-4.5",
                created=1,
                object="model",
                owned_by="xai",
                completion_text_token_price=1,
            )
        ]
    )
    provider = MagicMock()
    provider.async_get_access_token = AsyncMock(side_effect=["token-a", "token-b"])
    client = SpaceXAIClient(hass, provider, runtime_session=False)
    sdk = _FakeSDK()
    sdk.models.list = AsyncMock(return_value=page)

    def _build_sdk(**kwargs: object) -> _FakeSDK:
        sdk.api_key = kwargs["api_key"]  # type: ignore[assignment]
        return sdk

    with (
        patch(
            "homeassistant.components.spacexai.client.openai.AsyncOpenAI",
            side_effect=_build_sdk,
        ) as mock_ctor,
        patch.object(hass, "async_add_executor_job", new_callable=AsyncMock),
    ):
        await client.async_get_models()
        assert client._sdk_client is sdk
        assert sdk.api_key == "token-a"
        assert mock_ctor.call_count == 1
        await client.async_get_models()
        assert client._sdk_client is sdk
        assert sdk.api_key == "token-b"
        assert mock_ctor.call_count == 1


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
            max_output_tokens=2048,
            prompt_cache_key="conversation-id",
        )
    assert returned is stream
    assert create.call_args.kwargs["stream"] is True
    assert create.call_args.kwargs["store"] is False
    assert create.call_args.kwargs["include"] == ["reasoning.encrypted_content"]
    assert create.call_args.kwargs["parallel_tool_calls"] is False
    assert create.call_args.kwargs["prompt_cache_key"] == "conversation-id"
    assert "timeout" not in create.call_args.kwargs
    assert "text" not in create.call_args.kwargs


async def test_stream_create_timeout_is_typed(hass: HomeAssistant) -> None:
    """Translate a TTFB asyncio timeout into RequestTimeoutError."""
    with (
        patch(
            "openai.resources.responses.AsyncResponses.create",
            new_callable=AsyncMock,
            side_effect=TimeoutError(),
        ),
        pytest.raises(RequestTimeoutError),
    ):
        await _client(hass).async_stream_response(
            model="grok-4.5",
            input=[],
            tools=[],
            max_output_tokens=2048,
            prompt_cache_key="conversation-id",
        )


@pytest.mark.parametrize(
    ("status", "model", "body", "runtime", "operation", "error_type"),
    [
        pytest.param(
            401,
            None,
            {},
            False,
            Operation.RESPONSE,
            AuthenticationRejectedError,
            id="401",
        ),
        pytest.param(
            401,
            None,
            {},
            True,
            Operation.RESPONSE,
            ReauthenticationRequiredError,
            id="runtime-401",
        ),
        pytest.param(
            402, None, {}, False, Operation.RESPONSE, QuotaLimitedError, id="402"
        ),
        pytest.param(
            403,
            None,
            {},
            False,
            Operation.RESPONSE,
            SubscriptionNotEntitledError,
            id="403-response",
        ),
        pytest.param(
            403,
            None,
            {},
            False,
            Operation.MODELS,
            SubscriptionNotEntitledError,
            id="403-models",
        ),
        pytest.param(
            403,
            None,
            {},
            False,
            Operation.ACCOUNT,
            SubscriptionNotEntitledError,
            id="403-account",
        ),
        pytest.param(
            403,
            None,
            {},
            False,
            Operation.REVOCATION,
            PermanentProviderError,
            id="403-revocation",
        ),
        pytest.param(
            403,
            None,
            {"error": {"code": "subscription_required", "message": "inactive"}},
            False,
            Operation.REVOCATION,
            SubscriptionNotEntitledError,
            id="403-revocation-subscription-code",
        ),
        pytest.param(
            403,
            None,
            {"error": {"code": "permission_denied"}},
            False,
            Operation.RESPONSE,
            PermanentProviderError,
            id="403-response-permission-denied",
        ),
        pytest.param(
            403,
            None,
            {
                "error": {
                    "message": "Subscription inactive; account is not entitled",
                }
            },
            False,
            Operation.REVOCATION,
            SubscriptionNotEntitledError,
            id="403-revocation-subscription-message",
        ),
        pytest.param(
            426,
            None,
            {},
            False,
            Operation.RESPONSE,
            PermanentProviderError,
            id="426",
        ),
        pytest.param(
            404,
            "grok-4.5",
            {"code": "model"},
            False,
            Operation.RESPONSE,
            ModelNotEntitledError,
            id="404",
        ),
        pytest.param(
            408, None, {}, False, Operation.RESPONSE, RequestTimeoutError, id="408"
        ),
        pytest.param(
            429, None, {}, False, Operation.RESPONSE, RateLimitedError, id="429"
        ),
        pytest.param(
            500, None, {}, False, Operation.RESPONSE, TransientProviderError, id="5xx"
        ),
        pytest.param(
            400,
            None,
            {
                "code": "invalid-argument",
                "error": (
                    "Incorrect API key provided. You can obtain an API key "
                    "from https://console.x.ai."
                ),
            },
            False,
            Operation.RESPONSE,
            AuthenticationRejectedError,
            id="400-credential",
        ),
        pytest.param(
            400,
            None,
            {"code": "invalid_token"},
            False,
            Operation.RESPONSE,
            AuthenticationRejectedError,
            id="400-invalid-token-code",
        ),
        pytest.param(
            400,
            None,
            {"error": {"message": "Incorrect API key provided"}},
            False,
            Operation.RESPONSE,
            AuthenticationRejectedError,
            id="400-nested-error-message",
        ),
        pytest.param(
            400,
            None,
            {"error": 1, "message": "Incorrect API key provided"},
            False,
            Operation.RESPONSE,
            AuthenticationRejectedError,
            id="400-fallback-message",
        ),
        pytest.param(
            400,
            None,
            {
                "code": "invalid-argument",
                "error": "Request mentioned an api key field incorrectly",
            },
            False,
            Operation.RESPONSE,
            PermanentProviderError,
            id="400-bare-api-key-not-credential",
        ),
        pytest.param(
            400,
            None,
            None,
            False,
            Operation.RESPONSE,
            PermanentProviderError,
            id="400-non-mapping-body",
        ),
    ],
)
def test_status_classification(
    hass: HomeAssistant,
    status: int,
    model: str | None,
    body: object,
    runtime: bool,
    operation: Operation,
    error_type: type[SpaceXAIError],
) -> None:
    """Classify provider status families, including runtime reauthentication."""
    error = _client(hass, runtime=runtime).translate_sdk_error(
        _status_error(status, body),
        ErrorContext(operation=operation, model=model),
    )
    assert isinstance(error, error_type)
    assert error.context.operation is operation
    assert error.context.model == model


async def test_revoke(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """Send refresh-token revocation data on success."""
    aioclient_mock.post(REVOCATION_URL, status=200)
    await _client(hass).async_revoke("refresh", "client", "secret")
    assert aioclient_mock.mock_calls[0][2]["token"] == "refresh"
    assert aioclient_mock.mock_calls[0][2]["client_secret"] == "secret"


async def test_revoke_timeout(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Surface TimeoutError while revoking a refresh token."""
    aioclient_mock.post(REVOCATION_URL, exc=TimeoutError())
    with pytest.raises(RequestTimeoutError):
        await _client(hass).async_revoke("refresh-token", "client-id")


async def test_revoke_http_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Classify revocation HTTP failures."""
    aioclient_mock.post(REVOCATION_URL, status=401)
    with pytest.raises(AuthenticationRejectedError):
        await _client(hass).async_revoke("refresh-token", "client-id")


async def test_revoke_connection_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Surface connection failures while revoking a refresh token."""
    aioclient_mock.post(REVOCATION_URL, exc=ClientConnectionError())
    with pytest.raises(ConnectionFailureError):
        await _client(hass).async_revoke("refresh-token", "client-id")


@pytest.mark.parametrize(
    ("err", "error_type"),
    [
        pytest.param(
            APITimeoutError(request=httpx.Request("GET", "https://api.x.ai/v1")),
            RequestTimeoutError,
            id="timeout",
        ),
        pytest.param(
            APIConnectionError(request=httpx.Request("GET", "https://api.x.ai/v1")),
            ConnectionFailureError,
            id="connection",
        ),
        pytest.param(OpenAIError("denied"), PermanentProviderError, id="generic"),
    ],
)
def test_translate_non_status_sdk_errors(
    hass: HomeAssistant,
    err: Exception,
    error_type: type[SpaceXAIError],
) -> None:
    """Translate non-status SDK failures at the client boundary."""
    assert isinstance(
        _client(hass).translate_sdk_error(
            err, ErrorContext(operation=Operation.RESPONSE)
        ),
        error_type,
    )


def test_provider_error_helpers_accept_non_mapping_bodies(hass: HomeAssistant) -> None:
    """Ignore non-mapping provider bodies while classifying failures."""
    error = _client(hass).translate_sdk_error(
        _status_error(400, "not-a-mapping"),
        ErrorContext(operation=Operation.RESPONSE),
    )
    assert isinstance(error, PermanentProviderError)


def test_subscription_and_permission_denial_helpers() -> None:
    """Keep body/code helpers tight for subscription vs permission 403s."""
    assert not _is_subscription_denial(400, None, None)
    assert _is_subscription_denial(
        403, None, {"error": {"message": "Subscription required for access"}}
    )
    assert _is_permission_denial(
        None, {"error": {"message": "Permission denied for this resource"}}
    )


async def test_safe_json_returns_none_on_decode_error() -> None:
    """Ignore unreadable error bodies while classifying HTTP failures."""
    response = AsyncMock()
    response.json = AsyncMock(side_effect=ValueError("bad json"))
    assert await _safe_json(response) is None


async def test_sdk_schema_violation_is_malformed(hass: HomeAssistant) -> None:
    """Treat an SDK schema violation on create as a malformed provider response."""
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


def test_error_category_values_match_translation_keys() -> None:
    """Ensure every closed error category value is a strings.json exception key."""
    assert {category.value for category in ErrorCategory} == {
        "authentication_rejected",
        "refresh_rejected",
        "reauthentication_required",
        "account_mismatch",
        "subscription_not_entitled",
        "no_conversation_models",
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


async def test_generate_image_success(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Return decoded image bytes from the Imagine endpoint."""
    aioclient_mock.post(
        IMAGES_URL,
        json={
            "data": [
                {
                    "b64_json": base64.b64encode(b"image-bytes").decode(),
                    "revised_prompt": "a red bicycle at sunset",
                }
            ]
        },
    )
    generated = await _client(hass).async_generate_image(
        model="grok-imagine-image-quality", prompt="a red bicycle"
    )
    assert generated.image_data == b"image-bytes"
    assert generated.mime_type == "image/jpeg"
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


async def test_edit_image_success(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Return decoded image bytes from the Imagine edits endpoint."""
    aioclient_mock.post(
        IMAGES_EDIT_URL,
        json={
            "data": [
                {
                    "b64_json": base64.b64encode(b"edited-bytes").decode(),
                    "revised_prompt": "a red bicycle at noon",
                }
            ]
        },
    )
    generated = await _client(hass).async_edit_image(
        model="grok-imagine-image-quality",
        prompt="make it noon",
        images=["https://example.com/bike.jpg"],
    )
    assert generated.image_data == b"edited-bytes"
    assert generated.mime_type == "image/jpeg"
    request = aioclient_mock.mock_calls[0][2]
    assert request["image"] == {
        "url": "https://example.com/bike.jpg",
        "type": "image_url",
    }


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param("not-an-object", id="not-an-object"),
        pytest.param({"data": []}, id="empty-data"),
        pytest.param({"data": [{"b64_json": ""}]}, id="empty-base64"),
    ],
)
async def test_edit_image_malformed(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, payload: object
) -> None:
    """Reject malformed Imagine edit responses."""
    aioclient_mock.post(IMAGES_EDIT_URL, json=payload)
    with pytest.raises(MalformedProviderResponseError):
        await _client(hass).async_edit_image(
            model="grok-imagine-image-quality",
            prompt="make it noon",
            images=["https://example.com/bike.jpg"],
        )


async def test_edit_image_status_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Classify an Imagine edit endpoint status failure."""
    aioclient_mock.post(
        IMAGES_EDIT_URL, json={"error": {"code": "rate_limited"}}, status=429
    )
    with pytest.raises(RateLimitedError):
        await _client(hass).async_edit_image(
            model="grok-imagine-image-quality",
            prompt="make it noon",
            images=["https://example.com/bike.jpg"],
        )


async def test_edit_image_connection_failure(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Surface a transport failure from the Imagine edit endpoint."""
    aioclient_mock.post(IMAGES_EDIT_URL, exc=ClientConnectionError("offline"))
    with pytest.raises(ConnectionFailureError):
        await _client(hass).async_edit_image(
            model="grok-imagine-image-quality",
            prompt="make it noon",
            images=["https://example.com/bike.jpg"],
        )


async def test_generate_video_missing_request_id(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Reject a video create response that omits request_id."""
    aioclient_mock.post(VIDEOS_URL, json={})
    with pytest.raises(MalformedProviderResponseError):
        await _client(hass).async_generate_video(
            model="grok-imagine-video-1.5", prompt="ball"
        )


async def test_generate_video_malformed_create(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Reject a non-object video create response."""
    aioclient_mock.post(VIDEOS_URL, json="not-an-object")
    with pytest.raises(MalformedProviderResponseError):
        await _client(hass).async_generate_video(
            model="grok-imagine-video-1.5", prompt="ball"
        )


@pytest.mark.parametrize("status", ["failed", "expired"])
async def test_generate_video_terminal_status(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, status: str
) -> None:
    """Raise when the provider marks a video job failed or expired."""
    aioclient_mock.post(VIDEOS_URL, json={"request_id": "req-1"})
    aioclient_mock.get(
        f"{DEVELOPER_API_BASE_URL}/videos/req-1", json={"status": status}
    )
    with pytest.raises(PermanentProviderError):
        await _client(hass).async_generate_video(
            model="grok-imagine-video-1.5", prompt="ball"
        )


async def test_generate_video_times_out(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Raise when video polling exceeds the provider timeout."""
    aioclient_mock.post(VIDEOS_URL, json={"request_id": "req-1"})
    aioclient_mock.get(
        f"{DEVELOPER_API_BASE_URL}/videos/req-1", json={"status": "pending"}
    )
    with (
        patch(
            "homeassistant.components.spacexai.client.monotonic",
            side_effect=[0, 301],
        ),
        patch(
            "homeassistant.components.spacexai.client.asyncio.sleep",
            new_callable=AsyncMock,
        ),
        pytest.raises(RequestTimeoutError),
    ):
        await _client(hass).async_generate_video(
            model="grok-imagine-video-1.5", prompt="ball"
        )


async def test_generate_video_malformed_status(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Reject a malformed video status payload."""
    aioclient_mock.post(VIDEOS_URL, json={"request_id": "req-1"})
    aioclient_mock.get(f"{DEVELOPER_API_BASE_URL}/videos/req-1", json="not-an-object")
    with pytest.raises(MalformedProviderResponseError):
        await _client(hass).async_generate_video(
            model="grok-imagine-video-1.5", prompt="ball"
        )


async def test_generate_video_refreshes_token_while_polling(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Refresh the OAuth access token on each video status poll."""
    provider = AsyncMock()
    provider.async_get_access_token = AsyncMock(
        side_effect=["token-start", "token-poll-1", "token-poll-2"]
    )
    client = SpaceXAIClient(hass, provider, runtime_session=False)

    aioclient_mock.post(VIDEOS_URL, json={"request_id": "req-1"})
    status_url = f"{DEVELOPER_API_BASE_URL}/videos/req-1"
    status_payloads = iter(
        [
            {"status": "pending"},
            {"status": "done", "video": {"url": "https://vidgen.example/v.mp4"}},
        ]
    )

    async def status_side_effect(
        method: str, url: object, data: object
    ) -> AiohttpClientMockResponse:
        return AiohttpClientMockResponse(
            method=method,
            url=url,
            json=next(status_payloads),
        )

    aioclient_mock.get(status_url, side_effect=status_side_effect)

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


async def test_generate_video_create_sends_image_and_duration(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Send image-to-video source and duration on the Imagine create request."""
    aioclient_mock.post(VIDEOS_URL, json={"request_id": "req-1"})
    aioclient_mock.get(
        f"{DEVELOPER_API_BASE_URL}/videos/req-1",
        json={"status": "done", "video": {"url": "https://vidgen.example/from-image.mp4"}},
    )
    with patch(
        "homeassistant.components.spacexai.client.asyncio.sleep",
        new_callable=AsyncMock,
    ):
        generated = await _client(hass).async_generate_video(
            model="grok-imagine-video-1.5",
            prompt="animate this still",
            image_url="https://example.com/ball.jpg",
            duration=2,
        )
    assert generated.url == "https://vidgen.example/from-image.mp4"
    request = aioclient_mock.mock_calls[0][2]
    assert request["model"] == "grok-imagine-video-1.5"
    assert request["prompt"] == "animate this still"
    assert request["image"] == {"url": "https://example.com/ball.jpg"}
    assert request["duration"] == 2
