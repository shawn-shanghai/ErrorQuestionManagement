FROM python:3.11-slim

WORKDIR /app

RUN echo "deb https://mirrors.aliyun.com/debian trixie main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian trixie-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian-security trixie-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list
 
# System deps for PaddleOCR and Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxrender1 libxext6 libgl1 curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY app ./app
RUN pip install --no-cache-dir -e .

# Pre-download PaddleOCR model at build time (avoid cold start)
RUN python -c "from paddleocr import PaddleOCR; PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)"

COPY . .

# Run Alembic migrations then start server
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
