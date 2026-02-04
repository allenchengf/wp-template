.PHONY: help up down restart logs ps test clean

help: ## 顯示幫助訊息
	@echo "WordPress Docker 環境管理命令"
	@echo ""
	@echo "可用命令："
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

up: ## 啟動所有服務
	docker-compose up -d || docker compose up -d

down: ## 停止所有服務
	docker-compose down || docker compose down

restart: ## 重啟所有服務
	docker-compose restart || docker compose restart

logs: ## 查看所有服務日誌
	docker-compose logs -f || docker compose logs -f

ps: ## 查看服務狀態
	docker-compose ps || docker compose ps

test: ## 運行所有測試
	./tests/run_tests.sh

test-unit: ## 運行 Unit Tests
	python3 -m pytest tests/unit/ -v || python3 -m unittest tests.unit.test_containers

test-e2e: ## 運行 E2E Tests
	pip3 install -q -r tests/requirements.txt
	python3 -m pytest tests/e2e/ -v || python3 -m unittest tests.e2e.test_wordpress

clean: ## 清理所有容器和 Volume（警告：會刪除所有資料）
	docker-compose down -v || docker compose down -v

clean-all: clean ## 完全清理（包括映像）
	docker system prune -a -f

shell-wordpress: ## 進入 WordPress 容器
	docker-compose exec wordpress sh || docker compose exec wordpress sh

shell-db: ## 進入 MySQL 容器
	docker-compose exec db bash || docker compose exec db bash

shell-nginx: ## 進入 Nginx 容器
	docker-compose exec nginx sh || docker compose exec nginx sh

db-backup: ## 備份資料庫
	docker-compose exec db mysqldump -u wordpress -p$(shell grep MYSQL_PASSWORD .env | cut -d '=' -f2) wordpress > backup_$$(date +%Y%m%d_%H%M%S).sql || docker compose exec db mysqldump -u wordpress -p$(shell grep MYSQL_PASSWORD .env | cut -d '=' -f2) wordpress > backup_$$(date +%Y%m%d_%H%M%S).sql
