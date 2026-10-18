FROM python:3.12-slim
# Prevent Python from buffering stdout/stderr so print() logs appear immediately in docker logs
ENV PYTHONUNBUFFERED=1
WORKDIR /app
# Copy dependency list first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy the rest of the application code
COPY . .
CMD ["python", "main.py"]
