#!/bin/bash

docker volume create statements-ai-v7_postgres_data_backup
docker run --rm -v statements-ai-v7_postgres_data:/from -v statements-ai-v7_postgres_data_backup:/to alpine ash -c "cd /from && cp -a . /to"
docker rm bank-statements-db -f
docker volume rm statements-ai-v7_postgres_data
