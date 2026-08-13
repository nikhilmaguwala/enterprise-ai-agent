FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8101
RUN pip install --no-cache-dir "fastapi[standard]" uvicorn pydantic
COPY app ./app
EXPOSE 8101
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
