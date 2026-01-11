# Dockerfile (Place in Root Folder)
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Expose port
EXPOSE 8000

# Default command: Run Migrations -> Collect Static -> Start Gunicorn
# Note: We use --chdir testapp because wsgi.py is inside testapp/testapp/
CMD ["sh", "-c", "python testapp/manage.py migrate && python testapp/manage.py collectstatic --noinput && gunicorn --chdir testapp testapp.wsgi:application --bind 0.0.0.0:8000"]