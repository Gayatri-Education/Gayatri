"""Gayatri AI Platform — Curricula API Endpoints (Phase 02)."""
from __future__ import annotations

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from central_platform.api.schemas import ApiResponse, CurriculumResponse

router = APIRouter(prefix="/curricula", tags=["Curricula"])
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@router.get("/{course_id}", response_model=ApiResponse[CurriculumResponse])
async def get_curriculum(course_id: str):
    """Retrieve full curriculum hierarchy, concepts, and DAG prerequisites."""
    curr_file = PROJECT_ROOT / "data" / "curriculum" / "chemistry" / "ncert_class11_12.json"
    if not curr_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum file not found")

    try:
        with open(curr_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        concepts = data.get("concepts", [])
        
        # Group into 4 canonical chapters based on concept ID prefix
        chapters_map = {
            "Thermodynamics": [c for c in concepts if "thermo" in c.get("id", "")],
            "Chemical Bonding": [c for c in concepts if "bond" in c.get("id", "")],
            "Coordination Chemistry": [c for c in concepts if "coord" in c.get("id", "")],
            "Periodic Trends & Inorganic": [c for c in concepts if "inorg" in c.get("id", "") or "periodic" in c.get("id", "")],
        }
        chapters = [
            {"chapter_name": k, "concepts": v, "concept_count": len(v)}
            for k, v in chapters_map.items()
        ]
        total_concepts = len(concepts)
        total_topics = len(chapters)

        res = CurriculumResponse(
            course_id=course_id,
            chapters=chapters,
            total_topics=total_topics,
            total_concepts=total_concepts,
        )
        return ApiResponse(ok=True, data=res)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
