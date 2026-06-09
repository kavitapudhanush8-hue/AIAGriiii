# ── Build context is the project ROOT (d:/AGENTAI/) ──────────────────────────
# render.yaml sets dockerContext: . so all folders are available here.
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source into /app/
COPY backend/ ./

# Copy frontend into explicit absolute path inside container
# main.py resolves: /app/app/../../frontend-web = /frontend-web
COPY frontend-web/ /frontend-web/

# Copy AI model files into explicit absolute path
# main.py resolves: /app/app/../../ai-model = /ai-model
COPY ai-model/ /ai-model/

# Expose and run
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
