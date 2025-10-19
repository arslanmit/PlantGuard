FROM python:3.11-slim

ARG PYTORCH_INDEX_URL=""

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    TMPDIR=/var/tmp

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --upgrade pip \
    && python -m pip install imageio-ffmpeg \
    && if [ -n "$PYTORCH_INDEX_URL" ]; then \
        python -m pip install --extra-index-url "$PYTORCH_INDEX_URL" torch torchvision torchaudio; \
    fi \
    && python -m pip install -r requirements.txt

RUN python - <<'PY'
import os
import shutil
import stat

import imageio_ffmpeg

ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
target_path = "/usr/local/bin/ffmpeg"
shutil.copy2(ffmpeg_path, target_path)
os.chmod(target_path, os.stat(target_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
PY

COPY . .
RUN python -m pip install --no-deps -e .

ENV PYTHONPATH=/app/src

EXPOSE 8080

CMD ["bash", "-lc", "streamlit run mobile_spa_app.py --server.address=0.0.0.0 --server.port=${PORT:-8080}"]
