"""
CopadoCon 2025 Hackathon - Intelligent Salesforce Monitor

This is the main FastAPI server that brings everything together. Think of it as the control center
that coordinates our AI agent, serves the dashboard, and handles real-time WebSocket connections.
The goal is simple: catch Salesforce issues before they become problems and fix them automatically.
"""

import asyncio
import os
import sys
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from loguru import logger

from src.core.agent import ObservabilityAgent
from src.api.routes import router, set_agent
from src.core.config import settings

# Load environment variables from .env file (for API keys, database URLs, etc.)
load_dotenv()

# Global reference to our AI agent - this handles all the intelligent monitoring and analysis
agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application lifecycle - startup and shutdown procedures.
    This runs when the server starts and stops, handling initialization and cleanup.
    """
    # Configure logging to keep console output clean (only show errors)
    import logging
    
    # Set up minimal logging - we only want to see actual problems
    logging.getLogger().setLevel(logging.ERROR)
    logging.basicConfig(level=logging.ERROR, force=True)
    
    # Configure our custom logger (loguru) to match the minimal approach
    logger.remove()  # Clear any existing log handlers
    logger.add(
        sys.stderr,
        level="ERROR",
        format="<red>{time:YYYY-MM-DD HH:mm:ss.SSS}</red> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # Initialize our main AI agent that does all the monitoring and analysis
    global agent
    agent = ObservabilityAgent()
    set_agent(agent)  # Make it available to our API endpoints
    await agent.start()
    print("Application started - monitoring Salesforce for issues")
    
    yield  # This is where the application actually runs
    
    # Clean shutdown - stop the agent gracefully to avoid any hanging processes
    if agent:
        await agent.stop()
    print("Application stopped")

# Create our FastAPI application - this is the web server that handles everything
app = FastAPI(
    title="CopadoCon 2025 Hackathon - Intelligent Salesforce Monitor", 
    description="AI-powered system that watches your Salesforce org and fixes problems automatically",
    version="1.0.0",
    docs_url="/docs",  # Interactive API documentation
    redoc_url="/redoc",  # Alternative API docs
    lifespan=lifespan
)

# Wire up our API endpoints (these handle data requests from the dashboard)
app.include_router(router, prefix="/api")

# Make static files available (HTML, CSS, JavaScript, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_dashboard():
    """
    Serves the main dashboard when someone visits the website.
    This is the beautiful real-time monitoring interface that shows incidents,
    charts, and system status all in one place.
    """
    with open("static/index.html") as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Real-time data pipeline for the dashboard.
    
    When someone opens the dashboard, this WebSocket keeps pushing fresh data every 5 seconds.
    Think of it like a live news feed - incidents, metrics, and system status all update 
    automatically without the user having to refresh the page.
    """
    await websocket.accept()
    try:
        while True:
            # First, make sure the connection is still good
            if websocket.client_state.name != "CONNECTED":
                break
                
            # Start with safe defaults in case something goes wrong
            data_to_send = {"incidents": [], "metrics": {}}
            
            # Try to get fresh data from our monitoring agent
            if agent:
                try:
                    status = await agent.get_status()
                    if status:
                        data_to_send = status
                except Exception as status_error:
                    logger.error(f"Couldn't get agent status: {status_error}")
            
            # Send the data, but only if the connection is still active
            try:
                if websocket.client_state.name == "CONNECTED":
                    await websocket.send_json(data_to_send)
            except Exception as send_error:
                logger.debug(f"WebSocket send failed: {send_error}")
                break
                
            # Wait 5 seconds before the next update
            await asyncio.sleep(5)
            
    except Exception as e:
        logger.debug(f"WebSocket connection ended: {e}")
    finally:
        # Clean up the connection safely
        try:
            if websocket.client_state.name == "CONNECTED":
                await websocket.close()
        except:
            pass

if __name__ == "__main__":
    # When running directly (not imported), start the web server
    # This is where everything begins when you run "python main.py"
    
    import logging
    from loguru import logger
    
    # Keep the console clean by only showing error messages
    logging.basicConfig(level=logging.ERROR)
    logging.getLogger().setLevel(logging.ERROR)
    
    # Set up our logger to match - we only want to see actual problems
    logger.remove()  # Clear any default handlers
    logger.add(
        sys.stderr,
        level="ERROR",
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # Fire up the web server
    # In development mode, it will automatically restart when you change code
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="warning",
        access_log=False  # Skip HTTP request logs to keep things clean
    )
