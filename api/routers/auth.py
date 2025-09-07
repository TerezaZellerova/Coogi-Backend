from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from datetime import datetime
import logging

from ..models import LoginRequest, LoginResponse
from ..dependencies import TEST_USERS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

@router.options("/login")
async def login_options():
    """Handle CORS preflight for login"""
    return Response(status_code=200)

@router.options("/signup")
async def signup_options():
    """Handle CORS preflight for signup"""
    return Response(status_code=200)

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

@router.post("/signup", response_model=LoginResponse)
async def signup(request: LoginRequest):
    """Simple user registration for testing"""
    try:
        # Check if user already exists
        if request.email in TEST_USERS:
            return LoginResponse(
                success=False,
                message="User already exists"
            )
        
        # Basic validation
        if len(request.password) < 6:
            return LoginResponse(
                success=False,
                message="Password must be at least 6 characters long"
            )
        
        # Create new user (add to TEST_USERS dictionary)
        user_name = request.email.split('@')[0].replace('.', ' ').title()
        TEST_USERS[request.email] = {
            "password": request.password,
            "name": user_name,
            "role": "user"
        }
        
        # Generate token for immediate login
        token = f"test_token_{request.email.replace('@', '_').replace('.', '_')}"
        
        logger.info(f"New user registered: {request.email}")
        
        return LoginResponse(
            success=True,
            message="Account created successfully",
            token=token,
            user={
                "email": request.email,
                "name": user_name,
                "role": "user"
            }
        )
        
    except Exception as e:
        logger.error(f"Signup error: {e}")
        return LoginResponse(
            success=False,
            message="Registration failed"
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
