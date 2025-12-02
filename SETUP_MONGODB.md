# Setup MongoDB với mongoengine

## Đã chuyển từ djongo sang mongoengine

Do djongo không tương thích với Django 5.x, project đã được chuyển sang sử dụng **mongoengine** - một ODM (Object Document Mapper) cho MongoDB.

## Cài đặt

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Start MongoDB với Docker

```bash
docker-compose up -d
```

### 3. Cấu hình MongoDB trong `.env`

```
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB_NAME=agentvideo
MONGO_USERNAME=admin
MONGO_PASSWORD=admin123
```

### 4. Chạy migrations (chỉ cho SQLite - dùng cho Django admin)

```bash
python manage.py makemigrations
python manage.py migrate
```

**Lưu ý**: MongoDB không cần migrations như SQL databases. Collections sẽ được tạo tự động khi bạn tạo documents đầu tiên.

## Thay đổi chính

### Models
- Models được chuyển từ Django ORM (`app/models.py`) sang mongoengine (`app/mongodb_models.py`)
- Sử dụng `Document` thay vì `Model`
- Sử dụng mongoengine fields thay vì Django model fields

### Views
- Thay `get_object_or_404` bằng try/except với `ObjectId`
- Thay `objects.get_or_create` bằng try/except với `DoesNotExist`
- Convert `ObjectId` sang string khi trả về JSON
- File uploads được lưu vào media folder và path được lưu trong MongoDB

### Admin
- Django admin không tương thích với mongoengine
- Có thể tạo custom admin views nếu cần

## Kiểm tra kết nối MongoDB

```python
from mongoengine import connect
from app.mongodb_models import Project

# Test connection
projects = Project.objects.all()
print(f"Found {projects.count()} projects")
```

## Troubleshooting

### Lỗi kết nối MongoDB
- Kiểm tra MongoDB đã chạy: `docker ps`
- Kiểm tra credentials trong `.env`
- Kiểm tra firewall/port 27017

### Lỗi import
- Đảm bảo đã cài: `pip install mongoengine pymongo`
- Restart Django server sau khi cài packages

