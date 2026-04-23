import asyncio
import sys

# Windows: psycopg requires SelectorEventLoop, not ProactorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
import logging
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as v1_router
from app.api.middleware import RequestLoggingMiddleware
from app.agents.graph.graph import AgentGraph
from app.core.config import setting
from app.utils.logging import setup_logging
from app.db.engine import get_app_engine, get_checkpoint_engine
from app.services.chat_service import ChatService
from app.services.memory_service import MemoryService
from app.services.read_graph import GraphRunner
from app.core.prompt_loader import PromptManager
from app.core.llm_provider import get_llm

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("startup_begin")
    print("======= in lifespan ========")
    
    llm = get_llm(agent_name="startup", user_id="system")

    prompt_manager = PromptManager()

    agent_graph = await AgentGraph.create(
        llm=llm,
        prompt_manager=prompt_manager,
    )
    
    app.state.agent_graph = agent_graph
    logger.info("agent_graph_ready")

    app.state.redis = aioredis.from_url(
        setting.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    logger.info("redis_ready")

    memory_service = MemoryService()
    app.state.chat_service = ChatService(
        graph_runner=GraphRunner(graph=agent_graph),
        memory_service=memory_service,
    )
    logger.info("services_ready")

    logger.info("startup_complete")
    yield

    logger.info("shutdown_begin")
    await app.state.redis.aclose()
    await get_app_engine().dispose()
    await get_checkpoint_engine().dispose()
    logger.info("shutdown_complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Bravous MultiAgent API",
        version="1.0.0",
        docs_url="/docs" if setting.DEBUG else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    # ── Middleware — outermost first ────────────────────────────────
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in setting.ALLOWED_ORIGINS.split(",") if o.strip()] or ["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )

    # ── Routes ──────────────────────────────────────────────────────
    app.include_router(v1_router, prefix="/api/v1")

    return app


app = create_app()