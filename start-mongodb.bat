@echo off
echo Starting MongoDB with Docker...
docker-compose up -d
echo.
echo MongoDB is running on localhost:27017
echo Username: admin
echo Password: admin123
echo Database: agentvideo
echo.
echo To stop MongoDB, run: docker-compose down
pause

