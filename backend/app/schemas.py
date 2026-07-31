from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class TokenOut(BaseModel):
    access_token: str
    email: str
    handle: str


class MonitorIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    url: str = Field(min_length=4, max_length=2048)
    method: str = "GET"
    expected_status: int = 200
    interval_seconds: int = Field(default=60, ge=30, le=3600)
    is_public: bool = False


class MonitorPatch(BaseModel):
    name: str | None = None
    url: str | None = None
    interval_seconds: int | None = Field(default=None, ge=30, le=3600)
    is_active: bool | None = None
    is_public: bool | None = None


class MonitorOut(BaseModel):
    id: int
    name: str
    slug: str
    url: str
    method: str
    expected_status: int
    interval_seconds: int
    is_active: bool
    is_public: bool
    current_status: str
    last_checked_at: datetime | None
    uptime_24h: float | None = None
    avg_latency_ms: float | None = None

    class Config:
        from_attributes = True


class CheckOut(BaseModel):
    checked_at: datetime
    status_code: int | None
    latency_ms: float | None
    ok: bool
    error: str | None

    class Config:
        from_attributes = True


class IncidentOut(BaseModel):
    id: int
    monitor_id: int
    monitor_name: str | None = None
    started_at: datetime
    resolved_at: datetime | None
    cause: str
    summary: str | None
    acknowledged: bool

    class Config:
        from_attributes = True
