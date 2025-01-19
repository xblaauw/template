#!/bin/bash

# Define variables for user IDs right at the start
CURRENT_UID=$(id -u)
CURRENT_GID=$(id -g)
export CURRENT_UID CURRENT_GID

source .env

SCHEMA_NAME=${POSTGRES_SCHEMA:-default_schema}

# Replace placeholder and output to a file
sed "s/{{POSTGRES_SCHEMA}}/$SCHEMA_NAME/g" postgres/init.template.sql > postgres/init.sql

docker compose down

# Cleaning artifacts...
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".eggs" -exec rm -rf {} + 2>/dev/null || true
rm -rf logs/* 2>/dev/null || true

# Parse arguments
DROP_DB=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --drop-db)
            DROP_DB=true
            shift
            ;;
        *)
            echo "Usage: $0 [--drop-db]"
            exit 1
            ;;
    esac
done

# Remove postgres volume if --drop-db is specified
if [ "$DROP_DB" = true ]; then
    echo "Removing postgres volume..."
    docker volume rm $(docker volume ls -q | grep postgres_data) 2>/dev/null || true
fi

echo "Rebuilding and starting containers..."
docker compose build
docker compose up -d

echo "Following docker compose logs..."
docker compose logs -f