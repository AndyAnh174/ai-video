import os
import time
import logging
from django.conf import settings
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


def get_veo_client():
    """Get Veo client with API key"""
    try:
        api_key = os.getenv('VEO_API_KEY') or getattr(settings, 'VEO_API_KEY', None)
        if not api_key:
            error_msg = "VEO_API_KEY not found in environment variables or settings"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Initialize client with API key
        logger.debug("Initializing Veo client")
        client = genai.Client(api_key=api_key)
        return client
    
    except Exception as e:
        logger.error(f"Error initializing Veo client: {str(e)}", exc_info=True)
        raise


def generate_video(prompt: str, negative_prompt: str = None, aspect_ratio: str = "16:9", resolution: str = "720p", **kwargs) -> dict:
    """
    Gọi Veo API (veo-3.1-fast-generate-preview) để generate video
    
    Args:
        prompt: Prompt đã được fill data
        negative_prompt: Negative prompt (optional)
        aspect_ratio: Aspect ratio (default: "16:9", options: "16:9", "9:16", "1:1")
        resolution: Resolution (default: "720p", options: "720p", "1080p")
        **kwargs: Additional parameters
    
    Returns:
        Dict chứa operation object và job info
    
    Raises:
        ValueError: Nếu prompt rỗng hoặc invalid parameters
        Exception: Nếu có lỗi khi gọi Veo API
    """
    if not prompt or not prompt.strip():
        error_msg = "Prompt cannot be empty"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    valid_aspect_ratios = ["16:9", "9:16", "1:1"]
    if aspect_ratio not in valid_aspect_ratios:
        error_msg = f"Invalid aspect_ratio: {aspect_ratio}. Must be one of {valid_aspect_ratios}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    valid_resolutions = ["720p", "1080p"]
    if resolution not in valid_resolutions:
        error_msg = f"Invalid resolution: {resolution}. Must be one of {valid_resolutions}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        logger.info(f"Generating video with prompt length: {len(prompt)}, aspect_ratio: {aspect_ratio}, resolution: {resolution}")
        client = get_veo_client()
        
        # Build config
        config = types.GenerateVideosConfig(
            aspect_ratio=aspect_ratio,
            resolution=resolution,
        )
        
        if negative_prompt:
            config.negative_prompt = negative_prompt
        
        # Generate video
        operation = client.models.generate_videos(
            model="veo-3.1-fast-generate-preview",
            prompt=prompt,
            config=config,
        )
        
        if not operation:
            error_msg = "Failed to get operation from Veo API"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        operation_name = getattr(operation, 'name', None) or str(operation)
        logger.info(f"Video generation started successfully, operation: {operation_name}")
        
        # Return operation info
        return {
            "operation": operation,
            "operation_name": operation_name,
            "status": "processing",
            "message": "Video generation started"
        }
    
    except ValueError:
        raise
    except Exception as e:
        error_msg = f"Error calling Veo API: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise Exception(error_msg) from e


def check_video_status(operation) -> dict:
    """
    Check status của video generation operation
    
    Args:
        operation: Operation object từ generate_video()
    
    Returns:
        Dict chứa status, video_url (nếu completed), error (nếu failed)
    """
    if not operation:
        error_msg = "Operation object is None"
        logger.error(error_msg)
        return {
            "status": "error",
            "video_url": None,
            "progress": 0,
            "error": error_msg,
            "message": f"Error checking status: {error_msg}"
        }
    
    try:
        # Check if operation is done
        if hasattr(operation, 'done'):
            is_done = operation.done()
            logger.debug(f"Operation done status: {is_done}")
        else:
            logger.warning("Operation object does not have 'done' method")
            is_done = False
        
        # Get result if done
        if is_done:
            try:
                result = operation.result()
                logger.info("Video generation completed, extracting video URL")
                
                # Extract video URL from result
                video_url = None
                if hasattr(result, 'video_uri'):
                    video_url = result.video_uri
                elif hasattr(result, 'uri'):
                    video_url = result.uri
                elif isinstance(result, dict):
                    video_url = result.get('video_uri') or result.get('uri')
                
                if video_url:
                    logger.info(f"Video URL extracted: {video_url}")
                else:
                    logger.warning("Video generation completed but no video URL found in result")
                
                return {
                    "status": "completed",
                    "video_url": video_url,
                    "progress": 100,
                    "error": None,
                    "message": "Video generation completed"
                }
            except Exception as result_error:
                logger.error(f"Error getting result from operation: {str(result_error)}", exc_info=True)
                return {
                    "status": "error",
                    "video_url": None,
                    "progress": 0,
                    "error": str(result_error),
                    "message": f"Error getting result: {str(result_error)}"
                }
        else:
            # Check for errors
            if hasattr(operation, 'error'):
                error = operation.error
                if error:
                    error_msg = str(error)
                    logger.error(f"Video generation failed with error: {error_msg}")
                    return {
                        "status": "failed",
                        "video_url": None,
                        "progress": 0,
                        "error": error_msg,
                        "message": "Video generation failed"
                    }
            
            logger.debug("Video generation still in progress")
            return {
                "status": "processing",
                "video_url": None,
                "progress": 0,
                "error": None,
                "message": "Video generation in progress"
            }
    
    except Exception as e:
        error_msg = f"Error checking video status: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "video_url": None,
            "progress": 0,
            "error": str(e),
            "message": error_msg
        }


def wait_for_video_completion(operation, max_wait_time: int = 300, check_interval: int = 5) -> dict:
    """
    Poll Veo API cho đến khi video generation hoàn thành
    
    Args:
        operation: Operation object từ generate_video()
        max_wait_time: Maximum time to wait in seconds (default 5 minutes)
        check_interval: Time between checks in seconds (default 5 seconds)
    
    Returns:
        Final status dict
    """
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        status_result = check_video_status(operation)
        
        if status_result["status"] in ["completed", "failed", "error"]:
            return status_result
        
        time.sleep(check_interval)
    
    # Timeout
    return {
        "status": "timeout",
        "error": "Video generation timeout",
        "message": f"Video generation took longer than {max_wait_time} seconds"
    }

