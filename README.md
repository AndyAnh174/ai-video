# AI Video Generator với Gemini và Veo

Ứng dụng Django để tạo video tự động từ dữ liệu CSV/Excel sử dụng Gemini API và Veo API.

## Tính năng

- **Bước 1**: Upload file CSV/Excel và tự động detect các cột dữ liệu
- **Bước 2**: Viết prompt template với hỗ trợ Gemini API để suggest/enhance prompts
- **Bước 3**: Tạo video cho mỗi dòng dữ liệu sử dụng Veo API

## Cài đặt

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình API Keys

Tạo file `.env` từ `.env.example`:

```bash
cp .env.example .env
```

Sau đó thêm API keys của bạn vào file `.env`:

```
GEMINI_API_KEY=your_gemini_api_key_here
VEO_API_KEY=your_veo_api_key_here
```

### 3. Chạy MongoDB với Docker

```bash
docker-compose up -d
```

MongoDB sẽ chạy trên port 27017 với:
- Username: `admin`
- Password: `admin123`
- Database: `agentvideo`

Bạn có thể thay đổi trong file `.env`:
```
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB_NAME=agentvideo
MONGO_USERNAME=admin
MONGO_PASSWORD=admin123
```

**Kiểm tra kết nối MongoDB:**
```bash
python test_mongodb_connection.py
```

Nếu có lỗi authentication, hãy đảm bảo:
1. MongoDB container đang chạy: `docker ps`
2. Đợi vài giây để MongoDB khởi động hoàn toàn
3. Kiểm tra logs: `docker-compose logs mongodb`

### 4. Chạy migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Tạo superuser (optional)

```bash
python manage.py createsuperuser
```

### 6. Chạy server

```bash
python manage.py runserver
```

Truy cập ứng dụng tại: http://localhost:8000

## Sử dụng

1. **Upload File**: Upload file CSV hoặc Excel chứa dữ liệu của bạn
2. **Write Prompt**: Viết prompt template sử dụng `{{field_name}}` để insert dữ liệu. Có thể dùng nút "Get AI Suggestion" để Gemini giúp cải thiện prompt.
3. **Generate Videos**: Nhấn "Start Generating Videos" để tạo video cho mỗi dòng dữ liệu.

## Cấu trúc Project

```
app/
├── models.py          # Project, DataFile, PromptTemplate, VideoGeneration
├── views.py           # Views cho 3 steps và API endpoints
├── services/
│   ├── gemini_service.py  # Gemini API integration
│   └── veo_service.py     # Veo API integration
├── templates/app/      # HTML templates
└── static/            # CSS và JavaScript files
```

## API Endpoints

- `POST /api/gemini/suggest-prompt/` - Get prompt suggestion từ Gemini
- `POST /api/prompt/save/<project_id>/` - Save prompt template
- `POST /api/veo/start/<project_id>/` - Start video generation
- `GET /api/veo/status/<video_id>/` - Check video generation status

## Docker Commands

### Start MongoDB
```bash
docker-compose up -d
```

### Stop MongoDB
```bash
docker-compose down
```

### View MongoDB logs
```bash
docker-compose logs -f mongodb
```

### Access MongoDB shell
```bash
docker exec -it agentvideo-mongodb mongosh -u admin -p admin123 --authenticationDatabase admin
```

## Lưu ý

- Veo API sử dụng Google Genai SDK với model `veo-3.1-fast-generate-preview`.
- Gemini model mặc định là `gemini-1.5-flash`. Có thể thay đổi qua environment variable `GEMINI_MODEL`.
- File uploads được lưu trong thư mục `media/` (tự động tạo khi cần).
- Operation objects được lưu trong memory cache. Trong production, nên sử dụng Redis hoặc Celery để handle background tasks tốt hơn.
- MongoDB data được lưu trong Docker volume `mongodb_data`.
