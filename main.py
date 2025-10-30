import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import start_http_server
from pymongo.errors import PyMongoError
import uvicorn

from config.changeStream import watch_changes
from config.db import handle_database_error
from config.settings import SettingsError, get_settings
from routes.download_routes import router as donwload_router
from routes.filter_routes import router as filter_router
from routes.follow_routes import router as follow_router
from routes.interactions_routes import router as interactions_router

from routes.lyrics_routes import router as lyrics_routes
from routes.mail_routes import router as mail_router
from routes.posts_routes import router as posts_router
from routes.users_routes import router as users_router
from routes.routes import router as routes_router
from routes.search_routes import router as search_router

try:
    settings = get_settings()
except SettingsError as exc:
    raise RuntimeError("Failed to load application settings") from exc

# Iniciar la aplicación
app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir los routers
app.include_router(users_router, prefix="/v1/api/users")
app.include_router(posts_router, prefix="/v1/api/posts")
app.include_router(interactions_router, prefix="/v1/api/interactions")
app.include_router(lyrics_routes, prefix="/v1/api/lyrics")
app.include_router(follow_router, prefix="/v1/api/follows")
app.include_router(search_router, prefix="/v1/api/search")
app.include_router(filter_router, prefix="/v1/api/filter")
app.include_router(mail_router, prefix="/v1/api/mail")
app.include_router(donwload_router, prefix="/v1/api/download")
app.include_router(routes_router)
# Manejador de excepciones global para errores de base de datos
app.add_exception_handler(PyMongoError, handle_database_error)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(watch_changes())

def main():
    # Iniciar el servidor de Prometheus
    start_http_server(settings.prometheus_port)

    # Iniciar el servidor de FastAPI
    uvicorn.run(app, host=settings.app_host, port=settings.app_port)


if __name__ == "__main__":
    # Iniciar la aplicación
    main()
