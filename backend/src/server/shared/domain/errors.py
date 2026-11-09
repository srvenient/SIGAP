from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DomainError(Exception):
    """Error de negocio. Cada subclase define su código HTTP y su mensaje."""

    status_code: int = 400
    detail: str = "Operación no válida"

    def __init__(self, detail: str | None = None):
        if detail:
            self.detail = detail
        super().__init__(self.detail)


async def _domain_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


def register_domain_errors(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _domain_error_handler)
