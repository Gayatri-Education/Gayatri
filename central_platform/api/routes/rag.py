"""Gayatri AI Platform — Plug-and-Play RAG Knowledge API Endpoints (Phase 16).

Provides end-to-end REST endpoints for knowledge source attachment,
multi-format ingestion, validation, publishing, and grounded scoped retrieval.
"""
from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from central_platform.api.schemas import (
    ApiResponse,
    RAGChunkResponse,
    RAGIngestRequest,
    RAGIngestResponse,
    RAGPublishResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGResultItem,
    RAGSourceCreateRequest,
    RAGSourceResponse,
    RAGValidateResponse,
)
from central_platform.auth.dependencies import get_db
from central_platform.rag.service import RAGService

router = APIRouter(prefix="/rag", tags=["RAG"])


def get_rag_service() -> RAGService:
    db = get_db()
    return RAGService(db=db)


@router.post("/sources", response_model=ApiResponse[RAGSourceResponse], status_code=status.HTTP_201_CREATED)
async def create_rag_source(req: RAGSourceCreateRequest):
    """Register a new plug-and-play knowledge source for a course."""
    svc = get_rag_service()
    try:
        source = svc.register_source(
            organization_id="org-default",
            course_id=req.course_id,
            subject=req.subject,
            title=req.title,
            source_type=req.source_type,
            authority=req.authority,
            version=req.version,
            metadata=req.metadata,
        )
        return ApiResponse(
            ok=True,
            data=RAGSourceResponse(
                id=source.id,
                organization_id=source.organization_id,
                course_id=source.course_id,
                subject=source.subject,
                title=source.title,
                source_type=source.source_type,
                authority=source.authority,
                version=source.version,
                status=source.status,
                checksum=source.checksum,
                chunk_count=source.chunk_count,
                created_at=source.created_at,
                updated_at=source.updated_at,
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/sources", response_model=ApiResponse[List[RAGSourceResponse]])
async def list_rag_sources(
    course_id: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    authority: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List knowledge sources with optional course, subject, status, or authority filters."""
    svc = get_rag_service()
    sources = svc.db.list_rag_sources(
        course_id=course_id,
        subject=subject,
        status=status,
        authority=authority,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(
        ok=True,
        data=[
            RAGSourceResponse(
                id=s.id,
                organization_id=s.organization_id,
                course_id=s.course_id,
                subject=s.subject,
                title=s.title,
                source_type=s.source_type,
                authority=s.authority,
                version=s.version,
                status=s.status,
                checksum=s.checksum,
                chunk_count=s.chunk_count,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in sources
        ],
    )


@router.get("/sources/{source_id}", response_model=ApiResponse[RAGSourceResponse])
async def get_rag_source(source_id: str):
    """Get details for a specific knowledge source."""
    svc = get_rag_service()
    source = svc.db.get_rag_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Knowledge source '{source_id}' not found.")
    return ApiResponse(
        ok=True,
        data=RAGSourceResponse(
            id=source.id,
            organization_id=source.organization_id,
            course_id=source.course_id,
            subject=source.subject,
            title=source.title,
            source_type=source.source_type,
            authority=source.authority,
            version=source.version,
            status=source.status,
            checksum=source.checksum,
            chunk_count=source.chunk_count,
            created_at=source.created_at,
            updated_at=source.updated_at,
        ),
    )


@router.post("/sources/{source_id}/ingest", response_model=ApiResponse[RAGIngestResponse])
async def ingest_source_content(source_id: str, req: RAGIngestRequest):
    """Parse, clean, chunk, and index content into the specified knowledge source."""
    svc = get_rag_service()
    try:
        res = svc.ingest_document(
            source_id=source_id,
            content=req.content,
            file_name=req.file_name,
            override_source_type=req.override_source_type,
        )
        return ApiResponse(
            ok=True,
            data=RAGIngestResponse(
                source_id=res["source_id"],
                status=res["status"],
                sections_parsed=res["sections_parsed"],
                chunks_created=res["chunks_created"],
                checksum=res["checksum"],
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}")


@router.post("/sources/{source_id}/validate", response_model=ApiResponse[RAGValidateResponse])
async def validate_rag_source(source_id: str):
    """Validate ingested chunks, verify lengths, and check prompt injection safety."""
    svc = get_rag_service()
    try:
        res = svc.validate_source(source_id)
        return ApiResponse(
            ok=True,
            data=RAGValidateResponse(
                valid=res["valid"],
                source_id=res["source_id"],
                status=res["status"],
                chunk_count=res["chunk_count"],
                average_chunk_chars=res["average_chunk_chars"],
                concepts_covered=res["concepts_covered"],
                errors=res["errors"],
                warnings=res["warnings"],
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/sources/{source_id}/publish", response_model=ApiResponse[RAGPublishResponse])
async def publish_rag_source(source_id: str):
    """Publish a validated knowledge source, making its chunks available for live retrieval."""
    svc = get_rag_service()
    try:
        source = svc.publish_source(source_id)
        return ApiResponse(
            ok=True,
            data=RAGPublishResponse(
                source_id=source.id,
                status=source.status,
                updated_at=source.updated_at,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/sources/{source_id}/chunks", response_model=ApiResponse[List[RAGChunkResponse]])
async def get_source_chunks(
    source_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List chunks belonging to a knowledge source."""
    svc = get_rag_service()
    chunks = svc.db.get_rag_chunks(source_id, limit=limit, offset=offset)
    return ApiResponse(
        ok=True,
        data=[
            RAGChunkResponse(
                id=c.id,
                source_id=c.source_id,
                course_id=c.course_id,
                subject=c.subject,
                chapter=c.chapter,
                topic=c.topic,
                concept=c.concept,
                difficulty=c.difficulty,
                page=c.page,
                section=c.section,
                content_type=c.content_type,
                text=c.text,
                clean_text=c.clean_text,
                provenance_type=c.provenance_type,
                created_at=c.created_at,
            )
            for c in chunks
        ],
    )


@router.delete("/sources/{source_id}", response_model=ApiResponse[dict])
async def delete_rag_source(source_id: str):
    """Delete a knowledge source and all its associated chunks."""
    svc = get_rag_service()
    deleted = svc.db.delete_rag_source(source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Knowledge source '{source_id}' not found.")
    return ApiResponse(ok=True, data={"deleted": True, "source_id": source_id})


@router.post("/query", response_model=ApiResponse[RAGQueryResponse])
async def query_rag(req: RAGQueryRequest):
    """Retrieve grounded knowledge evidence cards scoped to course, subject, and concepts."""
    svc = get_rag_service()
    try:
        res = svc.query(
            query_text=req.query,
            course_id=req.course_id,
            subject=req.subject,
            concept=req.concept_id,
            top_k=req.top_k,
            confidence_threshold=req.confidence_threshold,
        )
        return ApiResponse(
            ok=True,
            data=RAGQueryResponse(
                status=res["status"],
                query=res["query"],
                results=[
                    RAGResultItem(
                        chunk_id=r["chunk_id"],
                        source_id=r.get("source_id"),
                        chapter=r["chapter"],
                        topic=r["topic"],
                        concept=r.get("concept"),
                        page=r["page"],
                        text=r["text"],
                        score=r["score"],
                        citation=r["citation"],
                    )
                    for r in res["results"]
                ],
                count=res["count"],
                data_context=res.get("data_context"),
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RAG query execution failed: {exc}")
