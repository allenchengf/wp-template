# WordPress 外掛清單

本文件列出本站建議安裝之外掛與功能項目，依類別整理。外掛名稱以 WordPress.org 官方名稱為準，說明以功能與常見用途為主。

---

## 一、SEO 與分析

| 項目 | 外掛名稱 | 說明 | 備註 |
|------|----------|------|------|
| SEO | [Rank Math SEO](https://wordpress.org/plugins/seo-by-rank-math/) | 關鍵字、sitemap、結構化資料、Open Graph 等 SEO 設定。 | 安裝後待網域與站點設定完成再進行設定。 |
| Google Analytics | [Site Kit by Google](https://wordpress.org/plugins/google-site-kit/) | 官方外掛，整合 Search Console、Analytics、AdSense 等。 | 安裝後待網域與站點設定完成再連結 Google 帳號。 |

---

## 二、效能與快取

| 項目 | 外掛名稱 | 說明 | 備註 |
|------|----------|------|------|
| 網頁快取與速度優化 | [WP Super Cache](https://wordpress.org/plugins/wp-super-cache/) | 產生靜態 HTML 快取，降低資料庫與 PHP 負載，提升載入速度。 | 可依主機環境選擇頁面快取或 Mod Rewrite 模式。 |

---

## 三、備份與還原

| 項目 | 外掛名稱 | 說明 | 備註 |
|------|----------|------|------|
| 自動備份與還原 | [UpdraftPlus](https://wordpress.org/plugins/updraftplus/) | 排程備份檔案與資料庫，支援本機下載及遠端（如 Google Drive、S3）儲存與一鍵還原。 | 建議設定排程並將備份存放至站外空間。 |

---

## 四、資安防護

| 項目 | 外掛名稱 | 說明 | 備註 |
|------|----------|------|------|
| 防火牆、掃描、登入安全 | [Wordfence Security](https://wordpress.org/plugins/wordfence/) | 防火牆規則、惡意程式掃描、即時流量監測、登入嘗試限制、雙因素驗證（2FA）等。 | 安裝後待網域與授權設定完成再啟用進階功能或註冊。 |
| 隱藏登入網址 | [WPS Hide Login](https://wordpress.org/plugins/wps-hide-login/) | 將預設 `wp-admin`／`wp-login.php` 改為自訂路徑（例如 `/login`），降低暴力破解目標。 | 設定後請牢記新登入網址。 |
| reCAPTCHA | [reCaptcha by BestWebSoft](https://wordpress.org/plugins/google-captcha/) | 在登入、註冊、留言或表單加入 Google reCAPTCHA，減少機器人與垃圾提交。 | 需至 Google reCAPTCHA 取得 site key／secret；可於網域與站點就緒後設定。 |

---

## 五、郵件發送

| 項目 | 外掛名稱 | 說明 | 備註 |
|------|----------|------|------|
| SMTP 發信與紀錄 | [WP Mail SMTP](https://wordpress.org/plugins/wp-mail-smtp/)（WPForms 出品） | 以 SMTP 發送系統與表單郵件，支援 Gmail、SendGrid、Mailgun 等，並可記錄發信狀態。 | 可參考官方文件或教學影片設定 SMTP；未啟用前可僅安裝。 |

---

## 六、內容與功能

| 項目 | 外掛名稱 | 說明 | 備註 |
|------|----------|------|------|
| 社群平台分享按鈕 | 待選 | 於文章或頁面加入社群分享按鈕（如 Facebook、X、Line）。常見選項：AddToAny、Shared Counts、Social Warfare 等。 | 依需求選擇其一安裝與設定。 |
| Google 地圖嵌入 | 待選 | 在頁面或文章中嵌入 Google 地圖。可用區塊「Google Maps」或外掛（如 WP Google Map、Maps Marker Pro）達成。 | 依需求選擇區塊或外掛。 |
| 關閉留言 | 內建或輕量外掛 | 關閉全站或特定文章／頁面留言，避免垃圾留言。可透過「設定 → 討論」關閉，或使用 Disable Comments 等外掛細部控制。 | 若無留言需求，建議關閉以減少維護與資安風險。 |

---

## 七、安裝與設定狀態總覽

| 類別 | 外掛 | 建議時程 |
|------|------|----------|
| SEO | Rank Math SEO | 先安裝，網域／站點就緒後設定 |
| 分析 | Site Kit by Google | 先安裝，網域／站點就緒後連結 |
| 快取 | WP Super Cache | 可立即安裝並設定 |
| 備份 | UpdraftPlus | 可立即安裝並設定排程與遠端儲存 |
| 資安 | Wordfence Security | 先安裝，網域／授權就緒後註冊與進階設定 |
| 登入隱藏 | WPS Hide Login | 可立即安裝並設定新登入路徑 |
| reCAPTCHA | reCaptcha by BestWebSoft | 先安裝，網域就緒後設定 key |
| 發信 | WP Mail SMTP | 可安裝，依需求啟用並設定 SMTP |
| 社群分享 | 待選 | 依需求選擇並安裝 |
| 地圖嵌入 | 待選 | 依需求選擇區塊或外掛 |
| 關閉留言 | 內建／外掛 | 依需求於「討論」設定或安裝外掛 |

---

## 批次安裝（VM 上使用 WP-CLI 腳本）

專案內提供腳本，可在已啟動 Docker Compose 的 VM 上一次安裝上述外掛（不含「待選」項目）：

```bash
cd /opt/wp-template
bash scripts/install-wp-plugins.sh
```

- 請用 **bash** 執行（勿用 `sh`）。需已設定 `.env`（含 `MYSQL_PASSWORD` 等），且 `docker compose up -d` 已啟動 wordpress、db。
- 腳本會以 WP-CLI 容器掛載同一 `wp_data` 並安裝外掛；安裝完成後請至後台「外掛」啟用並設定。
- 若專案目錄名稱非 `wp-template`，可先設定：`export COMPOSE_PROJECT_NAME=你的專案目錄名` 再執行腳本。
- 若出現 `請在 .env 設定 MYSQL_PASSWORD`，請確認 `/opt/wp-template/.env` 存在、含 `MYSQL_PASSWORD`，且目前使用者可讀取該檔案。

---

## 參考

- 外掛來源以 [WordPress.org Plugin Directory](https://wordpress.org/plugins/) 為準。
- 安裝前請確認外掛與目前 WordPress、PHP 版本相容，並定期更新以利安全與相容性。
