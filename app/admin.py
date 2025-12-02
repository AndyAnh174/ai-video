from django.contrib import admin

# Note: MongoDB models (mongoengine) are not compatible with Django admin
# If you need admin interface, consider using mongo-admin or create custom admin views
# For now, Django admin is disabled for MongoDB models

# If you want to keep some Django models for admin, you can create separate models
# or use a hybrid approach with SQLite for admin and MongoDB for main data
