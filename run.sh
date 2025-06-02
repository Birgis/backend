#!/bin/bash

# Ensure we're in the backend directory
cd "$(dirname "$0")"

# Remove old container if it exists
docker rm -f react-native-ui-backend 2>/dev/null || true

# Build the Docker image
docker build -t react-native-ui-backend .

# Create data directory if it doesn't exist
mkdir -p data

# Run the container
docker run -d \
    --name react-native-ui-backend \
    -p 8000:8000 \
    -v "$(pwd)/data:/app/data" \
    -e PYTHONPATH=/app \
    react-native-ui-backend

# Wait for the container to start
sleep 2

# Check if database exists
if [ -f "data/social.db" ]; then
    echo "Database exists, skipping migrations"
else
    # Run database migrations only if database doesn't exist
    if ! docker exec react-native-ui-backend alembic -c alembic.ini upgrade head; then
        echo "Failed to run database migrations"
        docker rm -f react-native-ui-backend
        exit 1
    fi
fi

# Seed the database
if ! docker exec react-native-ui-backend python seed.py; then
    echo "Failed to seed database"
    docker rm -f react-native-ui-backend
    exit 1
fi

# Check if the container is still running
if ! docker ps | grep -q react-native-ui-backend; then
    echo "Container failed to start"
    exit 1
fi

echo "Backend is running at http://localhost:8000" 