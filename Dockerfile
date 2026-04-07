# =============================================================
#  STAGE 1: Export dependencies from Poetry → requirements.txt
# =============================================================
#  WHY a separate stage?
#
#  This project uses Poetry for dependency management. Poetry
#  is great for development (lock files, dependency resolution,
#  virtual envs) but it's a 30MB tool that the production
#  container doesn't need. The standard pattern is:
#
#    1. Install Poetry in a throwaway stage
#    2. Use it to export a requirements.txt
#    3. Discard the stage — Poetry never enters the final image
#
#  This keeps the production image ~200MB smaller.
# =============================================================

FROM python:3.11-slim AS deps

    # ── Install Poetry ──────────────────────────────────
    # --no-cache-dir: don't store pip's download cache
    #   (this layer is throwaway, no point caching)
RUN pip install --no-cache-dir poetry==1.8.5

WORKDIR /build

    # ── Copy ONLY dependency files ──────────────────────
    # LAYER CACHING: Docker caches each layer. By copying
    # only pyproject.toml and poetry.lock BEFORE the code,
    # this expensive "export" step is cached as long as
    # dependencies don't change.
    #
    # If we did `COPY . .` here instead, ANY code change
    # (even a typo fix in heartbeat.py) would invalidate
    # this layer and re-run the export. That defeats the
    # purpose of caching.
COPY pyproject.toml poetry.lock ./

    # ── Export to requirements.txt ──────────────────────
    # --without-hashes: some pip versions choke on hashes
    #   in Docker builds (network vs cache conflicts)
    # --no-interaction: don't prompt for anything
    # --without dev: exclude pytest, black, mypy, etc.
    #   — dev tools don't belong in production images
RUN poetry export \
        --format requirements.txt \
        --output requirements.txt \
        --without-hashes \
        --without dev


# =============================================================
#  STAGE 2: Production runtime image
# =============================================================
#  This is the image that actually runs. It contains:
#    - Python 3.11 runtime (slim variant, ~120MB)
#    - Production Python packages (~80MB)
#    - Application code (~15KB)
#    - Trained model file (~700 bytes)
#    - curl for health checks (~5MB)
#  Total: ~200MB (vs ~800MB if we kept Poetry + dev deps)
#
#  What it does NOT contain:
#    - Poetry (30MB)
#    - Dev dependencies (pytest, black, mypy, etc.)
#    - Tests, docs, scripts
#    - .env file (secrets)
#    - .git directory
# =============================================================

FROM python:3.11-slim AS production

    # ── OS dependencies ────────────────────────────────
    # curl: needed for HEALTHCHECK (Docker calls this
    #   command to verify the container is healthy)
    # --no-install-recommends: skip suggested packages
    # rm -rf /var/lib/apt/lists/*: delete the package
    #   index after install — saves ~30MB in the image
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

    # ── Non-root user ──────────────────────────────────
    # SECURITY: Never run production containers as root.
    # If the application gets compromised (e.g. through
    # a deserialization bug in the ML model), the attacker
    # only has the privileges of 'appuser' — they can't
    # install packages, modify system files, or escalate.
    #
    # GID/UID 1001: avoids collision with system users
    # (root=0, nobody=65534, typical system range 100-999)
RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup --create-home appuser

    # ── Working directory ──────────────────────────────
WORKDIR /app

    # ── Install Python dependencies ────────────────────
    # COPY --from=deps: this is the multi-stage bridge.
    # We reach into Stage 1's filesystem and grab ONLY
    # the requirements.txt that Poetry exported. Stage 1
    # itself (with Poetry installed) is discarded.
    #
    # LAYER CACHING: requirements.txt is copied before
    # the application code. As long as dependencies don't
    # change, this `pip install` layer stays cached even
    # when you edit Python source files.
COPY --from=deps /build/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

    # ── Copy model file ────────────────────────────────
    # The trained model is baked INTO the image. This is
    # the production pattern because:
    #   1. No network dependency at startup (HuggingFace
    #      Hub down? Doesn't matter.)
    #   2. Reproducible — the exact model version is
    #      locked to the image tag
    #   3. Fast startup — no download step
    #
    # For this project the model is 696 bytes (tiny).
    # For larger models (100MB+), you'd use a volume mount
    # or download from S3/GCS at startup instead.
COPY sample_model/ ./sample_model/

    # ── Copy application code ──────────────────────────
    # This is LAST because code changes most frequently.
    # Every layer above this stays cached across code edits.
    #
    # Layer caching order (most stable → least stable):
    #   1. Base image (python:3.11-slim)     — months
    #   2. OS packages (curl)                — months
    #   3. Python deps (requirements.txt)    — weeks
    #   4. Model file (.joblib)              — days/weeks
    #   5. Application code                  — every commit
COPY fastapi_skeleton/ ./fastapi_skeleton/

    # ── Fix ownership ──────────────────────────────────
    # Everything was copied as root (COPY runs as root).
    # Transfer ownership to appuser so the process can
    # read all files it needs.
RUN chown -R appuser:appgroup /app

    # ── Switch to non-root user ────────────────────────
    # From this point on, all commands (including CMD)
    # run as appuser.
USER appuser

    # ── Environment variables ──────────────────────────
    # PYTHONUNBUFFERED=1: Python prints to stdout/stderr
    #   immediately instead of buffering. Essential for
    #   Docker because without it, logs are delayed or
    #   lost when the container stops.
    #
    # PYTHONDONTWRITEBYTECODE=1: Don't create __pycache__
    #   directories. The container filesystem is ephemeral
    #   — caching .pyc files wastes space for no benefit.
    #
    # DEFAULT_MODEL_PATH: tells our app where the baked-in
    #   model lives. This matches the COPY destination above.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEFAULT_MODEL_PATH=./sample_model/lin_reg_california_housing_model.joblib

    # ── Expose port ────────────────────────────────────
    # EXPOSE is documentation, not enforcement. It tells
    # humans and tools "this container listens on 8000".
    # You still need -p 8000:8000 when running the container.
EXPOSE 8000

    # ── Health check ───────────────────────────────────
    # Docker calls this command periodically to check if
    # the container is healthy. If it fails `retries` times
    # in a row, Docker marks the container as "unhealthy".
    #
    # --interval=30s:       check every 30 seconds
    # --timeout=5s:         give the check 5s to respond
    # --start-period=10s:   grace period after startup
    #   (the app needs a few seconds to load the model;
    #    this is only 10s because our model is tiny —
    #    for a large model, set this to 60-120s)
    # --retries=3:          3 failures = unhealthy
    #
    # /api/health/heartbeat: this is the actual endpoint
    #   our FastAPI app exposes — it checks if the model
    #   is loaded and returns 200 or 503.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/heartbeat || exit 1

    # ── Start command ──────────────────────────────────
    # Single worker (default) because the ML model lives
    # in-process memory. Multiple workers = multiple copies
    # of the model = 2x/3x/4x memory usage.
    #
    # Scale horizontally (more containers) not vertically
    # (more workers per container).
    #
    # --host 0.0.0.0: listen on all interfaces so Docker's
    #   port mapping can reach the process. localhost would
    #   only be reachable from inside the container.
CMD ["uvicorn", "fastapi_skeleton.main:app", "--host", "0.0.0.0", "--port", "8000"]
