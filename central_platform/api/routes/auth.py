"""Gayatri AI Platform — Auth API Endpoints (Phase 02)."""
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, Header, HTTPException, status
from central_platform.api.schemas import ApiResponse, LoginRequest, LoginResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

MOCK_USERS = {
    "admin": {"user_id": "usr-admin-01", "role": "SUPER_ADMIN", "org": "org-central"},
    "teacher_1": {"user_id": "usr-teacher-01", "role": "TEACHER", "org": "org-central"},
    "student_001": {"user_id": "usr-student-01", "role": "STUDENT", "org": "org-central"},
}


@router.post("/login", response_model=ApiResponse[LoginResponse])
async def login(req: LoginRequest):
    """Authenticate user and return session token."""
    user = MOCK_USERS.get(req.username)
    if not user and req.password != "password":
        # Check fallback
        if len(req.password) < 4:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        user = {"user_id": f"usr-{req.username}", "role": "STUDENT", "org": "org-default"}

    token = f"gayatri_tok_{uuid.uuid4().hex}"
    data = LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=3600,
        user_id=user["user_id"],
        username=req.username,
        role=user["role"],
        organization_id=user["org"],
    )
    return ApiResponse(ok=True, data=data)


@router.post("/logout", response_model=ApiResponse[dict])
async def logout(authorization: str = Header(default="")):
    """Log out current user and invalidate session."""
    return ApiResponse(ok=True, data={"logged_out": True})


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_current_user(authorization: str = Header(default="")):
    """Get current authenticated user profile."""
    data = UserResponse(
        user_id="usr-current-01",
        username="active_user",
        email="user@gayatri.ai",
        role="TEACHER",
        organization_id="org-central",
        is_active=True,
    )
    return ApiResponse(ok=True, data=data)


@router.post("/refresh", response_model=ApiResponse[dict])
async def refresh_token(authorization: str = Header(default="")):
    """Refresh session token."""
    new_token = f"gayatri_tok_{uuid.uuid4().hex}"
    return ApiResponse(ok=True, data={"access_token": new_token, "expires_in": 3600})
