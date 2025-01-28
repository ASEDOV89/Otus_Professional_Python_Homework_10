#!/bin/sh

python wait_for_db.py db 5432

python migrations/init_db.py

uvicorn main:app --host 0.0.0.0 --port 8000