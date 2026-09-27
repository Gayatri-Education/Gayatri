"""Gayatri AI Platform — Users API Endpoints (Phase 02)."""
from __future__ import annotations

import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from central_platform.api.schemas import ApiResponse, UserCreateRequest, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])

_USERS_STORE = [
    UserResponse(
        user_id="usr-admin-01",
        username="admin",
        email="admin@gayatri.ai",
        role="SUPER_ADMIN",
        organization_id="org-central",
        is_active=True,
    ),
    UserResponse(
        user_id="usr-teacher-01",
        username="teacher_sharma",
        email="sharma@gayatri.ai",
        role="TEACHER",
        organization_id="org-central",
        is_active=True,
    ),
    UserResponse(
        user_id="usr-student-01",
        username="student_001",
        email="student01@gayatri.ai",
        role="STUDENT",
        organization_id="org-central",
        is_active=True,
    ),
]


@router.get("", response_model=ApiResponse[List[UserResponse]])
async def list_users(
    role: Optional[str] = Query(default=None),
    organization_id: Optional[str] = Query(default=None),
):
    """List platform users with optional role or org filtering."""
    results = _USERS_STORE
    if role:
        results = [u for u in results if u.role.upper() == role.upper()]
    if organization_id:
        results = [u for u in results if u.organization_id == organization_id]
    return ApiResponse(ok=True, data=results)


@router.post("", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def create_user(req: UserCreateRequest):
    """Create a new platform user."""
    new_user = UserResponse(
        user_id=f"usr-{uuid.uuid4().hex[:8]}",
        username=req.username,
        email=req.email,
        role=req.role.upper(),
        organization_id=req.organization_id,
        is_active=True,
    )
    _USERS_STORE.append(new_user)
    return ApiResponse(ok=True, data=new_user)


@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
async def get_user_by_id(user_id: str):
    """Get user by unique ID."""
    for u in _USERS_STORE:
        if u.user_id == user_id:
            return ApiResponse(ok=True, data=u)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
