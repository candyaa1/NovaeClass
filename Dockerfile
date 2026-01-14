# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (helps with Docker caching)
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN python -m pip install --upgrade pip==25.3 \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port your app will run on
EXPOSE 8000

# Command to run the app using Gunicorn
# Replace 'myproject' with the actual folder containing wsgi.py
CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
