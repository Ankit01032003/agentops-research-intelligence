
import logging
from contextlib import asynccontextmanager
from pathlib import PurePosixPath

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.concurrency import run_in_threadpool

from app.config import settings
from app.schemas import ResearchRequest, ResearchResponse, IngestResponse
from app.retrieval import ingest_document
from app.workflow import run_research
from app.history import init_history_db, save_run, list_runs, get_run


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("agentops")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_in_threadpool(init_history_db)
    logger.info("Application started")
    yield
    logger.info("Application stopped")


app = FastAPI(
    title="AgentOps Research Intelligence",
    description=(
        "Agentic research with web search, document RAG, evidence review, "
        "report generation, evaluation, and saved research history."
    ),
    version="1.2.0",
    lifespan=lifespan,
)


@app.get("/")
def home():
    return {
        "project": "AgentOps Research Intelligence",
        "version": "1.2.0",
        "docs": "/docs",
        "health": "/health",
        "research_history": "/runs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="Configure OPENAI_API_KEY in .env first.",
        )

    try:
        result = await run_in_threadpool(
            run_research, request.question
        )
        await run_in_threadpool(save_run, result)
        logger.info("Research completed run_id=%s", result["run_id"])
        return result

    except Exception as exc:
        logger.exception("Research workflow failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=500,
            detail="Research failed. Check server logs.",
        ) from exc


@app.post("/documents", response_model=IngestResponse)
async def upload_document(file: UploadFile = File(...)):
    allowed_extensions = {".pdf", ".txt", ".md"}
    raw_filename = (file.filename or "upload.txt").replace("\\", "/")
    filename = PurePosixPath(raw_filename).name[:255]
    suffix = PurePosixPath(filename).suffix.lower()

    if not filename or suffix not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, TXT, and MD files are supported.",
        )

    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="Configure OPENAI_API_KEY in .env first.",
        )

    try:
        content = await file.read(10 * 1024 * 1024 + 1)

        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="Maximum upload size is 10 MB.",
            )

        if not content:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty.",
            )

        count = await run_in_threadpool(
            ingest_document, filename, content
        )

        logger.info(
            "Document indexed filename=%s chunks=%d", filename, count
        )
        return IngestResponse(
            filename=filename,
            chunks_added=count,
            status="indexed",
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "Document ingestion failed: %s", type(exc).__name__
        )
        raise HTTPException(
            status_code=500,
            detail="Document ingestion failed. Check server logs.",
        ) from exc
    finally:
        await file.close()


@app.get("/runs")
def research_runs(limit: int = Query(default=20, ge=1, le=100)):
    try:
        return {"runs": list_runs(limit)}
    except Exception as exc:
        logger.exception("History listing failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve research history.",
        ) from exc


@app.get("/runs/{run_id}")
def research_run_detail(run_id: str):
    try:
        result = get_run(run_id)
        if result is None:
            raise HTTPException(
                status_code=404, detail="Research run not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "History retrieval failed: %s", type(exc).__name__
        )
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve the research run.",
        ) from exc
