import uvicorn
from backend.app.main import app

if __name__ == "__main__":
    # This app.py acts as the main entry point to start the FastAPI backend server
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
