FROM python:3.11-slim
WORKDIR /app
COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY worker/teacher_worker.py worker/clean.py ./worker/
COPY prompts/teacher_prompt.txt ./prompts/teacher_prompt.txt
ENV PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 10001 worker && chown -R worker /app
USER 10001
CMD ["python", "worker/teacher_worker.py"]
