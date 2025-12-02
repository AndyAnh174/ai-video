@echo off
echo Starting Celery Worker for agentvideo...
echo.
echo Make sure Redis is running: docker-compose up -d redis
echo.
celery -A agentvideo worker --loglevel=info --pool=solo
pause

