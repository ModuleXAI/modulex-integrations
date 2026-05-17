"""Schema definitions for the modulex-integrations package.

Every integration declares its metadata by constructing an
``IntegrationManifest`` instance in its own ``manifest.py``. The modulex
runtime imports these manifests via the ``modulex.tools`` entry-point
group and uses them to drive credential UI, validation, and tool
discovery.

Design choices worth knowing:

- All models use ``extra="forbid"`` so a typo in a contributor's
  manifest fails at import time, not at runtime.
- ``auth_schemas`` is a discriminated union keyed on ``auth_type``;
  the same integration can expose multiple credential methods (GitHub
  supports both OAuth2 and a personal access token).
- Action ``output_schema`` is intentionally absent. The shape of every
  action's return value is derived from the LangChain ``@tool``
  function's return-type annotation (defined in each integration's
  ``outputs.py``); the runtime obtains it via
  ``Model.model_json_schema()`` at startup.
"""
from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ActionDefinition",
    "ApiKeyAuthSchema",
    "AuthSchema",
    "BearerTokenAuthSchema",
    "CustomAuthSchema",
    "EnvVar",
    "IntegrationManifest",
    "InternalAuthSchema",
    "ModulexKeyAuthSchema",
    "OAuth2AuthSchema",
    "OAuthConfig",
    "ParameterDef",
    "SuccessIndicators",
    "TestEndpoint",
]


# --- Parameters --------------------------------------------------------

ParameterType = Literal[
    "string",
    "integer",
    "number",
    "boolean",
    "array",
    "object",
]


class ParameterDef(BaseModel):
    """Definition of a single action parameter."""

    model_config = ConfigDict(extra="forbid")

    type: ParameterType
    description: str
    default: Any = None
    required: bool = False


# --- Actions -----------------------------------------------------------


class ActionDefinition(BaseModel):
    """One callable action exposed by the integration.

    The return shape is derived from the matching ``@tool`` function's
    return-type annotation in ``tools.py`` — do not duplicate it here.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    description: str
    parameters: dict[str, ParameterDef] = Field(default_factory=dict)


# --- Credentials -------------------------------------------------------


class EnvVar(BaseModel):
    """A configurable secret/setting the operator must provide."""

    model_config = ConfigDict(extra="forbid")

    name: str
    display_name: str
    description: str
    required: bool = True
    sensitive: bool = False
    only_for_custom: bool = False
    sample_format: str | None = None
    about_url: str | None = None


class SuccessIndicators(BaseModel):
    """How to tell a credential test endpoint succeeded."""

    model_config = ConfigDict(extra="forbid")

    status_codes: list[int]
    response_fields: list[str] | None = None


class TestEndpoint(BaseModel):
    """Endpoint hit to validate a configured credential.

    URL, header, body, and query-parameter values may contain
    placeholders such as ``{access_token}``, ``{token}``, or
    ``{api_key}`` which the runtime substitutes with the resolved
    credential value. ``body`` is sent as a JSON payload on non-GET
    methods (e.g. POST-based credential checks such as Exa's
    ``POST /search``). ``params`` is the URL query string used by
    integrations that pass their credential as a query parameter
    (e.g. ConvertAPI's ``?Secret={api_key}``, Nasdaq's
    ``?api_key={api_key}``).
    """

    __test__ = False  # pydantic model, not a pytest test class
    model_config = ConfigDict(extra="forbid")

    url: str
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
    params: dict[str, str] = Field(default_factory=dict)
    body: dict[str, Any] | None = None
    success_indicators: SuccessIndicators
    cost_level: str = "free"
    description: str | None = None


# --- Auth schemas (discriminated union) --------------------------------


class _AuthSchemaBase(BaseModel):
    """Fields shared by every auth_schema variant.

    ``test_endpoint`` is optional: some legacy integrations (e.g.
    instacart, hackernews) use ``modulex_key`` for a "public API"
    that has no credential to validate, so they ship no
    test_endpoint at all. The modulex runtime skips credential
    testing in that case.
    """

    model_config = ConfigDict(extra="forbid")

    display_name: str
    description: str
    setup_instructions: list[str] | None = None
    setup_environment_variables: list[EnvVar] = Field(default_factory=list)
    test_endpoint: TestEndpoint | None = None


class OAuthConfig(BaseModel):
    """OAuth 2.0 authorize/token URL bundle."""

    model_config = ConfigDict(extra="forbid")

    auth_url: str
    token_url: str
    scopes: list[str] = Field(default_factory=list)
    token_auth_method: Literal["body", "basic"] = "body"


class OAuth2AuthSchema(_AuthSchemaBase):
    auth_type: Literal["oauth2"] = "oauth2"
    oauth_config: OAuthConfig


class BearerTokenAuthSchema(_AuthSchemaBase):
    auth_type: Literal["bearer_token"] = "bearer_token"


class ApiKeyAuthSchema(_AuthSchemaBase):
    auth_type: Literal["api_key"] = "api_key"


class ModulexKeyAuthSchema(_AuthSchemaBase):
    auth_type: Literal["modulex_key"] = "modulex_key"


class CustomAuthSchema(_AuthSchemaBase):
    auth_type: Literal["custom"] = "custom"


class InternalAuthSchema(_AuthSchemaBase):
    auth_type: Literal["internal"] = "internal"


AuthSchema = Annotated[
    OAuth2AuthSchema
    | BearerTokenAuthSchema
    | ApiKeyAuthSchema
    | ModulexKeyAuthSchema
    | CustomAuthSchema
    | InternalAuthSchema,
    Field(discriminator="auth_type"),
]


# --- Top-level manifest ------------------------------------------------


class IntegrationManifest(BaseModel):
    """The contract every integration's ``manifest.py`` produces."""

    model_config = ConfigDict(extra="forbid")

    integration_type: Literal["tool"] = "tool"
    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    display_name: str
    description: str
    version: str = "1.0.0"
    author: str = "ModuleX"
    logo: str | None = None
    app_url: str | None = None
    categories: list[str] = Field(default_factory=list)
    actions: list[ActionDefinition] = Field(default_factory=list)
    auth_schemas: list[AuthSchema] = Field(default_factory=list)
