#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Встановлюємо залежності (gunicorn, whitenoise тощо)
pip install -r requirements.txt

# 2. Збираємо статику (дизайн, світлу/темну тему)
python manage.py collectstatic --no-input

# 3. ІНТЕГРАЦІЯ БД: Django сам створює всі таблиці в порожній базі на Render
python manage.py migrate