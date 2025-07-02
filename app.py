# app.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import api_process, api_chat, api_status # Import api_status

# This is the main application instance
app = FastAPI()

# Include routers from the routes package
app.include_router(api_process.router)
app.include_router(api_chat.router)
app.include_router(api_status.router) # Include the new status router

# ... rest of the file is unchanged ...

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