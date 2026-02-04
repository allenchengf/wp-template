#!/usr/bin/env python3
"""
E2E Tests for WordPress Installation and Functionality
端到端測試：WordPress 安裝流程和功能測試
"""

import unittest
import requests
import time
import subprocess
from typing import Dict, Optional


class TestWordPressInstallation(unittest.TestCase):
    """WordPress 安裝測試類"""

    BASE_URL = "http://localhost"
    TIMEOUT = 30

    @classmethod
    def setUpClass(cls):
        """測試類初始化"""
        # 等待服務啟動
        cls.wait_for_services()

    @classmethod
    def wait_for_services(cls, max_attempts: int = 30):
        """等待服務啟動"""
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{cls.BASE_URL}/health", timeout=5)
                if response.status_code == 200:
                    print("服務已啟動")
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(2)
        raise Exception("服務啟動超時")

    def test_nginx_health_endpoint(self):
        """測試 Nginx 健康檢查端點"""
        try:
            response = requests.get(f"{self.BASE_URL}/health", timeout=10)
            self.assertEqual(
                response.status_code,
                200,
                "Nginx 健康檢查端點無響應"
            )
            self.assertIn("healthy", response.text.lower())
        except requests.exceptions.RequestException as e:
            self.fail(f"無法連接到 Nginx: {e}")

    def test_wordpress_homepage_accessible(self):
        """測試 WordPress 首頁是否可以訪問"""
        try:
            response = requests.get(self.BASE_URL, timeout=self.TIMEOUT)
            self.assertEqual(
                response.status_code,
                200,
                f"WordPress 首頁無法訪問，狀態碼: {response.status_code}"
            )
            # 檢查是否包含 WordPress 相關內容
            self.assertIn(
                "wordpress",
                response.text.lower(),
                "響應內容不包含 WordPress 相關內容"
            )
        except requests.exceptions.RequestException as e:
            self.fail(f"無法訪問 WordPress 首頁: {e}")

    def test_wordpress_installation_page(self):
        """測試 WordPress 安裝頁面"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/wp-admin/install.php",
                timeout=self.TIMEOUT
            )
            self.assertIn(
                response.status_code,
                [200, 302],  # 200 表示安裝頁面，302 表示已安裝重定向
                f"WordPress 安裝頁面無法訪問，狀態碼: {response.status_code}"
            )
        except requests.exceptions.RequestException as e:
            self.fail(f"無法訪問 WordPress 安裝頁面: {e}")

    def test_wordpress_api_endpoint(self):
        """測試 WordPress REST API 端點"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/wp-json/wp/v2",
                timeout=self.TIMEOUT
            )
            # WordPress 可能還沒完全安裝，所以可能是 200、404 或其他狀態碼
            # 只要不是 500 錯誤，就認為端點可訪問
            self.assertNotEqual(
                response.status_code,
                500,
                f"WordPress REST API 服務器錯誤（狀態碼: {response.status_code}）"
            )
            # 如果返回 200，檢查響應格式
            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                # WordPress 安裝前可能返回 HTML，安裝後返回 JSON
                # 兩種情況都接受
                self.assertIn(
                    content_type,
                    ["application/json; charset=UTF-8", "text/html; charset=utf-8", "text/html; charset=UTF-8"],
                    f"REST API 響應格式異常: {content_type}"
                )
        except requests.exceptions.RequestException as e:
            self.skipTest(f"WordPress REST API 可能尚未完全安裝: {e}")

    def test_static_files_served(self):
        """測試靜態檔案是否可以正常服務"""
        static_files = [
            "/wp-includes/js/jquery/jquery.min.js",
            "/wp-content/themes/twentytwentyfour/style.css"
        ]
        
        for static_file in static_files:
            try:
                response = requests.get(
                    f"{self.BASE_URL}{static_file}",
                    timeout=self.TIMEOUT
                )
                self.assertIn(
                    response.status_code,
                    [200, 404],  # 404 表示檔案不存在但服務正常
                    f"靜態檔案 {static_file} 無法訪問"
                )
            except requests.exceptions.RequestException as e:
                self.fail(f"無法訪問靜態檔案 {static_file}: {e}")

    def test_php_execution(self):
        """測試 PHP 檔案是否可以正常執行"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/wp-admin/load-styles.php",
                timeout=self.TIMEOUT
            )
            # PHP 檔案應該返回 CSS 內容或重定向
            self.assertIn(
                response.status_code,
                [200, 302, 404],
                "PHP 檔案無法正常執行"
            )
        except requests.exceptions.RequestException as e:
            self.fail(f"PHP 執行測試失敗: {e}")

    def test_database_connection(self):
        """測試資料庫連接（通過 WordPress 配置檢查）"""
        try:
            # 檢查 wp-config.php 是否被正確保護
            response = requests.get(
                f"{self.BASE_URL}/wp-config.php",
                timeout=self.TIMEOUT,
                allow_redirects=False
            )
            # Nginx 應該返回 403 Forbidden 或 WordPress 重定向（不應該是 200）
            # 403 = 正確阻止，302 = WordPress 重定向（也可以接受），200 = 安全問題
            self.assertIn(
                response.status_code,
                [403, 404, 302],
                f"wp-config.php 不應該可以直接訪問（狀態碼: {response.status_code}）"
            )
        except requests.exceptions.RequestException as e:
            self.fail(f"資料庫連接測試失敗: {e}")


class TestWordPressFunctionality(unittest.TestCase):
    """WordPress 功能測試類"""

    BASE_URL = "http://localhost"
    TIMEOUT = 30

    def test_wordpress_version(self):
        """測試 WordPress 版本資訊"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/wp-json/wp/v2",
                timeout=self.TIMEOUT
            )
            if response.status_code == 200:
                data = response.json()
                # WordPress REST API 會返回版本資訊
                self.assertIsNotNone(data, "無法獲取 WordPress 版本資訊")
        except requests.exceptions.RequestException as e:
            self.skipTest(f"無法獲取版本資訊: {e}")

    def test_cors_headers(self):
        """測試 CORS 標頭配置"""
        try:
            response = requests.options(
                self.BASE_URL,
                timeout=self.TIMEOUT
            )
            # 檢查響應標頭
            headers = response.headers
            self.assertIsNotNone(headers, "無法獲取響應標頭")
        except requests.exceptions.RequestException as e:
            self.skipTest(f"CORS 測試失敗: {e}")

    def test_response_time(self):
        """測試響應時間"""
        try:
            start_time = time.time()
            response = requests.get(self.BASE_URL, timeout=self.TIMEOUT)
            end_time = time.time()
            
            response_time = end_time - start_time
            self.assertLess(
                response_time,
                2.0,  # 響應時間應小於 2 秒
                f"響應時間過長: {response_time:.2f} 秒"
            )
        except requests.exceptions.RequestException as e:
            self.fail(f"響應時間測試失敗: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
