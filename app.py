from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import api_process, api_chat

# This is the main application instance
app = FastAPI()

# Include routers from the routes package
app.include_router(api_process.router)
app.include_router(api_chat.router)

# Add CORS middleware to allow all origins
# This is the same configuration from your original app_ui.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Local PDF Assistant API"}