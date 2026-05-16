"""modulex-integrations — community-contributable integrations for ModuleX.

Every integration lives at ``modulex_integrations.tools.<name>`` and is
discovered by the modulex runtime via the ``modulex.tools`` entry-point
group declared in ``pyproject.toml``.

This top-level module re-exports the schema types so contributors can
write a manifest with::

    from modulex_integrations import (
        IntegrationManifest, ActionDefinition, OAuth2AuthSchema, ...
    )
"""
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    AuthSchema,
    BearerTokenAuthSchema,
    CustomAuthSchema,
    EnvVar,
    IntegrationManifest,
    InternalAuthSchema,
    ModulexKeyAuthSchema,
    OAuth2AuthSchema,
    OAuthConfig,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

try:
    __version__ = _pkg_version("modulex-integrations")
except PackageNotFoundError:  # source checkout without `pip install -e .`
    __version__ = "0.0.0+unknown"

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
    "__version__",
]
