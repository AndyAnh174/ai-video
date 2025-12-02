from django.db import models
from django.core.files.storage import default_storage
import os


class Project(models.Model):
    """Project chứa toàn bộ workflow từ upload file đến generate video"""
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('uploading', 'Uploading'),
            ('editing_prompt', 'Editing Prompt'),
            ('generating', 'Generating Videos'),
            ('completed', 'Completed'),
        ],
        default='uploading'
    )

    def __str__(self):
        return self.name


class DataFile(models.Model):
    """File CSV/Excel đã upload"""
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='data_file')
    file = models.FileField(upload_to='uploads/data_files/')
    file_type = models.CharField(max_length=10, choices=[('csv', 'CSV'), ('xlsx', 'Excel')])
    columns = models.JSONField(default=list, help_text="Danh sách các columns trong file")
    total_rows = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.name} - {os.path.basename(self.file.name)}"


class PromptTemplate(models.Model):
    """Prompt template với các placeholders {{field}}"""
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='prompt_template')
    template = models.TextField(help_text="Prompt template với {{field}} placeholders")
    enhanced_template = models.TextField(blank=True, help_text="Prompt đã được Gemini enhance")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Prompt for {self.project.name}"


class VideoGeneration(models.Model):
    """Mỗi video được generate từ một row dữ liệu"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='videos')
    row_index = models.IntegerField(help_text="Index của row trong file (0-based)")
    row_data = models.JSONField(help_text="Dữ liệu của row này")
    prompt_used = models.TextField(help_text="Prompt đã được fill data cho row này")
    video_url = models.URLField(blank=True, null=True)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    veo_job_id = models.CharField(max_length=200, blank=True, null=True, help_text="Job ID từ Veo API")
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['row_index']

    def __str__(self):
        return f"Video {self.row_index} - {self.project.name}"
