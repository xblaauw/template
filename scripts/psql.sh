#!/bin/bash

# Get container ID of the postgres service
POSTGRES_CONTAINER=$(docker compose ps -q postgres)

if [ -z "$POSTGRES_CONTAINER" ]; then
    echo "Error: Postgres container is not running"
    exit 1
fi

# Connect to psql inside the container
docker exec -it $POSTGRES_CONTAINER psql -U postgres -d mydb
