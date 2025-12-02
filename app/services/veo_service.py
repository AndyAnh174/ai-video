import os
import time
from django.conf import settings
from google import genai
from google.genai import types


def get_veo_client():
    """Get Veo client with API key"""
    api_key = os.getenv('VEO_API_KEY') or getattr(settings, 'VEO_API_KEY', None)
    if not api_key:
        raise ValueError("VEO_API_KEY not found in environment variables or settings")
    
    # Initialize client with API key
    client = genai.Client(api_key=api_key)
    return client


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
    """
    try:
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
        
        # Return operation info
        return {
            "operation": operation,
            "operation_name": getattr(operation, 'name', None) or str(operation),
            "status": "processing",
            "message": "Video generation started"
        }
    
    except Exception as e:
        raise Exception(f"Error calling Veo API: {str(e)}")


def check_video_status(operation) -> dict:
    """
    Check status của video generation operation
    
    Args:
        operation: Operation object từ generate_video()
    
    Returns:
        Dict chứa status, video_url (nếu completed), error (nếu failed)
    """
    try:
        # Check if operation is done
        if hasattr(operation, 'done'):
            is_done = operation.done()
        else:
            # Try to refresh operation status
            client = get_veo_client()
            # Re-fetch operation if needed
            is_done = False
        
        # Get result if done
        if is_done:
            result = operation.result()
            
            # Extract video URL from result
            video_url = None
            if hasattr(result, 'video_uri'):
                video_url = result.video_uri
            elif hasattr(result, 'uri'):
                video_url = result.uri
            elif isinstance(result, dict):
                video_url = result.get('video_uri') or result.get('uri')
            
            return {
                "status": "completed",
                "video_url": video_url,
                "progress": 100,
                "error": None,
                "message": "Video generation completed"
            }
        else:
            # Check for errors
            if hasattr(operation, 'error'):
                error = operation.error
                return {
                    "status": "failed",
                    "video_url": None,
                    "progress": 0,
                    "error": str(error) if error else "Unknown error",
                    "message": "Video generation failed"
                }
            
            return {
                "status": "processing",
                "video_url": None,
                "progress": 0,
                "error": None,
                "message": "Video generation in progress"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "video_url": None,
            "progress": 0,
            "error": str(e),
            "message": f"Error checking status: {str(e)}"
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

