import os
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create the app
app = FastAPI(title="SEBI Vidyalaya", version="1.0.0")

# Configure static files first
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure templates with Flask-like functions
def url_for(name: str, **params):
    if name == "static":
        return f"/static/{params.get('filename', '')}"
    if name == "landing":
        return "/"
    return f"/{name}"

def get_flashed_messages(with_categories=False):
    # Mock Flask's flash messages for compatibility
    return []

templates = Jinja2Templates(directory="templates")
templates.env.globals["url_for"] = url_for
templates.env.globals["get_flashed_messages"] = get_flashed_messages

# Configure upload settings  
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max file size
UPLOAD_FOLDER = 'uploads'

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Import routes to register them
import routes

if __name__ == '__main__':
    uvicorn.run("app:app", host='0.0.0.0', port=8080, reload=True)