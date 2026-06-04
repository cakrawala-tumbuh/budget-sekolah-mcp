# ── Stage: base ───────────────────────────────────────────────────────────────
# Runtime dependencies saja — digunakan sebagai dasar stage lainnya.
FROM python:3.11-slim AS base

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

RUN python -m pip install --no-cache-dir --upgrade pip setuptools>=68 wheel && \
    pip install --no-cache-dir .

# Catatan: automated test TIDAK lagi memakai stage di sini. Image test dibangun
# dari Dockerfile.test dan dijalankan via `make test` (lihat Makefile) agar
# lingkungan identik antara lokal dan CI.

# ── Stage: production ─────────────────────────────────────────────────────────
# Image ramping untuk deployment — tidak menyertakan test files.
FROM base AS production

ENV MCP_LOG_LEVEL=INFO

EXPOSE 9170

CMD ["uvicorn", "budget_sekolah_mcp.asgi:app", "--host", "0.0.0.0", "--port", "9170"]
