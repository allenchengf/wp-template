# WordPress Docker 環境安裝指南

## 系統需求

### 最低需求

- **作業系統**: Linux, macOS, 或 Windows (支援 WSL2)
- **Docker**: >= 20.10
- **Docker Compose**: >= 2.0
- **記憶體**: 2GB RAM
- **磁碟空間**: 5GB 可用空間
- **CPU**: 2 核心

### 推薦配置

- **記憶體**: 4GB RAM 或更多
- **磁碟空間**: 10GB 可用空間
- **CPU**: 4 核心或更多

## 安裝步驟

### 步驟 1: 安裝 Docker

#### macOS

1. 下載 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
2. 安裝並啟動 Docker Desktop
3. 驗證安裝：
```bash
docker --version
docker-compose --version
```

#### Linux (Ubuntu/Debian)

```bash
# 更新套件列表
sudo apt-get update

# 安裝必要套件
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加 Docker 官方 GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 設置 repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安裝 Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 啟動 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 驗證安裝
sudo docker --version
sudo docker compose version
```

#### Windows

1. 安裝 [WSL2](https://docs.microsoft.com/windows/wsl/install)
2. 下載 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
3. 安裝並啟動 Docker Desktop
4. 驗證安裝：
```bash
docker --version
docker-compose --version
```

### 步驟 2: 克隆或下載專案

```bash
# 如果使用 Git
git clone <repository-url>
cd wp-template

# 或直接下載並解壓縮專案檔案
```

### 步驟 3: 配置環境變數

1. 複製環境變數範例檔案：
```bash
cp env.example .env
```

2. 編輯 `.env` 檔案，設置安全密碼：
```bash
# 使用文字編輯器打開 .env 檔案
nano .env
# 或
vim .env
```

3. 修改以下變數（**務必更改預設值**）：
```env
MYSQL_ROOT_PASSWORD=your_secure_root_password_here
MYSQL_PASSWORD=your_secure_password_here
```

**安全建議**：
- 使用至少 16 個字符的強密碼
- 包含大小寫字母、數字和特殊字符
- 不要使用常見的密碼

### 步驟 4: 啟動服務

```bash
# 使用 Docker Compose V1
docker-compose up -d

# 或使用 Docker Compose V2
docker compose up -d
```

`-d` 參數表示在背景執行。

### 步驟 5: 等待服務啟動

服務啟動需要一些時間（約 30-60 秒）。可以使用以下命令檢查狀態：

```bash
# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f
```

當所有服務狀態顯示為 "Up" 或 "healthy" 時，表示服務已成功啟動。

### 步驟 6: 訪問 WordPress

1. 打開瀏覽器
2. 訪問：`http://localhost`
3. 您應該看到 WordPress 安裝頁面

### 步驟 7: 完成 WordPress 安裝

1. 選擇語言
2. 填寫網站資訊：
   - 網站標題
   - 管理員用戶名
   - 管理員密碼
   - 管理員電子郵件
3. 點擊「安裝 WordPress」
4. 安裝完成後，使用設置的管理員帳號登入

## 驗證安裝

### 檢查服務狀態

```bash
docker-compose ps
```

所有服務應該顯示為 "Up" 狀態。

### 運行測試

```bash
# 運行所有測試
./tests/run_tests.sh

# 或分別運行
python3 -m pytest tests/unit/ -v
python3 -m pytest tests/e2e/ -v
```

### 手動驗證

1. **檢查 Nginx**：
```bash
curl http://localhost/health
```
應該返回 "healthy"

2. **檢查 WordPress**：
```bash
curl http://localhost
```
應該返回 WordPress HTML 內容

3. **檢查資料庫**：
```bash
docker-compose exec db mysql -u wordpress -p -e "SHOW DATABASES;"
```
輸入 `.env` 檔案中的 `MYSQL_PASSWORD`

## 常見問題

### 問題 1: 端口已被佔用

**錯誤訊息**：
```
Error: bind: address already in use
```

**解決方法**：
1. 檢查哪個程序佔用了端口：
```bash
# macOS/Linux
lsof -i :80

# Windows
netstat -ano | findstr :80
```

2. 停止佔用端口的程序，或修改 `.env` 檔案中的 `NGINX_HTTP_PORT`

### 問題 2: 權限錯誤

**錯誤訊息**：
```
Permission denied
```

**解決方法**：
```bash
# Linux: 將用戶添加到 docker 群組
sudo usermod -aG docker $USER
newgrp docker

# macOS/Windows: 確保 Docker Desktop 正在運行
```

### 問題 3: 記憶體不足

**錯誤訊息**：
```
Cannot allocate memory
```

**解決方法**：
1. 增加 Docker 記憶體限制（Docker Desktop > Settings > Resources）
2. 關閉其他應用程式釋放記憶體
3. 減少 Docker Compose 中的資源限制

### 問題 4: WordPress 無法連接資料庫

**解決方法**：
1. 檢查資料庫容器是否運行：
```bash
docker-compose ps db
```

2. 檢查環境變數：
```bash
docker-compose exec wordpress env | grep WORDPRESS
```

3. 測試資料庫連接：
```bash
docker-compose exec db mysql -u wordpress -p
```

4. 檢查資料庫日誌：
```bash
docker-compose logs db
```

## 下一步

安裝完成後，您可以：

1. **自訂 WordPress 主題和插件**
2. **配置 SSL/TLS 證書**（生產環境）
3. **設置備份策略**
4. **優化性能配置**
5. **閱讀 [故障排除指南](TROUBLESHOOTING.md)**

## 卸載

如果需要完全移除環境：

```bash
# 停止並移除容器
docker-compose down

# 移除 Volume（**警告：這會刪除所有資料**）
docker-compose down -v

# 移除映像（可選）
docker rmi wordpress:6.4-php8.2-fpm-alpine
docker rmi mysql:8.0
docker rmi nginx:1.26-alpine
```

## 參考資源

- [Docker 官方文檔](https://docs.docker.com/)
- [Docker Compose 官方文檔](https://docs.docker.com/compose/)
- [WordPress 官方文檔](https://wordpress.org/documentation/)
- [Nginx 官方文檔](https://nginx.org/en/docs/)
