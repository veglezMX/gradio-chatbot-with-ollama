"""
FastAPI application factory with health checks.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Ollama Chat API",
        description="Chat interface for Ollama models",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routes
    from .routes import cookies, health
    app.include_router(cookies.router)
    app.include_router(health.router)
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Ollama Chat API",
            "docs": "/docs",
            "chat": "/gradio"
        }
    
    return app