# Used by Hugging Face Spaces (Docker SDK), Fly.io, Koyeb, Cloud Run -- anywhere
# that takes a container. Hugging Face Spaces expects the app on port 7860.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860 \
    FLASK_DEBUG=0

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
