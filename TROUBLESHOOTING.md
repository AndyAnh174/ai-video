# Troubleshooting MongoDB Connection

## Lỗi Authentication Failed

Nếu gặp lỗi `Authentication failed`, thử các bước sau:

### 1. Kiểm tra MongoDB đang chạy

```bash
docker ps
```

Nếu container không chạy:
```bash
docker-compose up -d
```

### 2. Đợi MongoDB khởi động hoàn toàn

MongoDB cần vài giây để khởi động và tạo user. Đợi 10-15 giây sau khi start container.

### 3. Kiểm tra logs

```bash
docker-compose logs mongodb
```

Tìm dòng "Waiting for connections" để biết MongoDB đã sẵn sàng.

### 4. Test connection

```bash
python test_mongodb_connection.py
```

### 5. Reset MongoDB (nếu cần)

Nếu vẫn không được, có thể reset MongoDB:

```bash
# Stop và xóa container
docker-compose down -v

# Start lại
docker-compose up -d

# Đợi 15 giây
sleep 15

# Test lại
python test_mongodb_connection.py
```

### 6. Kiểm tra credentials trong .env

Đảm bảo file `.env` có đúng:
```
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB_NAME=agentvideo
MONGO_USERNAME=admin
MONGO_PASSWORD=admin123
```

### 7. Thử kết nối không cần authentication (tạm thời)

Nếu vẫn không được, có thể tạm thời tắt authentication trong `docker-compose.yml`:

```yaml
# Xóa dòng này:
command: mongod --auth

# Và trong settings.py, set:
MONGO_USERNAME=
MONGO_PASSWORD=
```

**Lưu ý**: Chỉ dùng cho development, không dùng cho production!

### 8. Kết nối trực tiếp với mongosh

```bash
docker exec -it agentvideo-mongodb mongosh -u admin -p admin123 --authenticationDatabase admin
```

Nếu kết nối được, MongoDB đang chạy đúng. Vấn đề có thể ở cách mongoengine connect.

## Lỗi khác

### Connection refused
- Kiểm tra MongoDB container đang chạy
- Kiểm tra port 27017 không bị block bởi firewall

### Timeout
- Kiểm tra network connection
- Thử restart container: `docker-compose restart mongodb`

