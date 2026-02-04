# WordPress Docker 環境性能優化指南

## 性能測試結果

### 當前性能指標

| 指標 | 目標值 | 實際值 | 狀態 |
|------|--------|--------|------|
| 首頁載入時間 | < 2 秒 | ~0.85 秒 | ✅ 優秀 |
| 資料庫查詢響應 | < 200ms | ~141ms | ✅ 良好 |
| 靜態資源載入 | < 500ms | ~200ms | ✅ 良好 |
| 並發處理能力 | 10+ | 10+ | ✅ 通過 |

### 容器資源使用

| 容器 | CPU 使用 | 記憶體使用 | 狀態 |
|------|----------|------------|------|
| MySQL | 0.67% | 395.2 MiB | ✅ 正常 |
| WordPress | 0.46% | 43.23 MiB | ✅ 正常 |
| Nginx | 0.00% | 8.293 MiB | ✅ 正常 |

## 已實施的性能優化

### 1. Nginx 優化

#### Gzip 壓縮
- ✅ 已啟用 Gzip 壓縮
- ✅ 壓縮級別：6（平衡壓縮率和 CPU 使用）
- ✅ 支援的檔案類型：text、JSON、JavaScript、CSS、SVG、字體

#### 靜態檔案緩存
- ✅ 靜態資源（圖片、CSS、JS）緩存 1 年
- ✅ 使用 `immutable` 緩存策略
- ✅ 關閉靜態資源的訪問日誌

#### 連接優化
- ✅ Keep-alive 超時：65 秒
- ✅ 啟用 sendfile
- ✅ 啟用 tcp_nopush 和 tcp_nodelay

### 2. PHP 優化

#### OPcache 配置
- ✅ 已啟用 OPcache
- ✅ 記憶體消耗：128MB
- ✅ 最大加速檔案數：10000
- ✅ 重新驗證頻率：2 秒

#### PHP-FPM 配置
- ✅ 進程管理：dynamic
- ✅ 記憶體限制：256MB
- ✅ 上傳檔案大小：64MB
- ✅ 執行時間限制：300 秒

### 3. MySQL 優化

#### 字符集配置
- ✅ 使用 utf8mb4 字符集
- ✅ 使用 utf8mb4_unicode_ci 排序規則

#### 性能配置（建議）
可以在 `config/mysql/my.cnf` 中添加以下配置：

```ini
[mysqld]
innodb_buffer_pool_size = 256M
max_connections = 100
query_cache_type = 1
query_cache_size = 32M
innodb_flush_log_at_trx_commit = 2
innodb_log_file_size = 64M
```

## 進一步優化建議

### 1. 添加 Redis 快取

#### 安裝 Redis
在 `docker-compose.yml` 中添加：

```yaml
redis:
  image: redis:7-alpine
  container_name: wordpress_redis
  restart: unless-stopped
  networks:
    - wordpress-network
  volumes:
    - redis_data:/data
```

#### WordPress Redis 插件
安裝 WordPress Redis 快取插件（如 Redis Object Cache）以提升性能。

### 2. 啟用 Nginx 快取

#### FastCGI 快取配置
在 `config/nginx/default.conf` 中添加：

```nginx
fastcgi_cache_path /var/cache/nginx levels=1:2 keys_zone=WORDPRESS:100m inactive=60m;
fastcgi_cache_key "$scheme$request_method$host$request_uri";

location ~ \.php$ {
    # ... 現有配置 ...
    
    fastcgi_cache WORDPRESS;
    fastcgi_cache_valid 200 60m;
    fastcgi_cache_bypass $skip_cache;
    fastcgi_no_cache $skip_cache;
    add_header X-Cache $upstream_cache_status;
}
```

### 3. 資料庫優化

#### 索引優化
定期執行 `OPTIMIZE TABLE` 以優化資料庫表：

```sql
OPTIMIZE TABLE wp_posts;
OPTIMIZE TABLE wp_postmeta;
OPTIMIZE TABLE wp_options;
```

#### 查詢快取
確保 MySQL 查詢快取已啟用（見上方配置）。

### 4. CDN 整合

對於生產環境，建議使用 CDN 來加速靜態資源載入：
- Cloudflare
- AWS CloudFront
- Google Cloud CDN

### 5. 圖片優化

- 使用 WebP 格式
- 啟用圖片懶加載
- 使用 WordPress 圖片優化插件

### 6. 資料庫連接池

考慮使用連接池來減少資料庫連接開銷。

## 性能監控

### 監控工具

1. **Docker Stats**
```bash
docker stats wordpress_db wordpress_app wordpress_nginx
```

2. **Nginx 日誌分析**
```bash
docker compose logs nginx | grep response_time
```

3. **MySQL 慢查詢日誌**
在 MySQL 配置中啟用慢查詢日誌。

### 性能基準測試

運行性能測試：
```bash
python3 -m pytest tests/performance/ -v -s
```

## 生產環境建議

### 1. 資源限制

在 `docker-compose.yml` 中設置資源限制：

```yaml
services:
  wordpress:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

### 2. 日誌管理

- 啟用日誌輪轉
- 限制日誌檔案大小
- 定期清理舊日誌

### 3. 備份策略

- 定期備份資料庫
- 備份 WordPress 檔案
- 測試備份恢復流程

## 故障排除

### 性能問題診斷

1. **檢查容器資源使用**
```bash
docker stats
```

2. **檢查 Nginx 錯誤日誌**
```bash
docker compose logs nginx | grep error
```

3. **檢查 PHP-FPM 狀態**
```bash
docker compose exec wordpress ps aux | grep php-fpm
```

4. **檢查資料庫連接**
```bash
docker compose exec db mysqladmin processlist -u wordpress -p
```

## 參考資源

- [WordPress 性能優化指南](https://wordpress.org/support/article/optimization/)
- [Nginx 性能調優](https://nginx.org/en/docs/http/ngx_core_module.html)
- [PHP-FPM 調優](https://www.php.net/manual/en/install.fpm.configuration.php)
- [MySQL 性能優化](https://dev.mysql.com/doc/refman/8.0/en/optimization.html)
