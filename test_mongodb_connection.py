"""
Test MongoDB connection
Run this script to verify MongoDB connection before starting Django server
"""
import os
from dotenv import load_dotenv
import mongoengine
from pymongo import MongoClient

load_dotenv()

MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'agentvideo')
MONGO_USERNAME = os.getenv('MONGO_USERNAME', 'admin')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'admin123')

print("Testing MongoDB connection...")
print(f"Host: {MONGO_HOST}:{MONGO_PORT}")
print(f"Database: {MONGO_DB_NAME}")
print(f"Username: {MONGO_USERNAME}")

# Test with pymongo first - try without auth first
try:
    # Try without authentication first
    client = MongoClient(host=MONGO_HOST, port=MONGO_PORT)
    client.admin.command('ping')
    print("✓ pymongo connection successful (no auth)!")
except Exception as e1:
    # If that fails, try with authentication
    try:
        if MONGO_USERNAME and MONGO_PASSWORD:
            client = MongoClient(
                host=MONGO_HOST,
                port=MONGO_PORT,
                username=MONGO_USERNAME,
                password=MONGO_PASSWORD,
                authSource='admin'
            )
        else:
            raise e1
    except Exception as e2:
        print(f"✗ pymongo connection failed: {e2}")
        print("\nTroubleshooting:")
        print("1. Make sure MongoDB is running: docker ps")
        print("2. Check if MongoDB container is up: docker-compose up -d")
        print("3. Verify credentials in .env file")
        print("4. Check MongoDB logs: docker-compose logs mongodb")
        exit(1)
    
try:
    
    # Test connection (already tested above)
    
    # List databases
    print(f"Available databases: {client.list_database_names()}")
    
except Exception as e:
    print(f"✗ pymongo connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure MongoDB is running: docker ps")
    print("2. Check if MongoDB container is up: docker-compose up -d")
    print("3. Verify credentials in .env file")
    print("4. Check MongoDB logs: docker-compose logs mongodb")
    exit(1)

# Test with mongoengine - try without auth first
try:
    # Try without authentication first
    mongoengine.connect(
        db=MONGO_DB_NAME,
        host=MONGO_HOST,
        port=MONGO_PORT,
        alias='default'
    )
    print("✓ mongoengine connection successful (no auth)!")
    print("\nMongoDB is ready to use!")
except Exception as e1:
    # If that fails, try with authentication
    try:
        if MONGO_USERNAME and MONGO_PASSWORD:
            mongo_connection_string = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource=admin"
            mongoengine.connect(
                db=MONGO_DB_NAME,
                host=mongo_connection_string,
                alias='default'
            )
            print("✓ mongoengine connection successful (with auth)!")
            print("\nMongoDB is ready to use!")
        else:
            raise e1
    except Exception as e2:
        print(f"✗ mongoengine connection failed: {e2}")
        exit(1)

