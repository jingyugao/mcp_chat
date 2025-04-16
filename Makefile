.PHONY: logs-backend logs-frontend logs-all shell-backend rebuild rebuild-backend rebuild-frontend restart restart-backend restart-frontend

# 查看后端服务日志
logsbe:
	docker compose logs -f backend

# 查看前端服务日志
logsfe:
	docker compose logs -f frontend

# 查看所有服务日志
logs-all:
	docker compose logs -f

# 进入后端服务shell
shbe:
	docker compose exec backend /bin/bash

shfe:
	docker compose exec frontend /bin/bash

refe:
	docker compose build frontend
	docker compose up -d frontend

rebe:
	docker compose build backend
	docker compose up -d backend

reall:
	make rebe
	make refe

# 显示帮助信息
help:
	@echo "可用的命令："
	@echo "  make logsbe          - 查看后端服务日志"
	@echo "  make logsfe          - 查看前端服务日志"
	@echo "  make logsall         - 查看所有服务日志"
	@echo "  make shbe            - 进入后端服务shell"
	@echo "  make shfe            - 进入前端服务shell"
	@echo "  make rebe            - 重新构建后端服务"
	@echo "  make reall           - 重新构建所有服务"
