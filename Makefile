.PHONY: logs-backend logs-frontend logs-all shell-backend

# 查看后端服务日志
logs-backend:
	docker compose logs -f backend

# 查看前端服务日志
logs-frontend:
	docker compose logs -f frontend

# 查看所有服务日志
logs-all:
	docker compose logs -f

# 进入后端服务shell
shell-backend:
	docker compose exec backend /bin/bash

# 显示帮助信息
help:
	@echo "可用的命令："
	@echo "  make logs-backend  - 查看后端服务日志"
	@echo "  make logs-frontend - 查看前端服务日志"
	@echo "  make logs-all      - 查看所有服务日志"
	@echo "  make shell-backend - 进入后端服务shell" 