import os
import threading
from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import traceback


from openai import OpenAI

from dotenv import load_dotenv

from backend.llm_user.llm_user import init_llm_user
from backend.routes import auth, chat, mcp

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Error handling middleware
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except HTTPException as http_exc:
        # Log the exception details
        logger.error(f"HTTP Exception: {http_exc.status_code} - {http_exc.detail}")
        # Re-raise the exception to let FastAPI handle it
        raise http_exc
    except Exception as e:
        # Log the full error with traceback for unexpected errors
        logger.error(f"Error occurred: {str(e)}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error occurred"},
        )


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the authentication router
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

# Include the chat router
app.include_router(chat.router, prefix="/api/chat_room", tags=["chat"])


app.include_router(mcp.router, prefix="/api/mcp", tags=["mcp"])


@app.on_event("startup")
async def startup_event():
    print("startup_event")
    init_llm_user()


if __name__ == "__main__":

    import uvicorn

    # Configure uvicorn server with proper cleanup
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=14000,
        loop="asyncio",
        reload=True,
        timeout_keep_alive=30,
        timeout_graceful_shutdown=10,
    )

    server = uvicorn.Server(config)
    server.run()
