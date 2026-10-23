FROM python:3.12-slim AS dependencies
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
COPY backend/requirements.txt requirements.txt
RUN pip install --prefix=/install -r requirements.txt

FROM python:3.12-slim AS model
COPY --from=dependencies /install /usr/local
WORKDIR /build
COPY backend backend
COPY scripts scripts
COPY data/fixtures/corpus.jsonl data/fixtures/corpus.jsonl
RUN python -m scripts.build_index --cache /opt/models

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    EMBEDDING_CACHE=/opt/models RETRIEVAL_MODE=hybrid \
    HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY --from=dependencies /install /usr/local
COPY --from=model /opt/models /opt/models
COPY --chown=app:app backend backend
COPY --chown=app:app scripts scripts
COPY --from=model --chown=app:app /build/data/fixtures data/fixtures
RUN mkdir -p data/private && chown app:app data/private
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/healthz', timeout=4)"
CMD ["python", "-m", "scripts.start"]
