# WordPress Docker 環境故障排除指南

## 目錄

1. [服務無法啟動](#服務無法啟動)
2. [WordPress 無法訪問](#wordpress-無法訪問)
3. [資料庫連接問題](#資料庫連接問題)
4. [檔案權限問題](#檔案權限問題)
5. [性能問題](#性能問題)
6. [日誌查看](#日誌查看)
7. [常見錯誤訊息](#常見錯誤訊息)

## 服務無法啟動

### 檢查 Docker 狀態

```bash
# 檢查 Docker 是否運行
docker info

# 如果失敗，啟動 Docker
# macOS/Windows: 啟動 Docker Desktop
# Linux:
sudo systemctl start docker
```

### 檢查端口佔用

```bash
# 檢查 80 端口是否被佔用
# macOS/Linux:
lsof -i :80

# Windows:
netstat -ano | findstr :80

# 如果端口被佔用，可以：
# 1. 停止佔用端口的程序
# 2. 或修改 .env 檔案中的 NGINX_HTTP_PORT
```

### 檢查磁碟空間

```bash
# 檢查可用空間
df -h

# 清理未使用的 Docker 資源
docker system prune -a
```

### 檢查記憶體

```bash
# 檢查可用記憶體
free -h

# Docker Desktop: Settings > Resources > 增加記憶體限制
```

## WordPress 無法訪問

### 檢查服務狀態

```bash
# 查看所有服務狀態
docker-compose ps

# 應該看到所有服務都是 "Up" 狀態
```

### 檢查 Nginx 配置

```bash
# 測試 Nginx 配置語法
docker-compose exec nginx nginx -t

# 如果配置錯誤，檢查配置檔案
cat config/nginx/default.conf
```

### 檢查健康端點

```bash
# 測試 Nginx 健康檢查
curl http://localhost/health

# 應該返回 "healthy"
```

### 檢查防火牆

```bash
# Linux: 檢查防火牆規則
sudo ufw status
sudo iptables -L

# 如果需要，允許 80 端口
sudo ufw allow 80/tcp
```

## 資料庫連接問題

### 檢查資料庫容器

```bash
# 檢查資料庫容器狀態
docker-compose ps db

# 查看資料庫日誌
docker-compose logs db
```

### 測試資料庫連接

```bash
# 進入資料庫容器
docker-compose exec db bash

# 連接資料庫
mysql -u wordpress -p
# 輸入 .env 檔案中的 MYSQL_PASSWORD
```

### 檢查環境變數

```bash
# 檢查 WordPress 環境變數
docker-compose exec wordpress env | grep WORDPRESS

# 應該看到：
# WORDPRESS_DB_HOST=db:3306
# WORDPRESS_DB_USER=wordpress
# WORDPRESS_DB_PASSWORD=<your_password>
# WORDPRESS_DB_NAME=wordpress
```

### 檢查資料庫初始化

```bash
# 檢查資料庫是否存在
docker-compose exec db mysql -u root -p -e "SHOW DATABASES;"

# 檢查用戶權限
docker-compose exec db mysql -u root -p -e "SELECT User, Host FROM mysql.user;"
```

### 重新初始化資料庫

如果資料庫配置有問題，可以重新初始化：

```bash
# 停止服務
docker-compose down

# 移除資料庫 Volume（**警告：會刪除所有資料**）
docker volume rm wp-template_db_data

# 重新啟動
docker-compose up -d
```

## 檔案權限問題

### 檢查檔案權限

```bash
# 檢查 WordPress 檔案權限
docker-compose exec wordpress ls -la /var/www/html

# 應該看到檔案屬於 www-data:www-data (33:33)
```

### 修復檔案權限

```bash
# 修復 WordPress 檔案權限
docker-compose exec wordpress chown -R www-data:www-data /var/www/html
docker-compose exec wordpress chmod -R 755 /var/www/html
docker-compose exec wordpress chmod -R 775 /var/www/html/wp-content
```

### 檢查 Volume 掛載

```bash
# 檢查 Volume 是否正確掛載
docker-compose exec wordpress df -h /var/www/html

# 檢查 Volume 列表
docker volume ls
```

## 性能問題

### 檢查資源使用

```bash
# 查看容器資源使用情況
docker stats

# 查看特定服務的資源使用
docker stats wordpress_app wordpress_db wordpress_nginx
```

### 優化配置

1. **增加 PHP 記憶體限制**：
編輯 `config/php/php.ini`：
```ini
memory_limit = 512M
```

2. **優化 MySQL 配置**：
可以添加 MySQL 配置檔案到 `config/mysql/my.cnf`

3. **啟用 OPcache**：
確保 `config/php/php.ini` 中 OPcache 已啟用

### 清理快取

```bash
# 清理 WordPress 快取（如果使用快取插件）
docker-compose exec wordpress wp cache flush

# 清理 Docker 快取
docker system prune
```

## 日誌查看

### 查看所有服務日誌

```bash
# 查看所有日誌
docker-compose logs

# 查看最近 100 行
docker-compose logs --tail=100

# 即時查看日誌
docker-compose logs -f
```

### 查看特定服務日誌

```bash
# Nginx 日誌
docker-compose logs nginx

# WordPress 日誌
docker-compose logs wordpress

# 資料庫日誌
docker-compose logs db
```

### 查看容器內部日誌

```bash
# 進入容器查看日誌
docker-compose exec nginx cat /var/log/nginx/error.log
docker-compose exec wordpress cat /var/log/php_errors.log
```

## 常見錯誤訊息

### 錯誤 1: "Cannot connect to the Docker daemon"

**原因**：Docker 服務未運行

**解決方法**：
```bash
# macOS/Windows: 啟動 Docker Desktop
# Linux:
sudo systemctl start docker
```

### 錯誤 2: "bind: address already in use"

**原因**：端口已被佔用

**解決方法**：
```bash
# 查找佔用端口的程序
lsof -i :80

# 停止程序或更改端口
# 編輯 .env 檔案：NGINX_HTTP_PORT=8080
```

### 錯誤 3: "Error response from daemon: driver failed programming external connectivity"

**原因**：Docker 網路配置問題

**解決方法**：
```bash
# 重啟 Docker 服務
sudo systemctl restart docker

# 或重新創建網路
docker network prune
docker-compose up -d
```

### 錯誤 4: "Access denied for user 'wordpress'@'172.x.x.x'"

**原因**：資料庫用戶權限問題

**解決方法**：
```bash
# 重新設置用戶權限
docker-compose exec db mysql -u root -p
# 在 MySQL 中執行：
GRANT ALL PRIVILEGES ON wordpress.* TO 'wordpress'@'%';
FLUSH PRIVILEGES;
```

### 錯誤 5: "PHP Fatal error: Allowed memory size exhausted"

**原因**：PHP 記憶體限制不足

**解決方法**：
編輯 `config/php/php.ini`：
```ini
memory_limit = 512M
```
然後重啟服務：
```bash
docker-compose restart wordpress
```

### 錯誤 6: "502 Bad Gateway"

**原因**：PHP-FPM 無法連接或配置錯誤

**解決方法**：
```bash
# 檢查 PHP-FPM 是否運行
docker-compose exec wordpress ps aux | grep php-fpm

# 檢查 Nginx 配置中的 upstream
docker-compose exec nginx cat /etc/nginx/conf.d/default.conf | grep upstream

# 重啟服務
docker-compose restart wordpress nginx
```

## 進階故障排除

### 完全重置環境

如果遇到無法解決的問題，可以完全重置：

```bash
# 停止所有服務
docker-compose down

# 移除所有容器、網路和 Volume
docker-compose down -v

# 清理未使用的資源
docker system prune -a

# 重新啟動
docker-compose up -d
```

### 檢查 Docker Compose 配置

```bash
# 驗證配置檔案語法
docker-compose config

# 查看解析後的配置
docker-compose config > docker-compose.resolved.yml
```

### 調試模式

啟用詳細日誌：

```bash
# 使用詳細模式啟動
docker-compose up --verbose

# 或查看詳細日誌
docker-compose logs --details
```

## 獲取幫助

如果以上方法都無法解決問題：

1. **查看完整日誌**：
```bash
docker-compose logs > debug.log
```

2. **檢查系統資訊**：
```bash
docker info
docker-compose version
```

3. **提交 Issue**：包含以下資訊：
   - 錯誤訊息
   - 日誌檔案
   - 系統資訊
   - 重現步驟

## 參考資源

- [Docker 故障排除指南](https://docs.docker.com/config/troubleshooting/)
- [WordPress 故障排除](https://wordpress.org/documentation/article/faq-troubleshooting/)
- [Nginx 故障排除](https://nginx.org/en/docs/http/ngx_core_module.html#error_log)
