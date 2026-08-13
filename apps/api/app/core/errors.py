"""RFC 9457 Problem Details error handling."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ProblemError(Exception):
    def __init__(
        self,
        *,
        status: int,
        title: str,
        detail: str | None = None,
        type: str = "about:blank",
        extensions: dict[str, Any] | None = None,
    ) -> None:
        self.status = status
        self.title = title
        self.detail = detail
        self.type = type
        self.extensions = extensions or {}
        super().__init__(detail or title)


def problem_response(
    *,
    status: int,
    title: str,
    detail: str | None = None,
    type: str = "about:blank",
    instance: str | None = None,
    extensions: dict[str, Any] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": type,
        "title": title,
        "status": status,
    }
    if detail:
        body["detail"] = detail
    if instance:
        body["instance"] = instance
    if extensions:
        body.update(extensions)
    return JSONResponse(
        status_code=status,
        content=body,
        media_type="application/problem+json",
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProblemError)
    async def problem_handler(_: Request, exc: ProblemError) -> JSONResponse:
        return problem_response(
            status=exc.status,
            title=exc.title,
            detail=exc.detail,
            type=exc.type,
            extensions=exc.extensions,
        )

    @app.exception_handler(HTTPException)
    async def http_handler(request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail
        title = "HTTP Error"
        if isinstance(detail, dict):
            return problem_response(
                status=exc.status_code,
                title=str(detail.get("title") or title),
                detail=str(detail.get("detail") or detail),
                instance=str(request.url.path),
            )
        return problem_response(
            status=exc.status_code,
            title=title,
            detail=str(detail),
            instance=str(request.url.path),
        )

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return problem_response(
            status=exc.status_code,
            title="HTTP Error",
            detail=str(exc.detail),
            instance=str(request.url.path),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return problem_response(
            status=422,
            title="Validation Error",
            detail="Request validation failed",
            type="https://httpstatuses.com/422",
            instance=str(request.url.path),
            extensions={"errors": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        return problem_response(
            status=500,
            title="Internal Server Error",
            detail="An unexpected error occurred",
            instance=str(request.url.path),
        )
