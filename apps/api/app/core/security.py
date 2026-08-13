"""JWT validation, execution context, and dev token minting."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(slots=True)
class ExecutionContext:
    organization_id: UUID
    actor_id: UUID
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    email: str | None = None
    display_name: str | None = None
    token_type: str = "bearer"
    raw_claims: dict[str, Any] = field(default_factory=dict)

    def has_role(self, *roles: str) -> bool:
        return any(r in self.roles for r in roles)

    def require_permission(self, permission: str) -> None:
        if permission not in self.permissions and "admin" not in self.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"missing permission: {permission}",
            )


ROLE_PERMISSIONS: dict[str, list[str]] = {
    "customer": ["conversations:write", "approvals:respond", "documents:read"],
    "support_agent": [
        "conversations:write",
        "conversations:read_all",
        "approvals:respond",
        "documents:read",
        "agent_runs:read",
        "jobs:read",
        "audit:read",
    ],
    "supervisor": [
        "conversations:write",
        "conversations:read_all",
        "approvals:respond",
        "documents:read",
        "documents:write",
        "agent_runs:read",
        "jobs:read",
        "jobs:replay",
        "audit:read",
        "evaluations:write",
    ],
    "admin": [
        "conversations:write",
        "conversations:read_all",
        "approvals:respond",
        "documents:read",
        "documents:write",
        "documents:delete",
        "agent_runs:read",
        "jobs:read",
        "jobs:replay",
        "audit:read",
        "evaluations:write",
        "admin:all",
    ],
}


def permissions_for_roles(roles: list[str]) -> list[str]:
    perms: set[str] = set()
    for role in roles:
        perms.update(ROLE_PERMISSIONS.get(role, []))
    return sorted(perms)


def mint_access_token(
    *,
    organization_id: UUID | str,
    actor_id: UUID | str,
    roles: list[str],
    email: str | None = None,
    settings: Settings | None = None,
    expires_minutes: int = 60 * 12,
    token_use: str = "app",
) -> str:
    cfg = settings or get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(actor_id),
        "org_id": str(organization_id),
        "roles": roles,
        "email": email,
        "iss": "enterprise-ai-dev",
        "aud": cfg.oidc_audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
        "token_use": token_use,
    }
    return jwt.encode(payload, cfg.dev_auth_secret, algorithm="HS256")


def mint_dev_token(
    *,
    organization_id: UUID | str,
    actor_id: UUID | str,
    roles: list[str],
    email: str | None = None,
    settings: Settings | None = None,
    expires_minutes: int = 60 * 12,
) -> str:
    cfg = settings or get_settings()
    if not cfg.dev_auth_enabled:
        raise RuntimeError("dev auth is disabled")
    return mint_access_token(
        organization_id=organization_id,
        actor_id=actor_id,
        roles=roles,
        email=email,
        settings=cfg,
        expires_minutes=expires_minutes,
        token_use="dev",
    )


@lru_cache
def _jwks_cache_key(issuer: str) -> str:
    return issuer.rstrip("/")


async def _fetch_jwks(issuer: str) -> dict[str, Any]:
    import httpx

    url = f"{issuer.rstrip('/')}/.well-known/jwks.json"
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


async def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="invalid token header") from exc

    alg = header.get("alg")
    if alg == "HS256" and (settings.dev_auth_enabled or settings.registration_enabled):
        try:
            return jwt.decode(
                token,
                settings.dev_auth_secret,
                algorithms=["HS256"],
                audience=settings.oidc_audience,
                options={"verify_iss": False},
            )
        except JWTError as exc:
            raise HTTPException(status_code=401, detail="invalid app token") from exc

    # OIDC JWKS path
    try:
        jwks = await _fetch_jwks(settings.oidc_issuer)
        kid = header.get("kid")
        key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        if key is None and jwks.get("keys"):
            key = jwks["keys"][0]
        if key is None:
            raise HTTPException(status_code=401, detail="jwks key not found")
        return jwt.decode(
            token,
            key,
            algorithms=[alg or "RS256"],
            audience=settings.oidc_audience,
            issuer=settings.oidc_issuer,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="oidc validation failed") from exc


def claims_to_context(claims: dict[str, Any]) -> ExecutionContext:
    org_raw = claims.get("org_id") or claims.get("organization_id")
    sub = claims.get("sub")
    if not org_raw or not sub:
        raise HTTPException(status_code=401, detail="token missing org or sub")
    roles = list(claims.get("roles") or claims.get("permissions") or ["customer"])
    if isinstance(roles, str):
        roles = [roles]
    return ExecutionContext(
        organization_id=UUID(str(org_raw)),
        actor_id=UUID(str(sub)),
        roles=[str(r) for r in roles],
        permissions=permissions_for_roles([str(r) for r in roles]),
        email=claims.get("email"),
        display_name=claims.get("name"),
        token_type=str(claims.get("token_use") or "oidc"),
        raw_claims=claims,
    )


async def get_execution_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> ExecutionContext:
    token: str | None = None
    if credentials is not None and credentials.credentials:
        token = credentials.credentials
    else:
        token = request.query_params.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="missing bearer token")
    claims = await decode_access_token(token, settings)
    return claims_to_context(claims)


async def get_optional_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> ExecutionContext | None:
    if credentials is None and not request.query_params.get("access_token"):
        return None
    return await get_execution_context(request, credentials, settings)
