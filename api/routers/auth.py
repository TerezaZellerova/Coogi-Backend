from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging

from ..models import LoginRequest, LoginResponse
from ..dependencies import TEST_USERS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Simple authentication for testing"""
    try:
        user_data = TEST_USERS.get(request.email)
        
        if not user_data:
            return LoginResponse(
                success=False,
                message="User not found"
            )
        
        if user_data["password"] != request.password:
            return LoginResponse(
                success=False,
                message="Invalid password"
            )
        
        # Generate a simple token (in production, use proper JWT)
        token = f"test_token_{request.email.replace('@', '_').replace('.', '_')}"
        
        return LoginResponse(
            success=True,
            message="Login successful",
            token=token,
            user={
                "email": request.email,
                "name": user_data["name"],
                "role": user_data["role"]
            }
        )
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return LoginResponse(
            success=False,
            message="Login failed"
        )

@router.get("/users")
async def get_test_users():
    """Get list of test users for development"""
    return {
        "test_users": [
            {
                "email": email,
                "name": data["name"],
                "role": data["role"]
            }
            for email, data in TEST_USERS.items()
        ]
    }
