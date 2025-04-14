FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# 安装uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# 复制项目文件
COPY requirements.txt pyproject.toml ./
COPY backend ./backend

# 使用uv安装Python依赖
RUN /root/.cargo/bin/uv pip install --no-cache -r requirements.txt

# 设置环境变量
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 14000

# 启动命令
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "14000"] 