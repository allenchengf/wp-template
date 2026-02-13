# WordPress Docker 環境

使用 Docker Compose 建立的完整 WordPress 網站環境，採用最新 LTS 版本的組件，遵循官方最佳實踐。

## 📋 專案概述

本專案提供了一個完整的 WordPress 開發和生產環境，包含：

- **Nginx 1.26** (LTS) - Web 服務器和反向代理
- **WordPress 6.4** (LTS) - 內容管理系統
- **PHP 8.2** (LTS) - 應用程式運行環境
- **MySQL 8.0** (LTS) - 資料庫系統

## 🚀 快速開始

### 前置需求

- Docker >= 20.10
- Docker Compose >= 2.0
- 至少 2GB 可用記憶體
- 至少 5GB 可用磁碟空間

### 安裝步驟

1. **複製環境變數檔案**

```bash
cp env.example .env
```

2. **編輯環境變數**

編輯 `.env` 檔案，設置安全的密碼：

```bash
MYSQL_ROOT_PASSWORD=your_secure_root_password_here
MYSQL_PASSWORD=your_secure_password_here
```

3. **啟動服務**

```bash
docker-compose up -d
```

或者使用 Docker Compose V2：

```bash
docker compose up -d
```

4. **等待服務啟動**

服務啟動需要約 30-60 秒。可以使用以下命令檢查狀態：

```bash
docker-compose ps
```

5. **訪問 WordPress**

打開瀏覽器訪問：`http://localhost`

## 📁 專案結構

```
wp-template/
├── docker-compose.yml          # Docker Compose 配置
├── .env                        # 環境變數（需自行創建）
├── env.example                 # 環境變數範例
├── .gitignore                  # Git 忽略檔案
├── README.md                   # 本檔案
├── config/                     # 配置檔案目錄
│   ├── nginx/                 # Nginx 配置
│   │   ├── nginx.conf
│   │   ├── default.conf
│   │   ├── default-ssl.conf
│   │   └── default-80-redirect.conf
│   ├── php/                   # PHP 配置
│   │   └── php.ini
│   └── mysql/                 # MySQL 配置
│       └── init/
│           └── 01-init.sql
├── docs/                       # 文檔目錄
│   ├── GCP_COMPUTE_ENGINE_DEPLOYMENT.md
│   ├── WORDPRESS_PLUGINS.md
│   └── SDD/                   # SDD 文檔
│       ├── 01-brief.md
│       ├── 02-plan.md
│       ├── 03-spec.md
│       └── 04-tasks.md
├── scripts/                    # 自動化腳本
│   ├── setup-letsencrypt-gcloud.sh
│   ├── verify-https.sh
│   └── install-wp-plugins.sh
└── tests/                      # 測試目錄
    ├── unit/                  # Unit Tests
    │   └── test_containers.py
    ├── e2e/                   # E2E Tests
    │   └── test_wordpress.py
    ├── requirements.txt       # Python 測試依賴
    └── run_tests.sh          # 測試執行腳本
```

## 🧪 測試

### 運行所有測試

```bash
./tests/run_tests.sh
```

### 運行 Unit Tests

```bash
python3 -m pytest tests/unit/ -v
```

或使用 unittest：

```bash
python3 -m unittest tests.unit.test_containers
```

### 運行 E2E Tests

首先安裝依賴：

```bash
pip3 install -r tests/requirements.txt
```

然後運行測試：

```bash
python3 -m pytest tests/e2e/ -v
```

或使用 unittest：

```bash
python3 -m unittest tests.e2e.test_wordpress
```

## 🔧 常用命令

### 啟動服務

```bash
docker-compose up -d
```

### 停止服務

```bash
docker-compose down
```

### 查看服務狀態

```bash
docker-compose ps
```

### 查看日誌

```bash
# 查看所有服務日誌
docker-compose logs

# 查看特定服務日誌
docker-compose logs nginx
docker-compose logs wordpress
docker-compose logs db
```

### 重啟服務

```bash
docker-compose restart
```

### 進入容器

```bash
# 進入 WordPress 容器
docker-compose exec wordpress sh

# 進入 MySQL 容器
docker-compose exec db bash

# 進入 Nginx 容器
docker-compose exec nginx sh
```

### 執行 MySQL 命令

```bash
docker-compose exec db mysql -u wordpress -p wordpress
```

### 備份資料庫

```bash
docker-compose exec db mysqldump -u wordpress -p wordpress > backup.sql
```

### 還原資料庫

```bash
docker-compose exec -T db mysql -u wordpress -p wordpress < backup.sql
```

### 批次安裝 WordPress 外掛（VM）

```bash
cd /opt/wp-template
bash scripts/install-wp-plugins.sh
```

說明：
- 請使用 `bash`（勿用 `sh`）
- 需先完成 `docker compose up -d` 且 `.env` 已設定 `MYSQL_PASSWORD`
- 清單來源與說明見 `docs/WORDPRESS_PLUGINS.md`

## 🔐 安全建議

1. **更改預設密碼**：務必在 `.env` 檔案中設置強密碼
2. **生產環境配置**：生產環境應使用 SSL/TLS 證書
3. **防火牆規則**：僅暴露必要端口
4. **定期更新**：定期更新 Docker 鏡像到最新版本
5. **備份策略**：建立定期備份機制

## 📊 服務端口

| 服務 | 內部端口 | 外部端口 | 說明 |
|------|----------|----------|------|
| Nginx | 80 | 80 | HTTP 服務 |
| Nginx | 443 | 443 | HTTPS 服務（Let's Encrypt） |
| MySQL | 3306 | - | 資料庫（僅內部訪問） |
| WordPress | 9000 | - | PHP-FPM（僅內部訪問） |

## 🐛 故障排除

### 服務無法啟動

1. 檢查 Docker 是否運行：
```bash
docker info
```

2. 檢查端口是否被佔用：
```bash
lsof -i :80
```

3. 查看詳細日誌：
```bash
docker-compose logs
```

### WordPress 無法連接資料庫

1. 檢查資料庫容器是否運行：
```bash
docker-compose ps db
```

2. 檢查環境變數是否正確：
```bash
docker-compose exec wordpress env | grep WORDPRESS
```

3. 測試資料庫連接：
```bash
docker-compose exec db mysql -u wordpress -p
```

### 檔案權限問題

如果遇到檔案權限問題，可以執行：

```bash
docker-compose exec wordpress chown -R www-data:www-data /var/www/html
```

## 📚 文檔

詳細文檔請參考：

- [專案簡述 (Brief)](docs/SDD/01-brief.md)
- [專案計畫 (Plan)](docs/SDD/02-plan.md)
- [技術規格 (Spec)](docs/SDD/03-spec.md)
- [任務清單 (Tasks)](docs/SDD/04-tasks.md)
- [GCP 部署與 HTTPS 設定](docs/GCP_COMPUTE_ENGINE_DEPLOYMENT.md)
- [WordPress 外掛清單與批次安裝](docs/WORDPRESS_PLUGINS.md)

## 🔄 版本資訊

- **WordPress**: 6.4 (LTS)
- **PHP**: 8.2 (LTS)
- **MySQL**: 8.0 (LTS)
- **Nginx**: 1.26 (LTS)

## 📝 授權

本專案採用 MIT 授權。

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📧 聯絡方式

如有問題或建議，請提交 Issue。

---

**注意**：本專案僅供學習和開發使用。生產環境部署請參考 [WordPress 官方文檔](https://wordpress.org/documentation/) 和 [Docker 最佳實踐](https://docs.docker.com/develop/dev-best-practices/)。
