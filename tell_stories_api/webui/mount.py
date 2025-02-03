from fastapi import FastAPI
from gradio.routes import mount_gradio_app
from tell_stories_api.webui.interface import create_gradio_app
import os
from dotenv import load_dotenv
load_dotenv()

def mount_webui(app: FastAPI, path: str = "/") -> None:
    """Mount the Gradio interface at the specified path in the FastAPI app"""
    host = os.getenv("TELLSTORIESAI_HOST")
    port = os.getenv("TELLSTORIESAI_PORT")
    api_base_url = f'http://{host}:{port}/api'
    blocks = create_gradio_app(api_base_url=api_base_url)
    mount_gradio_app(app, blocks, path=path) 