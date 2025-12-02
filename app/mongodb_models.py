"""
MongoDB models using mongoengine
These models store the main application data in MongoDB
"""
from mongoengine import Document, EmbeddedDocument, fields, connect
from datetime import datetime
import os
from django.conf import settings

# Ensure connection is established
try:
    MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
    MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'agentvideo')
    MONGO_USERNAME = os.getenv('MONGO_USERNAME', 'admin')
    MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'admin123')
    
    if MONGO_USERNAME and MONGO_PASSWORD:
        mongo_connection_string = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource=admin"
        connect(db=MONGO_DB_NAME, host=mongo_connection_string, alias='default')
    else:
        connect(db=MONGO_DB_NAME, host=MONGO_HOST, port=MONGO_PORT, alias='default')
except Exception as e:
    print(f"Warning: MongoDB connection error in models: {e}")


class Project(Document):
    """Project chứa toàn bộ workflow từ upload file đến generate video"""
    name = fields.StringField(required=True, max_length=200)
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)
    status = fields.StringField(
        max_length=20,
        choices=['uploading', 'editing_prompt', 'generating', 'completed'],
        default='uploading'
    )
    
    meta = {
        'collection': 'projects',
        'indexes': ['name', 'status', 'created_at']
    }
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)


class DataFile(Document):
    """File CSV/Excel đã upload"""
    project = fields.ReferenceField(Project, reverse_delete_rule=2)  # CASCADE
    file_path = fields.StringField(required=True)  # Path to uploaded file
    file_type = fields.StringField(max_length=10, choices=['csv', 'xlsx'])
    columns = fields.ListField(fields.StringField(), default=list)
    total_rows = fields.IntField(default=0)
    uploaded_at = fields.DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'data_files',
        'indexes': ['project']
    }
    
    def __str__(self):
        import os
        return f"{self.project.name} - {os.path.basename(self.file_path)}"


class PromptTemplate(Document):
    """Prompt template với các placeholders {{field}}"""
    project = fields.ReferenceField(Project, reverse_delete_rule=2)  # CASCADE
    template = fields.StringField(required=True)
    enhanced_template = fields.StringField(default='')
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'prompt_templates',
        'indexes': ['project']
    }
    
    def __str__(self):
        return f"Prompt for {self.project.name}"
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)


class VideoGeneration(Document):
    """Mỗi video được generate từ một row dữ liệu"""
    project = fields.ReferenceField(Project, reverse_delete_rule=2)  # CASCADE
    row_index = fields.IntField(required=True)
    row_data = fields.DictField(required=True)
    prompt_used = fields.StringField(required=True)
    video_url = fields.URLField(default=None)
    video_file_path = fields.StringField(default=None)
    status = fields.StringField(
        max_length=20,
        choices=['pending', 'processing', 'completed', 'failed'],
        default='pending'
    )
    veo_job_id = fields.StringField(max_length=200, default=None)
    error_message = fields.StringField(default=None)
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'video_generations',
        'indexes': ['project', 'row_index', 'status', 'created_at'],
        'ordering': ['row_index']
    }
    
    def __str__(self):
        return f"Video {self.row_index} - {self.project.name}"
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

