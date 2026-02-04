#!/bin/bash
# 測試執行腳本

set -e

echo "=========================================="
echo "WordPress Docker 環境測試"
echo "=========================================="

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查 Docker 是否運行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}錯誤: Docker 未運行${NC}"
    exit 1
fi

# 檢查 docker-compose 是否可用
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}錯誤: Docker Compose 未安裝${NC}"
    exit 1
fi

# 啟動服務
echo -e "${YELLOW}啟動 Docker 服務...${NC}"
docker-compose up -d || docker compose up -d

# 等待服務啟動
echo -e "${YELLOW}等待服務啟動（30秒）...${NC}"
sleep 30

# 檢查服務狀態
echo -e "${YELLOW}檢查服務狀態...${NC}"
docker-compose ps || docker compose ps

# 運行 Unit Tests
echo -e "${YELLOW}運行 Unit Tests...${NC}"
if [ -f "tests/unit/test_containers.py" ]; then
    python3 -m pytest tests/unit/test_containers.py -v || python3 -m unittest tests.unit.test_containers
else
    echo -e "${RED}Unit Test 檔案不存在${NC}"
fi

# 運行 E2E Tests
echo -e "${YELLOW}運行 E2E Tests...${NC}"
if [ -f "tests/e2e/test_wordpress.py" ]; then
    # 安裝依賴
    if [ -f "tests/requirements.txt" ]; then
        pip3 install -r tests/requirements.txt --quiet
    fi
    
    python3 -m pytest tests/e2e/test_wordpress.py -v || python3 -m unittest tests.e2e.test_wordpress
else
    echo -e "${RED}E2E Test 檔案不存在${NC}"
fi

echo -e "${GREEN}測試完成！${NC}"
