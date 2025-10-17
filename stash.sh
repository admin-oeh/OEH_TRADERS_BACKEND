#!/bin/bash

# Wait a moment for the container to fully start
sleep 3

# Start the application
echo "Starting FastAPI application..."
exec uvicorn server:app --host 0.0.0.0 --port 8000 --access-log