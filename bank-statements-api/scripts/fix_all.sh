#!/bin/bash

isort .
black .
ruff check . --fix
