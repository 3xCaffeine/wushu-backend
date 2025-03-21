from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import athlete, auth, institute, endorse, tournament

def create_app() -> FastAPI:
    app = FastAPI(
        title="WUSHU Backend API",
        description="Routes for various functionalities of wushu backend",
        version="0.0.1",
        terms_of_service="https://github.com/3xCaffeine/wushu-backend",
        license_info={
            "name": "Apache 2.0",
            "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
        },
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"], summary="Check API health status")
    async def health():
        return {"health": "ok"}

    app.include_router(auth.router)
    app.include_router(athlete.router)
    app.include_router(athlete.router)
    app.include_router(institute.router)
    app.include_router(tournament.router)
    app.include_router(endorse.router)


    return app