# Hướng dẫn chạy với Docker

## Quick Start

Chạy tất cả services với một lệnh:

```bash
docker-compose up -d
```

Truy cập ứng dụng tại: http://localhost:8000

## Services

Docker Compose sẽ khởi động các services sau:

1. **mongodb** - MongoDB database (port 27017)
2. **redis** - Redis cache và Celery broker (port 6379)
3. **web** - Django web server (port 8000)
4. **celery-worker** - Celery worker xử lý video generation
5. **celery-beat** - Celery beat cho scheduled tasks

## Commands

### Khởi động
```bash
# Khởi động tất cả services
docker-compose up -d

# Khởi động và rebuild
docker-compose up -d --build

# Khởi động và xem logs
docker-compose up
```

### Dừng
```bash
# Dừng tất cả services
docker-compose down

# Dừng và xóa volumes (xóa data)
docker-compose down -v
```

### Logs
```bash
# Xem tất cả logs
docker-compose logs -f

# Xem logs của một service cụ thể
docker-compose logs -f celery-worker
docker-compose logs -f web
docker-compose logs -f mongodb
docker-compose logs -f redis
```

### Restart
```bash
# Restart tất cả services
docker-compose restart

# Restart một service cụ thể
docker-compose restart celery-worker
docker-compose restart web
```

### Chạy commands trong container
```bash
# Chạy Django management commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# Chạy shell trong container
docker-compose exec web bash
docker-compose exec celery-worker bash

# Test MongoDB connection
docker-compose exec web python test_mongodb_connection.py
```

## Environment Variables

Tạo file `.env` trong thư mục project:

```env
# MongoDB (sử dụng service name 'mongodb' trong Docker)
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DB_NAME=agentvideo
MONGO_USERNAME=admin
MONGO_PASSWORD=admin123

# Redis (sử dụng service name 'redis' trong Docker)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
VEO_API_KEY=your_veo_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

**Lưu ý:** Khi chạy trong Docker, các services có thể truy cập nhau qua service name (`mongodb`, `redis`) thay vì `localhost`.

## Volumes

Docker Compose tạo các volumes để persist data:

- `mongodb_data` - MongoDB data
- `redis_data` - Redis data
- `media_files` - Uploaded files và generated videos

## Network

Tất cả services chạy trong network `agentvideo-network`, cho phép chúng truy cập nhau qua service name.

## Troubleshooting

### Container không start
```bash
# Xem logs để biết lỗi
docker-compose logs [service-name]

# Kiểm tra container status
docker ps -a

# Rebuild containers
docker-compose up -d --build
```

### Lỗi kết nối MongoDB
```bash
# Kiểm tra MongoDB đang chạy
docker-compose ps mongodb

# Test connection từ web container
docker-compose exec web python test_mongodb_connection.py

# Xem MongoDB logs
docker-compose logs mongodb
```

### Lỗi kết nối Redis
```bash
# Kiểm tra Redis đang chạy
docker-compose ps redis

# Test connection từ web container
docker-compose exec web python -c "from django.core.cache import cache; cache.set('test', 'ok'); print(cache.get('test'))"

# Xem Redis logs
docker-compose logs redis
```

### Celery worker không chạy tasks
```bash
# Kiểm tra worker đang chạy
docker-compose ps celery-worker

# Xem worker logs
docker-compose logs -f celery-worker

# Kiểm tra Redis có nhận tasks
docker-compose exec redis redis-cli LLEN celery
```

### Code changes không áp dụng
```bash
# Rebuild containers
docker-compose up -d --build

# Hoặc restart service
docker-compose restart web
docker-compose restart celery-worker
```

### Xóa tất cả và bắt đầu lại
```bash
# Dừng và xóa containers, networks, volumes
docker-compose down -v

# Xóa images
docker-compose down --rmi all

# Build lại từ đầu
docker-compose up -d --build
```

## Production

Cho production, bạn nên:

1. Sử dụng production-ready web server (Gunicorn, uWSGI) thay vì Django dev server
2. Cấu hình nginx làm reverse proxy
3. Sử dụng secrets management cho API keys
4. Enable SSL/TLS
5. Setup monitoring và logging
6. Configure backup cho MongoDB và Redis
7. Sử dụng Docker secrets hoặc environment variables từ secure source

Ví dụ với Gunicorn:

```yaml
web:
  command: gunicorn agentvideo.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

