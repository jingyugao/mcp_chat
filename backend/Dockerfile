FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*
RUN pip install uv fastapi uvicorn

ENV PATH="/app/.venv/bin:$PATH"

# 复制项目文件

COPY .env ./

COPY pyproject.toml uv.lock ./
COPY backend ./backend

# 使用uv安装Python依赖
RUN uv sync --python 3.10 --frozen --all-extras

# 设置环境变量
ENV PYTHONPATH=/app:$PYTHONPATH
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 14000

# 启动命令
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "14000", "--reload"] 