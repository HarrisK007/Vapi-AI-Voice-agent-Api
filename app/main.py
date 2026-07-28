from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import init_db
from app.routes import patients, vapi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("patient_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables
    logger.info("Initializing SQLite database tables...")
    init_db()
    yield
    # Shutdown
    logger.info("Shutting down API service.")


app = FastAPI(
    title="Voice AI Patient Registration API",
    description="REST API backend for Vapi Voice Agent patient registration system.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for cross-origin requests (Vapi / web UI dashboard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(patients.router)
app.include_router(vapi.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "data": {
            "name": "Voice AI Patient Registration API",
            "status": "online",
            "version": "1.0.0",
            "documentation": "/docs"
        },
        "error": None
    }


# Exception Handlers to enforce consistent JSON envelope: { "data": null, "error": ... }

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    formatted_errors = []
    for err in errors:
        field = " -> ".join([str(loc) for loc in err.get("loc", []) if loc != "body"])
        msg = err.get("msg", "Invalid field")
        formatted_errors.append({"field": field, "message": msg})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "data": None,
            "error": {
                "message": "Validation failed for request body or parameters.",
                "code": 422,
                "details": formatted_errors
            }
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "data": None,
            "error": {
                "message": exc.detail,
                "code": exc.status_code
            }
        }
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "data": None,
            "error": {
                "message": "An internal server error occurred.",
                "code": 500,
                "details": str(exc)
            }
        }
    )
