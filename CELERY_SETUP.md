# Hướng dẫn chạy Celery và Redis

## Cách 1: Chạy với Docker (Khuyến nghị)

### 1. Khởi động tất cả services với Docker Compose

```bash
docker-compose up -d
```

Lệnh này sẽ khởi động:
- **MongoDB** trên port 27017
- **Redis** trên port 6379
- **Django Web** trên port 8000
- **Celery Worker** (xử lý video generation)
- **Celery Beat** (cho scheduled tasks nếu cần)

### 2. Xem logs

```bash
# Xem tất cả logs
docker-compose logs -f

# Xem logs của Celery worker
docker-compose logs -f celery-worker

# Xem logs của web server
docker-compose logs -f web
```

### 3. Dừng services

```bash
docker-compose down
```

### 4. Rebuild containers (khi có thay đổi code)

```bash
docker-compose up -d --build
```

### 5. Chỉ chạy một số services

```bash
# Chỉ chạy MongoDB và Redis
docker-compose up -d mongodb redis

# Chỉ chạy Celery worker
docker-compose up -d celery-worker
```

## Cách 2: Chạy local (không dùng Docker)

### 1. Khởi động Redis với Docker

Redis đã được thêm vào `docker-compose.yml`. Để khởi động:

```bash
docker-compose up -d redis mongodb
```

Redis sẽ chạy trên port `6379`.

## 2. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

## 3. Chạy Celery Worker

Trong một terminal riêng, chạy Celery worker:

### Windows (PowerShell):
```powershell
celery -A agentvideo worker --loglevel=info --pool=solo
```

### Linux/Mac:
```bash
celery -A agentvideo worker --loglevel=info
```

### Với hot reload (development):
```bash
celery -A agentvideo worker --loglevel=info --reload
```

## 4. Chạy Celery Beat (nếu cần scheduled tasks)

```bash
celery -A agentvideo beat --loglevel=info
```

## 5. Monitor Celery (optional)

Cài đặt Flower để monitor Celery:

```bash
pip install flower
```

Chạy Flower:

```bash
celery -A agentvideo flower
```

Truy cập tại: http://localhost:5555

## 6. Kiểm tra kết nối Redis

```bash
# Windows
redis-cli -h localhost -p 6379 ping

# Linux/Mac (nếu đã cài redis-cli)
redis-cli ping
```

Hoặc test trong Python:

```python
from django.core.cache import cache
cache.set('test', 'value', 30)
print(cache.get('test'))
```

## 7. Environment Variables

Đảm bảo file `.env` có các biến sau:

### Khi chạy với Docker:
```env
# MongoDB (sử dụng service name trong docker-compose)
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DB_NAME=agentvideo
MONGO_USERNAME=admin
MONGO_PASSWORD=admin123

# Redis (sử dụng service name trong docker-compose)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://redis:6379/0

# Celery (sử dụng service name trong docker-compose)
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# API Keys
GEMINI_API_KEY=your_key_here
VEO_API_KEY=your_key_here
```

### Khi chạy local (không Docker):
```env
# Redis (optional, có default)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://localhost:6379/0

# Celery (optional, có default)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# MongoDB
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB_NAME=agentvideo
MONGO_USERNAME=admin
MONGO_PASSWORD=admin123

# API Keys
GEMINI_API_KEY=your_key_here
VEO_API_KEY=your_key_here
```

**Lưu ý:** Khi chạy với Docker, các service có thể truy cập nhau qua service name (mongodb, redis) thay vì localhost.

## 8. Troubleshooting

### Lỗi kết nối Redis (Docker):
- Kiểm tra Redis container đang chạy: `docker ps`
- Kiểm tra logs: `docker-compose logs redis`
- Thử restart: `docker-compose restart redis`
- Kiểm tra network: `docker network ls` và `docker network inspect agentvideo_agentvideo-network`

### Lỗi Celery worker (Docker):
- Kiểm tra container đang chạy: `docker ps | grep celery`
- Xem logs chi tiết: `docker-compose logs celery-worker`
- Kiểm tra Redis connection trong container: `docker-compose exec celery-worker python -c "from django.core.cache import cache; cache.set('test', 'ok'); print(cache.get('test'))"`
- Kiểm tra MongoDB connection: `docker-compose exec celery-worker python test_mongodb_connection.py`

### Lỗi Celery worker (Local):
- Kiểm tra Redis connection
- Kiểm tra MongoDB connection
- Xem logs của worker để biết lỗi cụ thể

### Tasks không chạy:
- Đảm bảo worker đang chạy: `docker ps | grep celery-worker` hoặc check process
- Kiểm tra task có được import đúng không
- Xem logs của worker: `docker-compose logs -f celery-worker`
- Kiểm tra Redis có nhận tasks không: `docker-compose exec redis redis-cli LLEN celery`

### Lỗi build Docker image:
- Xóa cache và rebuild: `docker-compose build --no-cache`
- Kiểm tra Dockerfile có đúng không
- Kiểm tra requirements.txt có đầy đủ dependencies

## 9. Production Setup

Trong production, nên sử dụng:
- Supervisor hoặc systemd để quản lý Celery worker
- Redis với persistence
- Monitoring với Flower hoặc Celery monitoring tools
- Logging tập trung

