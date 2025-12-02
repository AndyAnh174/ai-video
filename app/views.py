import os
import json
import logging
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.core.cache import cache
# Use MongoDB models instead of Django ORM models
from .mongodb_models import Project, DataFile, PromptTemplate, VideoGeneration
from .services import gemini_service, veo_service
from .tasks import batch_generate_videos, generate_single_video, check_video_status_task
import re

logger = logging.getLogger(__name__)


def index(request):
    """Redirect to step 1 or create new project"""
    return redirect('step1_upload')


@csrf_exempt
def step1_upload(request):
    """Step 1: Upload CSV/Excel file and detect columns"""
    if request.method == 'POST':
        project_name = request.POST.get('project_name', 'Untitled Project')
        uploaded_file = request.FILES.get('data_file')
        
        if not uploaded_file:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
        
        # Determine file type
        file_name = uploaded_file.name.lower()
        if file_name.endswith('.csv'):
            file_type = 'csv'
        elif file_name.endswith(('.xlsx', '.xls')):
            file_type = 'xlsx'
        else:
            return JsonResponse({'error': 'Unsupported file type. Please upload CSV or Excel file.'}, status=400)
        
        # Save file to media folder
        import os
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', 'data_files')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = default_storage.save(
            os.path.join('uploads', 'data_files', uploaded_file.name),
            ContentFile(uploaded_file.read())
        )
        full_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
        
        # Create project in MongoDB
        project = Project(name=project_name, status='uploading')
        project.save()
        
        # Parse file and detect columns
        try:
            # Read file without normalizing column names
            # Keep original column names as they appear in the file
            if file_type == 'csv':
                # Read CSV with original column names, handle encoding
                df = pd.read_csv(full_file_path, encoding='utf-8-sig')
            else:
                # Read Excel with original column names
                df = pd.read_excel(full_file_path, engine='openpyxl')
            
            # Get original column names (preserve Vietnamese characters, spaces, etc.)
            columns = df.columns.tolist()
            total_rows = len(df)
            
            # Ensure columns are stored as list of strings (not normalized)
            # Convert any non-string column names to strings while preserving original format
            columns = [str(col) for col in columns]
            
            # Create DataFile in MongoDB
            data_file = DataFile(
                project=project,
                file_path=file_path,
                file_type=file_type,
                columns=columns,
                total_rows=total_rows
            )
            data_file.save()
            
            # Update project status
            project.status = 'editing_prompt'
            project.save()
            
            return JsonResponse({
                'success': True,
                'project_id': str(project.id),  # Convert ObjectId to string
                'columns': columns,
                'total_rows': total_rows,
                'preview': df.head(5).to_dict('records')  # First 5 rows as preview
            })
        
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            project.delete()  # Clean up on error
            # Log error for debugging
            print(f"Error parsing file: {str(e)}")
            print(error_trace)
            return JsonResponse({'error': f'Error parsing file: {str(e)}'}, status=400)
    
    # GET request - show upload form
    return render(request, 'app/step1_upload.html')


