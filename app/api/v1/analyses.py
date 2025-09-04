"""
Analysis API endpoints for palm reading functionality.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request, Query, status
from app.schemas.analysis import (
    AnalysisResponse, 
    AnalysisStatusResponse, 
    AnalysisListResponse,
    AnalysisSummaryResponse
)
from app.services.analysis_service import AnalysisService
from app.models.analysis import AnalysisStatus
from app.models.user import User
from app.dependencies.auth import get_current_user, get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post("/", response_model=AnalysisResponse)
async def create_analysis(
    left_image: Optional[UploadFile] = File(None),
    right_image: Optional[UploadFile] = File(None),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> AnalysisResponse:
    """Create new palm analysis (up to 2 images).
    
    Accepts multipart form data with optional left_image and right_image files.
    At least one image is required. Analysis can be created anonymously or by logged-in users.
    """
    try:
        # Validate at least one image is provided
        if not left_image and not right_image:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one palm image is required"
            )
        
        analysis_service = AnalysisService()
        
        # Create analysis record and save images
        analysis = await analysis_service.create_analysis(
            user_id=current_user.id if current_user else None,
            left_image=left_image,
            right_image=right_image
        )
        
        logger.info(f"Created analysis {analysis.id} for user {current_user.id if current_user else 'anonymous'}")
        
        return AnalysisResponse.model_validate(analysis)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create analysis"
        )


@router.get("/{analysis_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(analysis_id: int) -> AnalysisStatusResponse:
    """Get current status of analysis job for polling.
    
    This endpoint can be used by the frontend to poll for analysis progress.
    It's available to both authenticated and anonymous users.
    """
    try:
        analysis_service = AnalysisService()
        analysis = await analysis_service.get_analysis_status(analysis_id)
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        # Calculate progress percentage
        progress_map = {
            AnalysisStatus.QUEUED: 10,
            AnalysisStatus.PROCESSING: 50,
            AnalysisStatus.COMPLETED: 100,
            AnalysisStatus.FAILED: 0
        }
        progress = progress_map.get(analysis.status, 0)
        
        # Generate human-readable message
        message_map = {
            AnalysisStatus.QUEUED: "Analysis is queued for processing",
            AnalysisStatus.PROCESSING: "Analyzing palm images...",
            AnalysisStatus.COMPLETED: "Analysis completed successfully",
            AnalysisStatus.FAILED: "Analysis failed"
        }
        message = message_map.get(analysis.status, "Unknown status")
        
        # Include analysis result when completed for frontend redirection
        result = None
        if analysis.status == AnalysisStatus.COMPLETED and analysis.summary:
            result = {
                "analysis_id": analysis.id,
                "summary": analysis.summary,
                "status": analysis.status.value
            }
        
        return AnalysisStatusResponse(
            analysis_id=analysis.id,
            status=analysis.status.value,
            progress=progress,
            error_message=analysis.error_message,
            message=message,
            result=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis status {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analysis status"
        )


@router.get("/{analysis_id}/summary", response_model=AnalysisSummaryResponse)
async def get_analysis_summary(analysis_id: int) -> AnalysisSummaryResponse:
    """Get analysis summary (available without authentication).
    
    Returns the summary portion of the analysis which is available to anonymous users.
    Full reports require authentication.
    """
    try:
        analysis_service = AnalysisService()
        analysis = await analysis_service.get_analysis_by_id(analysis_id)
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        return AnalysisSummaryResponse(
            analysis_id=analysis.id,
            summary=analysis.summary,
            status=analysis.status.value,
            created_at=analysis.created_at.isoformat(),
            requires_login=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis summary {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analysis summary"
        )


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user)
) -> AnalysisResponse:
    """Get full analysis details (requires authentication).
    
    Returns complete analysis including the full report, which is only available
    to authenticated users who own the analysis.
    """
    try:
        analysis_service = AnalysisService()
        analysis = await analysis_service.get_analysis_by_id(analysis_id)
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        # Check if user owns this analysis or if it's anonymous and user is authenticated
        if analysis.user_id and analysis.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this analysis"
            )
        
        return AnalysisResponse.model_validate(analysis)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analysis"
        )


@router.get("/", response_model=AnalysisListResponse)
async def list_user_analyses(
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(5, ge=1, le=20, description="Items per page")
) -> AnalysisListResponse:
    """List analyses for the current user with pagination.
    
    Returns analyses ordered by creation date (most recent first).
    """
    try:
        analysis_service = AnalysisService()
        analyses, total = await analysis_service.get_user_analyses(
            user_id=current_user.id,
            page=page,
            per_page=per_page
        )
        
        analysis_responses = [AnalysisResponse.model_validate(a) for a in analyses]
        
        has_more = page * per_page < total
        
        return AnalysisListResponse(
            analyses=analysis_responses,
            total=total,
            page=page,
            per_page=per_page,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Error listing analyses for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list analyses"
        )


@router.delete("/{analysis_id}")
async def delete_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user)
) -> dict:
    """Delete an analysis and all associated data.
    
    Only the owner of the analysis can delete it. This will remove the analysis,
    all associated images, conversations, and messages.
    """
    try:
        analysis_service = AnalysisService()
        success = await analysis_service.delete_analysis(
            analysis_id=analysis_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found or you don't have permission to delete it"
            )
        
        return {"message": "Analysis deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete analysis"
        )
