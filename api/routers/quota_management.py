from fastapi import APIRouter, Depends
from ..dependencies import get_current_user
import logging
import sys
import os

# Add the parent directory to the Python path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.hunter_quota_manager import hunter_quota_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["quota-management"])

@router.get("/hunter/quota-status")
async def get_hunter_quota_status(current_user: dict = Depends(get_current_user)):
    """Get current Hunter.io quota status and usage statistics"""
    try:
        status = hunter_quota_manager.get_quota_status()
        return {
            "success": True,
            "quota_status": status,
            "recommendations": _get_quota_recommendations(status)
        }
    except Exception as e:
        logger.error(f"Error getting Hunter.io quota status: {e}")
        return {"success": False, "error": str(e)}

@router.post("/hunter/reset-quota")
async def reset_hunter_quota(current_user: dict = Depends(get_current_user)):
    """Reset Hunter.io quota tracking (admin only)"""
    try:
        # Only allow admin users to reset quota
        if current_user.get("role") != "admin":
            return {"success": False, "error": "Admin access required"}
        
        hunter_quota_manager.quota_data["daily_usage"] = 0
        hunter_quota_manager.quota_data["monthly_usage"] = 0
        hunter_quota_manager.quota_data["requests_today"] = []
        hunter_quota_manager.save_quota_data()
        
        return {"success": True, "message": "Hunter.io quota reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting Hunter.io quota: {e}")
        return {"success": False, "error": str(e)}

@router.get("/hunter/optimized-limits")
async def get_optimized_limits(current_user: dict = Depends(get_current_user)):
    """Get current optimized limits based on quota status"""
    try:
        limits = hunter_quota_manager.get_optimized_limits()
        status = hunter_quota_manager.get_quota_status()
        
        return {
            "success": True,
            "optimized_limits": limits,
            "quota_remaining": status["daily_remaining"],
            "recommendation": _get_batch_recommendation(status)
        }
    except Exception as e:
        logger.error(f"Error getting optimized limits: {e}")
        return {"success": False, "error": str(e)}

def _get_quota_recommendations(status):
    """Get recommendations based on current quota usage"""
    remaining = status["daily_remaining"]
    efficiency = status["efficiency_stats"].get("success_rate", 0)
    
    recommendations = []
    
    if remaining < 50:
        recommendations.append("⚠️ Low quota remaining. Consider running smaller batches.")
    elif remaining < 100:
        recommendations.append("📊 Moderate quota remaining. Run medium-sized batches.")
    else:
        recommendations.append("✅ Good quota remaining. You can run full batches.")
    
    if efficiency < 50:
        recommendations.append("🎯 Low success rate. Consider improving company filtering.")
    elif efficiency > 80:
        recommendations.append("🏆 Excellent success rate! Current strategy is working well.")
    
    return recommendations

def _get_batch_recommendation(status):
    """Get recommended batch size based on quota"""
    remaining = status["daily_remaining"]
    
    if remaining > 200:
        return "You can run large batches (40-50 contacts)"
    elif remaining > 100:
        return "Run medium batches (25-30 contacts)"
    elif remaining > 50:
        return "Run small batches (15-20 contacts)"
    else:
        return "Run minimal batches (5-10 contacts) or wait for quota reset"
