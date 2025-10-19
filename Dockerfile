FROM python:3.11-slim

ARG PYTORCH_INDEX_URL=""
ARG TARGETARCH

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

RUN set -eux; \
    if [ "${TARGETARCH}" = "amd64" ]; then \
        FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"; \
    elif [ "${TARGETARCH}" = "arm64" ]; then \
        FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz"; \
    else \
        echo "Unsupported TARGETARCH: ${TARGETARCH}" >&2; exit 1; \
    fi; \
    python - "$FFMPEG_URL" <<'PY'
import os
import stat
import sys
import tarfile
import tempfile
import urllib.request
import shutil

url = sys.argv[1]
with tempfile.TemporaryDirectory() as tmpdir:
    archive_path = os.path.join(tmpdir, "ffmpeg.tar.xz")
    urllib.request.urlretrieve(url, archive_path)
    with tarfile.open(archive_path, mode="r:xz") as tar:
        tar.extractall(tmpdir)
    extracted_dir = next(
        path
        for path in (os.path.join(tmpdir, name) for name in os.listdir(tmpdir))
        if os.path.isdir(path) and "ffmpeg" in os.path.basename(path)
    )
    for binary in ("ffmpeg", "ffprobe"):
        src = os.path.join(extracted_dir, binary)
        dst = os.path.join("/usr/local/bin", binary)
        shutil.move(src, dst)
        os.chmod(dst, os.stat(dst).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
PY

COPY requirements.txt .

RUN python -m pip install --upgrade pip \
    && if [ -n "$PYTORCH_INDEX_URL" ]; then \
        python -m pip install --extra-index-url "$PYTORCH_INDEX_URL" torch torchvision torchaudio; \
    fi \
    && python -m pip install -r requirements.txt

COPY . .
RUN python -m pip install --no-deps -e .

ENV PYTHONPATH=/app/src

EXPOSE 8080

CMD ["bash", "-lc", "streamlit run mobile_spa_app.py --server.address=0.0.0.0 --server.port=${PORT:-8080}"]
