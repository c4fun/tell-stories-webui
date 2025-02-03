from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tell_stories_api.routes import script, voice, book
from tell_stories_api.logs import logger
from tell_stories_api.webui import mount_webui
import uvicorn
import os
from dotenv import load_dotenv
load_dotenv()

def create_app() -> FastAPI:
    app = FastAPI()
    
    # Set all CORS enabled origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许所有域名
        allow_credentials=True,
        allow_methods=["*"],  # 允许所有方法
        allow_headers=["*"],  # 允许所有头
    )
    
    # Include routers
    app.include_router(script.router, prefix="/api/script", tags=["script"])
    app.include_router(voice.router, prefix="/api/voice", tags=["voice"])
    app.include_router(book.router, prefix="/api/book", tags=["book"])
    
    # Mount the Gradio interface
    mount_webui(app, path="/ui")
    
    return app

app = create_app()
logger.info("The FastAPI application has started!")

if __name__ == "__main__":
    uvicorn.run(app,
                host=os.getenv("TELLSTORIESAI_HOST"),
                port=int(os.getenv("TELLSTORIESAI_PORT")))