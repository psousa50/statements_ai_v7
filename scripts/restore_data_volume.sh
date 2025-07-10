#!/bin/bash

# Restore the postgres data volume from backup
docker volume create statements-ai-v7_postgres_data
docker run --rm -v statements-ai-v7_postgres_data_backup:/from -v statements-ai-v7_postgres_data:/to alpine ash -c "cd /from && cp -a . /to"