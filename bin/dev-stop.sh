#!/bin/bash
(lsof -ti :8000 | xargs kill -9; lsof -ti :5173 | xargs kill -9) 2>/dev/null || true
echo "Stopped dev servers"
