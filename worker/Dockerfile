# Task 1 worker image for sharded teacher labelling.
FROM python:3.11-slim

WORKDIR /app

COPY worker/requirements*.txt ./
RUN if [ -f requirements.lock.txt ]; then \
      pip install --no-cache-dir -r requirements.lock.txt; \
    else pip install --no-cache-dir -r requirements.txt; fi

COPY worker/storage.py worker/label_worker.py worker/clean.py ./
COPY prompts/teacher_prompt.txt ./prompts/teacher_prompt.txt

ENV PROMPT_FILE=/app/prompts/teacher_prompt.txt \
    PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "label_worker.py"]
