from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from ai.ingest import ingest_excel
from ai.rag import answer_question
from ai.streaming import stream_answer

router = APIRouter(prefix="/api/ai")

# Request model for /ingest route
class IngestRequest(BaseModel):
    file_path: str

# Response model for /ingest route
class IngestResponse(BaseModel):
    success: bool
    message: str

# Request model for /query route
class QueryRequest(BaseModel):
    session_id: str
    question: str

# Response model for /query route
class QueryResponse(BaseModel):
    answer: str
    citations: List[str]

# /ingest route
@router.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest):
    try:
        success, message = await ingest_excel(request.file_path)
        return IngestResponse(success=success, message=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# /query route
@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try:
        answer, citations = await answer_question(request.session_id, request.question)
        return QueryResponse(answer=answer, citations=citations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# /stream route
@router.get("/stream")
async def stream(query: str, session_id: str):
    try:
        stream_generator = stream_answer(query, session_id)
        return StreamingResponse(stream_generator, media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))