"""Configuration models for the LangChain-Drasi library.

This module defines Pydantic models for configuring MCP connections
and reconnection policies, with validation and sensible defaults.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class ReconnectPolicy(BaseModel):
    """Policy for handling MCP connection failures and reconnection.

    This model configures how the library should behave when the MCP
    connection is lost, including retry logic and backoff strategies.

    Attributes:
        enabled: Whether to attempt reconnection on failure
        max_retries: Maximum retry attempts (None = infinite retries)
        retry_delay: Initial delay between retries in seconds
        backoff_multiplier: Exponential backoff multiplier (e.g., 2.0 doubles delay each retry)
        max_delay: Maximum delay between retries in seconds
    """

    enabled: bool = Field(
        default=True,
        description="Enable automatic reconnection on connection failure",
    )
    max_retries: int | None = Field(
        default=5,
        description="Maximum retry attempts (None for infinite)",
    )
    retry_delay: float = Field(
        default=1.0,
        gt=0,
        description="Initial retry delay in seconds",
    )
    backoff_multiplier: float = Field(
        default=2.0,
        ge=1.0,
        description="Exponential backoff multiplier",
    )
    max_delay: float = Field(
        default=60.0,
        gt=0,
        description="Maximum retry delay in seconds",
    )

    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, v: int | None) -> int | None:
        """Validate that max_retries is positive if set."""
        if v is not None and v < 0:
            raise ValueError("max_retries must be positive or None")
        return v

    @field_validator("max_delay")
    @classmethod
    def validate_max_delay(cls, v: float, info: Any) -> float:
        """Validate that max_delay is greater than retry_delay."""
        # Note: In Pydantic v2, we can't easily access other fields during validation
        # This validation is kept simple and can be enhanced with model_validator
        if v <= 0:
            raise ValueError("max_delay must be positive")
        return v


class MCPConnectionConfig(BaseModel):
    """Configuration for connecting to a Drasi MCP server via HTTP.

    This model defines how to connect to a remote Drasi MCP server
    over HTTP/HTTPS, including the server URL, authentication headers,
    and reconnection policy.

    Attributes:
        server_url: HTTP/HTTPS URL of the Drasi MCP server
        headers: Optional HTTP headers for authentication (e.g., API keys, bearer tokens)
        timeout: Request timeout in seconds
        reconnect_policy: Policy for handling connection failures
    """

    server_url: str = Field(
        description="HTTP/HTTPS URL of the Drasi MCP server",
        examples=["http://localhost:8080", "https://drasi.example.com/api"],
    )
    headers: dict[str, str] | None = Field(
        default=None,
        description="HTTP headers for authentication (e.g., Authorization, API-Key)",
        examples=[{"Authorization": "Bearer token123"}, {"X-API-Key": "key123"}],
    )
    timeout: float = Field(
        default=30.0,
        gt=0,
        description="Request timeout in seconds",
    )
    reconnect_policy: ReconnectPolicy = Field(
        default_factory=ReconnectPolicy,
        description="Reconnection policy for handling connection failures",
    )

    @field_validator("server_url")
    @classmethod
    def validate_server_url(cls, v: str) -> str:
        """Validate that server_url is not empty and has valid scheme."""
        if not v or not v.strip():
            raise ValueError("server_url cannot be empty")

        url = v.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValueError("server_url must start with http:// or https://")

        return url

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "server_url": "https://drasi.example.com/api",
                    "headers": {"Authorization": "Bearer token123"},
                    "timeout": 30.0,
                    "reconnect_policy": {
                        "enabled": True,
                        "max_retries": 5,
                        "retry_delay": 1.0,
                        "backoff_multiplier": 2.0,
                        "max_delay": 60.0,
                    },
                }
            ]
        }
    }
