FROM python:3.11-slim
WORKDIR /app
# CPU-only torch keeps the image small; no model weights are baked in.
RUN pip install --no-cache-dir torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu
COPY service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY service/app.py service/schema.json ./
ENV MAX_NEW_TOKENS=64 PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
