from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScopeBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    domain: str = Field(min_length=1, max_length=255)
    allowed_ports: str | None = Field(default=None, max_length=500)
    allowed_checks: str | None = None
    description: str | None = None

    @field_validator("domain")
    @classmethod
    def normalize_domain(cls, value: str) -> str:
        value = value.strip().lower().rstrip(".")
        if not value:
            raise ValueError("Domain cannot be empty.")
        return value


class ScopeCreate(ScopeBase):
    pass


class ScopeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    domain: str | None = Field(default=None, min_length=1, max_length=255)
    allowed_ports: str | None = Field(default=None, max_length=500)
    allowed_checks: str | None = None
    description: str | None = None
    is_active: bool | None = None

    @field_validator("domain")
    @classmethod
    def normalize_domain(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().lower().rstrip(".")
        if not value:
            raise ValueError("Domain cannot be empty.")
        return value


class ScopeResponse(ScopeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
