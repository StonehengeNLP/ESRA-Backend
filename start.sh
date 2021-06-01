#!/bin/bash
python manage.py migrate
python manage.py search_index --rebuild -f 
gunicorn --bind 0.0.0.0:8000 --workers 8 backend.wsgi