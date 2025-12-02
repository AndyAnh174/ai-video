"""
Celery tasks for video generation
"""
import os
import json
import logging
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from bson import ObjectId
from mongoengine import DoesNotExist
from .mongodb_models import Project, DataFile, PromptTemplate, VideoGeneration
from .services import veo_service

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_single_video(self, video_id: str):
    """
    Generate video for a single VideoGeneration record
    
    Args:
        video_id: MongoDB ObjectId string of VideoGeneration
    
    Returns:
        dict with status and result
    """
    try:
        # Get video generation record
        video_gen = VideoGeneration.objects.get(id=ObjectId(video_id))
        
        # Check if already processing or completed
        if video_gen.status in ['processing', 'completed']:
            logger.info(f"Video {video_id} already in status: {video_gen.status}")
            return {
                'status': video_gen.status,
                'video_id': video_id,
                'message': f'Video already {video_gen.status}'
            }
        
        # Update status to processing
        video_gen.status = 'processing'
        video_gen.save()
        
        logger.info(f"Starting video generation for video_id: {video_id}, prompt: {video_gen.prompt_used[:100]}...")
        
        # Call Veo API
        result = veo_service.generate_video(video_gen.prompt_used)
        operation = result.get('operation')
        operation_name = result.get('operation_name')
        
        if not operation:
            raise Exception("Failed to get operation from Veo API")
        
        # Store operation in Redis cache (instead of in-memory)
        cache_key = f'veo_operation:{video_id}'
        # Store operation name and metadata in cache
        cache.set(
            cache_key,
            {
                'operation_name': operation_name,
                'status': 'processing',
                'created_at': str(video_gen.created_at)
            },
            timeout=3600 * 24  # 24 hours
        )
        
        # Update video generation record
        video_gen.veo_job_id = operation_name or str(video_id)
        video_gen.save()
        
        logger.info(f"Video generation started for {video_id}, operation: {operation_name}")
        
        return {
            'status': 'processing',
            'video_id': video_id,
            'operation_name': operation_name,
            'message': 'Video generation started'
        }
    
    except DoesNotExist:
        error_msg = f"VideoGeneration with id {video_id} not found"
        logger.error(error_msg)
        return {
            'status': 'failed',
            'video_id': video_id,
            'error': error_msg
        }
    
    except Exception as e:
        error_msg = f"Error generating video {video_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Update video generation status to failed
        try:
            video_gen = VideoGeneration.objects.get(id=ObjectId(video_id))
            video_gen.status = 'failed'
            video_gen.error_message = str(e)
            video_gen.save()
        except:
            pass
        
        # Retry if not exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying video generation for {video_id}, attempt {self.request.retries + 1}")
            raise self.retry(exc=e)
        
        return {
            'status': 'failed',
            'video_id': video_id,
            'error': error_msg
        }


@shared_task
def check_video_status_task(video_id: str):
    """
    Check status of a video generation and update the record
    
    Args:
        video_id: MongoDB ObjectId string of VideoGeneration
    
    Returns:
        dict with status information
    """
    try:
        video_gen = VideoGeneration.objects.get(id=ObjectId(video_id))
        
        # Get operation from Redis cache
        cache_key = f'veo_operation:{video_id}'
        operation_data = cache.get(cache_key)
        
        if not operation_data:
            logger.warning(f"No operation found in cache for video {video_id}")
            return {
                'status': video_gen.status,
                'video_id': video_id,
                'message': 'No operation found. Video may not have started yet.'
            }
        
        # Reconstruct operation (in production, you might need to store more info)
        # For now, we'll use the veo_service to check status
        # Note: This is a simplified version - in production you'd store the full operation object
        
        # Since we can't easily reconstruct the operation object,
        # we'll use a different approach: store operation_name and check via API
        operation_name = operation_data.get('operation_name')
        
        if not operation_name:
            return {
                'status': video_gen.status,
                'video_id': video_id,
                'message': 'Operation name not found'
            }
        
        # For now, we'll need to modify veo_service to support checking by operation name
        # Or we can implement a polling mechanism
        # This is a placeholder - you may need to adjust based on Veo API capabilities
        
        logger.info(f"Checking status for video {video_id}, operation: {operation_name}")
        
        # Update status based on current state
        # In a real implementation, you'd call Veo API to check the actual status
        return {
            'status': video_gen.status,
            'video_id': video_id,
            'operation_name': operation_name,
            'message': 'Status check completed'
        }
    
    except DoesNotExist:
        return {
            'status': 'error',
            'video_id': video_id,
            'error': f'VideoGeneration with id {video_id} not found'
        }
    
    except Exception as e:
        logger.error(f"Error checking video status {video_id}: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'video_id': video_id,
            'error': str(e)
        }


@shared_task
def batch_generate_videos(project_id: str):
    """
    Generate videos for all rows in a project
    
    Args:
        project_id: MongoDB ObjectId string of Project
    
    Returns:
        dict with summary of started tasks
    """
    try:
        project = Project.objects.get(id=ObjectId(project_id))
        data_file = DataFile.objects.get(project=project)
        prompt_template = PromptTemplate.objects.get(project=project)
        
        # Read the data file
        import pandas as pd
        file_path = os.path.join(settings.MEDIA_ROOT, data_file.file_path)
        
        if data_file.file_type == 'csv':
            df = pd.read_csv(file_path, encoding='utf-8-sig')
        else:
            df = pd.read_excel(file_path, engine='openpyxl')
        
        # Update project status
        project.status = 'generating'
        project.save()
        
        # Create VideoGeneration objects and queue tasks
        created_videos = []
        tasks_started = []
        
        for index, row in df.iterrows():
            row_data = row.to_dict()
            
            # Fill template with row data
            filled_prompt = prompt_template.template
            for key, value in row_data.items():
                placeholder = f"{{{{{key}}}}}"
                filled_prompt = filled_prompt.replace(placeholder, str(value))
            
            # Create VideoGeneration record
            video_gen = VideoGeneration(
                project=project,
                row_index=int(index),
                row_data=row_data,
                prompt_used=filled_prompt,
                status='pending'
            )
            video_gen.save()
            
            created_videos.append(str(video_gen.id))
            
            # Queue Celery task for async processing
            task = generate_single_video.delay(str(video_gen.id))
            tasks_started.append({
                'video_id': str(video_gen.id),
                'task_id': task.id
            })
        
        logger.info(f"Started {len(tasks_started)} video generation tasks for project {project_id}")
        
        return {
            'success': True,
            'project_id': project_id,
            'video_count': len(created_videos),
            'tasks_started': len(tasks_started),
            'message': f'Started generating {len(created_videos)} videos'
        }
    
    except DoesNotExist as e:
        error_msg = f"Project, DataFile, or PromptTemplate not found: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg
        }
    
    except Exception as e:
        error_msg = f"Error in batch_generate_videos: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Update project status on error
        try:
            project = Project.objects.get(id=ObjectId(project_id))
            project.status = 'editing_prompt'
            project.save()
        except:
            pass
        
        return {
            'success': False,
            'error': error_msg
        }

