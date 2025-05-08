#!/bin/bash

# Check if PostgreSQL is running
echo "Checking if PostgreSQL is running..."
if ! pg_isready -h localhost -p 5432 -U postgres > /dev/null 2>&1; then
    echo "Starting PostgreSQL service..."
    sudo service postgresql start
    sleep 5
else
    echo "PostgreSQL is already running."
fi

# Check if Redis is running
echo "Checking if Redis is running..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Starting Redis using Docker..."
    docker run --name neurospark-redis-local -p 6379:6379 -d redis:7-alpine redis-server --requirepass redis_password
    sleep 5
else
    echo "Redis is already running."
fi

# Set environment variables for local development
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres_password
export POSTGRES_DB=neurospark

export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=redis_password
export REDIS_URL=redis://:redis_password@localhost:6379/0

# External API settings
export OPENAI_API_KEY=$(grep OPENAI_API_KEY /home/jt/neurospark-core/.env | cut -d '=' -f2)
export SERPAPI_API_KEY=$(grep SERPAPI_API_KEY /home/jt/neurospark-core/.env | cut -d '=' -f2)
export NEWSAPI_API_KEY=$(grep NEWSAPI_API_KEY /home/jt/neurospark-core/.env | cut -d '=' -f2 || echo "")
export OPENALEX_API_KEY=$(grep OPENALEX_API_KEY /home/jt/neurospark-core/.env | cut -d '=' -f2 || echo "")

# Run the Curator Agent with a timeout
echo "Starting Curator Agent..."
timeout 120 python -m src.agents.curator.main &
CURATOR_PID=$!

# Wait for the Curator Agent to finish or timeout
wait $CURATOR_PID
CURATOR_EXIT_CODE=$?

if [ $CURATOR_EXIT_CODE -eq 124 ]; then
    echo "Curator Agent timed out after 120 seconds, but this is expected for a long-running process."
    echo "Killing the process..."
    kill -9 $CURATOR_PID 2>/dev/null || true
elif [ $CURATOR_EXIT_CODE -ne 0 ]; then
    echo "Curator Agent exited with code $CURATOR_EXIT_CODE"
else
    echo "Curator Agent completed successfully"
fi

# Note: We're not stopping PostgreSQL as it might be used by other applications
# But we can stop the Redis container if we started it
if [ "$(docker ps -q -f name=neurospark-redis-local)" ]; then
    echo "Stopping Redis container..."
    docker stop neurospark-redis-local
    docker rm neurospark-redis-local
fi

echo "Curator Agent run completed."
