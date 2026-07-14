from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path

app = FastAPI()

TEMPLATES_DIR = Path(__file__).resolve().parent / 'templates'


@app.get('/ui', response_class=HTMLResponse)
async def ui_home() -> HTMLResponse:
    return HTMLResponse((TEMPLATES_DIR / 'index.html').read_text(encoding='utf-8'))


@app.get('/ui/chat', response_class=HTMLResponse)
async def ui_chat() -> HTMLResponse:
    return HTMLResponse((TEMPLATES_DIR / 'chat.html').read_text(encoding='utf-8'))


@app.get('/ui/dashboard', response_class=HTMLResponse)
async def ui_dashboard() -> HTMLResponse:
    return HTMLResponse((TEMPLATES_DIR / 'dashboard.html').read_text(encoding='utf-8'))
