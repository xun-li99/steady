FROM python:3.11-slim
WORKDIR /app
COPY . .
EXPOSE 8100
ENV STEADY_DIR=/app/.steady
ENV STEADY_PORT=8100
CMD ["python", "steady_api.py"]
