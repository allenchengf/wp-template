-- MySQL 初始化腳本
-- 確保使用 utf8mb4 字符集

-- 設置字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- 創建資料庫（如果不存在）
CREATE DATABASE IF NOT EXISTS wordpress 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- 使用資料庫
USE wordpress;

-- 確保用戶權限正確設置
-- 注意：用戶和權限已在 docker-compose.yml 中通過環境變數設置
-- 此處僅作為備份配置

-- 授予權限（如果需要）
-- GRANT ALL PRIVILEGES ON wordpress.* TO 'wordpress'@'%';
-- FLUSH PRIVILEGES;
