#!/bin/bash
watchmedo auto-restart -d . -p "*.py;**/*.py" -R -- docker-compose up --build