def step2_prompt(request, project_id):
    """Step 2: Prompt editor with Gemini integration"""
    from bson import ObjectId
    from mongoengine import DoesNotExist
    
    try:
        project = Project.objects.get(id=ObjectId(project_id))
    except (DoesNotExist, Exception):
        from django.http import Http404
        raise Http404("Project not found")
    
    try:
        data_file = DataFile.objects.get(project=project)
    except (DoesNotExist, Exception):
        from django.http import Http404
        raise Http404("Data file not found")
    
    # Get or create prompt template
    try:
        prompt_template = PromptTemplate.objects.get(project=project)
    except DoesNotExist:
        prompt_template = PromptTemplate(project=project, template='')
        prompt_template.save()
    
    # Generate default template with all fields
    if not prompt_template.template and data_file.columns:
        default_template = "Create a video about "
        for i, col in enumerate(data_file.columns):
            if i > 0:
                default_template += ", "
            default_template += f"{{{{{col}}}}}"
        prompt_template.template = default_template
        prompt_template.save()
    
    # Ensure fields is a list
    fields_list = data_file.columns if data_file.columns else []
    if not isinstance(fields_list, list):
        fields_list = list(fields_list) if fields_list else []
    
    context = {
        'project': project,
        'data_file': data_file,
        'prompt_template': prompt_template,
        'fields': fields_list,
        'fields_json': json.dumps(fields_list),
    }
    
    return render(request, 'app/step2_prompt.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def api_gemini_suggest_prompt(request):
    """API endpoint: Get prompt suggestion from Gemini"""
    try:
        data = json.loads(request.body)
        template = data.get('template', '').strip()
        fields = data.get('fields', [])
        
        # Validate input
        if not template:
            return JsonResponse({'error': 'Template is required'}, status=400)
        
        if not fields:
            return JsonResponse({'error': 'Fields are required'}, status=400)
        
        # Ensure fields is a list
        if not isinstance(fields, list):
            return JsonResponse({'error': 'Fields must be an array'}, status=400)
        
        if len(fields) == 0:
            return JsonResponse({'error': 'At least one field is required'}, status=400)
        
        suggested_prompt = gemini_service.generate_prompt_suggestion(template, fields)
        
        return JsonResponse({
            'success': True,
            'suggested_prompt': suggested_prompt
        })
    
    except json.JSONDecodeError as e:
        return JsonResponse({'error': f'Invalid JSON: {str(e)}'}, status=400)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in api_gemini_suggest_prompt: {str(e)}")
        print(error_trace)
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def save_prompt_template(request, project_id):
    """Save prompt template"""
    project = get_object_or_404(Project, id=project_id)
    
    try:
        data = json.loads(request.body)
        template = data.get('template', '')
        
        prompt_template, created = PromptTemplate.objects.get_or_create(project=project)
        prompt_template.template = template
        prompt_template.save()
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def step3_videos(request, project_id):
    """Step 3: Video generation view"""
    from bson import ObjectId
    from mongoengine import DoesNotExist
    
    try:
        project = Project.objects.get(id=ObjectId(project_id))
    except (DoesNotExist, Exception):
        from django.http import Http404
        raise Http404("Project not found")
    
    try:
        data_file = DataFile.objects.get(project=project)
    except (DoesNotExist, Exception):
        from django.http import Http404
        raise Http404("Data file not found")
    
    try:
        prompt_template = PromptTemplate.objects.get(project=project)
    except (DoesNotExist, Exception):
        from django.http import Http404
        raise Http404("Prompt template not found")
    
    # Get all video generations for this project
    videos = VideoGeneration.objects(project=project)
    
    context = {
        'project': project,
        'data_file': data_file,
        'prompt_template': prompt_template,
        'videos': videos,
    }
    
    return render(request, 'app/step3_videos.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def api_start_video_generation(request, project_id):
    """API endpoint: Start video generation for all rows using Celery"""
    from bson import ObjectId
    from mongoengine import DoesNotExist
    
    try:
        project = Project.objects.get(id=ObjectId(project_id))
    except (DoesNotExist, Exception) as e:
        logger.error(f"Project not found: {project_id}, error: {str(e)}")
        return JsonResponse({'error': 'Project not found'}, status=404)
    
    try:
        data_file = DataFile.objects.get(project=project)
    except (DoesNotExist, Exception) as e:
        logger.error(f"Data file not found for project {project_id}, error: {str(e)}")
        return JsonResponse({'error': 'Data file not found'}, status=404)
    
    try:
        prompt_template = PromptTemplate.objects.get(project=project)
    except (DoesNotExist, Exception) as e:
        logger.error(f"Prompt template not found for project {project_id}, error: {str(e)}")
        return JsonResponse({'error': 'Prompt template not found'}, status=404)
    
    # Validate prompt template is not empty
    if not prompt_template.template or not prompt_template.template.strip():
        return JsonResponse({'error': 'Prompt template is empty. Please save a prompt template first.'}, status=400)
    
    try:
        # Queue Celery task for async batch processing
        task = batch_generate_videos.delay(str(project.id))
        
        logger.info(f"Queued batch video generation task {task.id} for project {project_id}")
        
        return JsonResponse({
            'success': True,
            'message': 'Video generation started. Videos will be processed asynchronously.',
            'task_id': task.id,
            'project_id': project_id
        })
    
    except Exception as e:
        logger.error(f"Error starting video generation for project {project_id}: {str(e)}", exc_info=True)
        
        # Update project status on error
        try:
            project.status = 'editing_prompt'
            project.save()
        except Exception as save_error:
            logger.error(f"Error updating project status: {str(save_error)}")
        
        return JsonResponse({
            'error': f'Error starting video generation: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def api_veo_status(request, video_id):
    """API endpoint: Check Veo video generation status using Redis cache"""
    from bson import ObjectId
    from mongoengine import DoesNotExist
    
    try:
        video_gen = VideoGeneration.objects.get(id=ObjectId(video_id))
    except (DoesNotExist, Exception) as e:
        logger.error(f"Video generation not found: {video_id}, error: {str(e)}")
        return JsonResponse({'error': 'Video generation not found'}, status=404)
    
    # Get operation data from Redis cache
    cache_key = f'veo_operation:{video_id}'
    operation_data = cache.get(cache_key)
    
    if not operation_data:
        logger.debug(f"No operation found in Redis cache for video {video_id}")
        return JsonResponse({
            'status': video_gen.status,
            'video_id': str(video_id),
            'message': 'No operation found. Video may not have started yet or cache expired.'
        })
    
    try:
        # Queue async status check task
        # For real-time status, we can also check directly
        # But for better scalability, we use the task
        task = check_video_status_task.delay(str(video_id))
        
        # Also try to get current status from database
        # The task will update the status in the background
        response_data = {
            'status': video_gen.status,
            'video_id': str(video_id),
            'operation_name': operation_data.get('operation_name'),
            'task_id': task.id,
            'message': 'Status check queued'
        }
        
        # If video is already completed, include video URL
        if video_gen.status == 'completed' and video_gen.video_url:
            response_data['video_url'] = video_gen.video_url
        
        # If video failed, include error message
        if video_gen.status == 'failed' and video_gen.error_message:
            response_data['error'] = video_gen.error_message
        
        return JsonResponse(response_data)
    
    except Exception as e:
        logger.error(f"Error checking video status {video_id}: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': str(e),
            'status': video_gen.status,
            'video_id': str(video_id)
        }, status=500)
