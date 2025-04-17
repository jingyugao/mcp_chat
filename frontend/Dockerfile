FROM node:18-slim

WORKDIR /app

# 复制package.json和package-lock.json
COPY frontend/package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY frontend/ .

# 构建应用
RUN npm run build

# 安装serve用于生产环境服务
RUN npm install -g serve

# 暴露端口
EXPOSE 3000

# 启动命令
CMD ["npm", "run", "serve", "--", "--host", "0.0.0.0", "--port", "3000"]
# CMD ["serve", "-s", "dist", "-l", "3000"] 