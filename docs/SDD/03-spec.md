# WordPress 網站架設專案 - Specification（技術規格）

## 版本規格

### 組件版本要求

| 組件 | 版本要求 | 具體版本 | 備註 |
|------|----------|----------|------|
| Docker | >= 20.10 | 最新穩定版 | 支援 Docker Compose V2 |
| Docker Compose | >= 2.0 | 最新穩定版 | 使用 Compose V2 語法 |
| Nginx | LTS | 1.26.x | 最新 LTS 版本 |
| PHP | LTS | 8.2.x | WordPress 推薦版本 |
| MySQL | LTS | 8.0.x | 最新 LTS 版本 |
| WordPress | LTS | 6.4.x | 最新穩定版本 |

### 版本相容性矩陣

```
WordPress 6.4.x
├── PHP 8.2.x (推薦)
├── PHP 8.1.x (支援)
└── PHP 8.0.x (支援)

MySQL 8.0.x
├── 支援所有 WordPress 版本
└── 字符集：utf8mb4
```

## Docker Compose 規格

### 服務定義

#### 1. Nginx 服務
```yaml
服務名稱: nginx
鏡像: nginx:1.26-alpine
端口映射:
  - 80:80 (HTTP)
  - 443:443 (HTTPS，可選)
依賴服務:
  - wordpress
Volume 掛載:
  - ./config/nginx/nginx.conf:/etc/nginx/nginx.conf
  - ./config/nginx/default.conf:/etc/nginx/conf.d/default.conf
  - ./wp_data:/var/www/html:ro
網路: wordpress-network
重啟策略: unless-stopped
```

#### 2. WordPress 服務
```yaml
服務名稱: wordpress
鏡像: wordpress:6.4-php8.2-fpm-alpine
依賴服務:
  - db
環境變數:
  WORDPRESS_DB_HOST: db:3306
  WORDPRESS_DB_USER: wordpress
  WORDPRESS_DB_PASSWORD: ${MYSQL_PASSWORD}
  WORDPRESS_DB_NAME: wordpress
  WORDPRESS_TABLE_PREFIX: wp_
Volume 掛載:
  - ./wp_data:/var/www/html
網路: wordpress-network
重啟策略: unless-stopped
```

#### 3. MySQL 服務
```yaml
服務名稱: db
鏡像: mysql:8.0
端口映射:
  - 3306:3306 (僅開發環境，生產環境不暴露)
環境變數:
  MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
  MYSQL_DATABASE: wordpress
  MYSQL_USER: wordpress
  MYSQL_PASSWORD: ${MYSQL_PASSWORD}
Volume 掛載:
  - ./db_data:/var/lib/mysql
  - ./config/mysql/init:/docker-entrypoint-initdb.d
網路: wordpress-network
重啟策略: unless-stopped
```

### 網路配置
```yaml
網路名稱: wordpress-network
驅動: bridge
```

### Volume 配置
```yaml
Volumes:
  - wp_data: WordPress 檔案資料
  - db_data: MySQL 資料庫資料
```

## Nginx 配置規格

### 基本配置要求
- 反向代理到 PHP-FPM（wordpress:9000）
- 支援 PHP 檔案處理
- 靜態檔案直接服務
- 啟用 Gzip 壓縮
- 設定適當的緩存策略
- 安全標頭配置

### 關鍵配置項
```nginx
upstream php {
    server wordpress:9000;
}

server {
    listen 80;
    server_name localhost;
    root /var/www/html;
    index index.php index.html;
    
    # PHP 處理
    location ~ \.php$ {
        fastcgi_pass php;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }
    
    # 靜態檔案
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## PHP 配置規格

### PHP-FPM 配置要求
- Pool 名稱：www
- 監聽：9000 端口
- 進程管理：dynamic
- 最大子進程數：根據資源調整
- 請求超時：300 秒

### PHP 擴展要求
WordPress 必需擴展：
- mysqli
- pdo_mysql
- gd
- zip
- curl
- mbstring
- xml
- exif
- imagick (可選)

### PHP 配置參數
```ini
memory_limit = 256M
upload_max_filesize = 64M
post_max_size = 64M
max_execution_time = 300
max_input_time = 300
```

## MySQL 配置規格

### 資料庫初始化
- 字符集：utf8mb4
- 排序規則：utf8mb4_unicode_ci
- 預設資料庫：wordpress
- 用戶權限：僅授予必要權限

### 性能配置
```ini
innodb_buffer_pool_size = 256M
max_connections = 100
query_cache_type = 1
query_cache_size = 32M
```

## WordPress 配置規格

### 安裝要求
- 使用官方 WordPress 鏡像
- 透過環境變數配置資料庫連接
- 支援自動安裝（wp-config.php 自動生成）
- 檔案權限：www-data:www-data (33:33)

### 環境變數規格
```bash
WORDPRESS_DB_HOST=db:3306
WORDPRESS_DB_USER=wordpress
WORDPRESS_DB_PASSWORD=<secure_password>
WORDPRESS_DB_NAME=wordpress
WORDPRESS_TABLE_PREFIX=wp_
```

### 檔案結構
```
wp_data/
├── wp-admin/
├── wp-includes/
├── wp-content/
│   ├── themes/
│   ├── plugins/
│   └── uploads/
├── wp-config.php
└── index.php
```

## 安全規格

### 資料庫安全
- Root 密碼：使用強密碼（至少 16 字符）
- 應用用戶：僅授予必要權限
- 不暴露 3306 端口到主機（生產環境）

### 網路安全
- 使用 Docker 內部網路
- 僅暴露必要端口（80）
- 實施防火牆規則（生產環境）

### 檔案安全
- 正確的檔案權限設定
- 敏感資訊使用環境變數
- 不將 .env 檔案提交到版本控制

## 性能規格

### 資源限制
```yaml
Nginx:
  CPU: 0.5
  Memory: 128M

WordPress:
  CPU: 1.0
  Memory: 512M

MySQL:
  CPU: 1.0
  Memory: 512M
```

### 性能指標
- 首頁載入時間：< 2 秒
- 資料庫查詢響應：< 100ms
- 並發用戶支援：50+
- 容器啟動時間：< 30 秒

## 測試規格

### Unit Test 規格
- 測試框架：Python pytest 或 Node.js Jest
- 測試覆蓋率：> 80%
- 測試項目：
  - 容器健康檢查
  - 服務連接測試
  - 配置檔案驗證
  - 環境變數驗證

### E2E Test 規格
- 測試框架：Playwright 或 Cypress
- 測試場景：
  - WordPress 安裝流程
  - 前端頁面訪問
  - 管理後台操作
  - 資料庫操作驗證

## 部署規格

### 開發環境
- 使用 docker-compose.yml
- 啟用開發模式配置
- 啟用調試日誌

### 生產環境
- 使用 docker-compose.prod.yml
- 禁用調試模式
- 啟用日誌輪轉
- 配置備份策略

## 文檔規格

### 必需文檔
1. README.md - 專案概述和使用說明
2. docs/SDD/01-brief.md - 專案簡述
3. docs/SDD/02-plan.md - 專案計畫
4. docs/SDD/03-spec.md - 技術規格（本文件）
5. docs/SDD/04-tasks.md - 任務清單
6. docs/INSTALLATION.md - 安裝指南
7. docs/TROUBLESHOOTING.md - 故障排除

### 文檔格式
- 使用 Markdown 格式
- 包含代碼範例
- 包含截圖（如需要）
- 使用清晰的標題結構
