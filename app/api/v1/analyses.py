"""
Analysis API endpoints for palm reading functionality.
"""

import logging
import json
import asyncio
from typing import Optional, AsyncGenerator
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request, Query, status
from fastapi.responses import StreamingResponse
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
from app.core.redis import redis_service

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


@router.get("/{analysis_id}/stream-test")
async def test_stream_endpoint(analysis_id: int):
    """Simple test endpoint to verify route registration."""
    return {"message": f"Stream endpoint working for analysis {analysis_id}"}


@router.get("/{analysis_id}/stream")
async def stream_analysis_status(analysis_id: int) -> StreamingResponse:
    """Stream analysis status updates via Server-Sent Events.

    This endpoint provides real-time updates for analysis progress,
    eliminating the need for polling. Available to both authenticated
    and anonymous users.

    Returns SSE stream with analysis status updates.
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for analysis status updates via Redis pub/sub."""
        analysis_service = AnalysisService()

        # Check if analysis exists first
        analysis = await analysis_service.get_analysis_status(analysis_id)
        if not analysis:
            yield f"event: error\ndata: {json.dumps({'error': 'Analysis not found'})}\n\n"
            return

        # Send initial status
        yield f"event: status\ndata: {json.dumps(_format_analysis_status(analysis))}\n\n"

        # If analysis is already complete, close the stream
        if analysis.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]:
            yield f"event: close\ndata: {json.dumps({'message': 'Analysis finished'})}\n\n"
            return

        # Subscribe to Redis channel for this analysis
        channel = f"analysis_updates:{analysis_id}"
        pubsub = await redis_service.subscribe(channel)

        if not pubsub:
            # Fallback to polling if Redis pub/sub fails
            logger.warning(f"Redis pub/sub failed for analysis {analysis_id}, falling back to polling")
            yield f"event: info\ndata: {json.dumps({'message': 'Using fallback polling mode'})}\n\n"

            # Fallback polling logic
            max_duration = 300  # 5 minutes timeout
            elapsed = 0
            poll_interval = 3

            while elapsed < max_duration:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

                try:
                    updated_analysis = await analysis_service.get_analysis_status(analysis_id)
                    if not updated_analysis:
                        yield f"event: error\ndata: {json.dumps({'error': 'Analysis not found'})}\n\n"
                        break

                    # Send status update
                    yield f"event: status\ndata: {json.dumps(_format_analysis_status(updated_analysis))}\n\n"

                    # Check if analysis is complete
                    if updated_analysis.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]:
                        yield f"event: complete\ndata: {json.dumps(_format_analysis_status(updated_analysis))}\n\n"
                        break

                except Exception as e:
                    logger.error(f"Error polling analysis status {analysis_id}: {e}")
                    yield f"event: error\ndata: {json.dumps({'error': 'Failed to get status update'})}\n\n"
                    break
            return

        try:
            # Listen for Redis events with timeout
            timeout_seconds = 300  # 5 minutes timeout
            start_time = asyncio.get_event_loop().time()

            while True:
                current_time = asyncio.get_event_loop().time()
                if current_time - start_time > timeout_seconds:
                    yield f"event: timeout\ndata: {json.dumps({'message': 'Stream timeout reached'})}\n\n"
                    break

                try:
                    # Listen for messages with a timeout
                    message = await asyncio.wait_for(pubsub.get_message(ignore_subscribe_messages=True), timeout=5.0)

                    if message and message['type'] == 'message':
                        try:
                            event_data = json.loads(message['data'])
                            event_type = event_data.get('event', 'status_update')

                            # Forward the event to the client
                            yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"

                            # Close stream if analysis is complete or failed
                            if event_data.get('status') in ['completed', 'failed']:
                                yield f"event: close\ndata: {json.dumps({'message': 'Analysis finished'})}\n\n"
                                break

                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON in Redis message: {e}")
                            continue

                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f"event: heartbeat\ndata: {json.dumps({'timestamp': asyncio.get_event_loop().time()})}\n\n"
                    continue

        except Exception as e:
            logger.error(f"Error in Redis pub/sub for analysis {analysis_id}: {e}")
            yield f"event: error\ndata: {json.dumps({'error': 'Stream connection failed'})}\n\n"
        finally:
            # Clean up Redis subscription
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
            except Exception as e:
                logger.error(f"Error closing Redis subscription: {e}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",  # TODO: Restrict to your domain in production
            "Access-Control-Allow-Headers": "Cache-Control",
            "X-Accel-Buffering": "no"  # Disable nginx buffering for SSE
        }
    )


def _format_analysis_status(analysis) -> dict:
    """Format analysis status for SSE events."""
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

    # Include analysis result when completed
    result = None
    if analysis.status == AnalysisStatus.COMPLETED and analysis.summary:
        result = {
            "analysis_id": analysis.id,
            "summary": analysis.summary,
            "status": analysis.status.value
        }

    return {
        "analysis_id": analysis.id,
        "status": analysis.status.value,
        "progress": progress,
        "error_message": analysis.error_message,
        "message": message,
        "result": result,
        "timestamp": analysis.updated_at.isoformat() if hasattr(analysis, 'updated_at') and analysis.updated_at else None
    }


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
    """Get full analysis details with conversation mode (requires authentication).
    
    Returns complete analysis including the full report and conversation mode,
    which is only available to authenticated users who own the analysis.
    """
    try:
        analysis_service = AnalysisService()
        analysis, conversation = await analysis_service.get_analysis_with_conversation_mode(
            analysis_id, current_user.id
        )
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found or you don't have permission to access it"
            )
        
        return AnalysisResponse.from_analysis(analysis, conversation)
        
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


@router.put("/{analysis_id}/associate")
async def associate_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user)
) -> dict:
    """Associate an anonymous analysis with the authenticated user.
    
    This endpoint allows authenticated users to claim ownership of an anonymous analysis
    that was created before they logged in. The analysis must have user_id = null to be
    associable.
    """
    try:
        analysis_service = AnalysisService()
        success = await analysis_service.associate_analysis(
            analysis_id=analysis_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found or already associated with another user"
            )
        
        logger.info(f"Associated analysis {analysis_id} with user {current_user.id}")
        return {"message": "Analysis associated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error associating analysis {analysis_id} with user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to associate analysis"
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
