# Use official Python image
FROM python:3.13-slim

# Set env variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working dir
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . .

# Default: Gunicorn for production-style entry
CMD ["gunicorn", "superkart.wsgi:application", "--bind", "0.0.0.0:8000"]

