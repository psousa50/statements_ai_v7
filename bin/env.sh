#!/bin/bash
ROOT_DIR="$(git rev-parse --show-toplevel)"

export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:54321/bank_statements"
export TEST_DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:15432/bank_statements_test"
