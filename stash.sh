#!/bin/bash

# Wait for network to be ready
sleep 5

# Start the application
echo "Starting FastAPI application..."
exec uvicorn server:app --host 0.0.0.0 --port 8000 --access-log