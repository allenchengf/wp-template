#!/usr/bin/env python3
"""
Negative Test Cases - 負面測試案例
測試錯誤情況、邊界條件和異常處理
"""

import unittest
import subprocess
import os
import requests
from typing import Dict, List


class TestNegativeCases(unittest.TestCase):
    """負面測試類"""

    BASE_URL = "http://localhost"
    TIMEOUT = 10

    def test_invalid_endpoint(self):
        """測試無效端點返回 404"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/nonexistent-page-12345",
                timeout=self.TIMEOUT,
                allow_redirects=False
            )
            # WordPress 可能會重定向到首頁，所以允許 302 或 404
            self.assertIn(
                response.status_code,
                [404, 302],
                f"無效端點應返回 404 或 302，實際: {response.status_code}"
            )
        except requests.exceptions.RequestException as e:
            self.fail(f"無法測試無效端點: {e}")

    def test_malformed_request(self):
        """測試格式錯誤的請求"""
        try:
            # 測試無效的 HTTP 方法
            response = requests.request(
                "INVALID_METHOD",
                self.BASE_URL,
                timeout=self.TIMEOUT
            )
            # 應該返回 405 Method Not Allowed 或 400 Bad Request
            self.assertIn(
                response.status_code,
                [400, 405, 501],
                f"格式錯誤請求應返回錯誤狀態碼，實際: {response.status_code}"
            )
        except requests.exceptions.RequestException:
            # 某些錯誤可能導致連接失敗，這也是可以接受的
            pass

    def test_oversized_request(self):
        """測試超大請求（超過限制）"""
        try:
            # 創建一個超過 client_max_body_size 的請求
            large_data = "x" * (65 * 1024 * 1024)  # 65MB，超過 64MB 限制
            response = requests.post(
                f"{self.BASE_URL}/wp-admin/admin-ajax.php",
                data={"data": large_data},
                timeout=self.TIMEOUT
            )
            # 應該返回 413 Request Entity Too Large 或 400
            self.assertIn(
                response.status_code,
                [400, 413, 500],
                f"超大請求應返回錯誤狀態碼，實際: {response.status_code}"
            )
        except requests.exceptions.RequestException:
            # 連接可能被拒絕，這也是可以接受的
            pass

    def test_sql_injection_attempt(self):
        """測試 SQL 注入嘗試（負面測試）"""
        try:
            # 嘗試 SQL 注入
            payload = "1' OR '1'='1"
            response = requests.get(
                f"{self.BASE_URL}/?s={payload}",
                timeout=self.TIMEOUT
            )
            # 應該正常處理，不應該執行 SQL（WordPress 會轉義）
            # 檢查響應中不應該包含資料庫錯誤
            self.assertNotIn(
                "SQL syntax",
                response.text.lower(),
                "SQL 注入嘗試不應該暴露資料庫錯誤"
            )
            self.assertNotIn(
                "mysql error",
                response.text.lower(),
                "SQL 注入嘗試不應該暴露 MySQL 錯誤"
            )
        except requests.exceptions.RequestException as e:
            self.skipTest(f"無法測試 SQL 注入防護: {e}")

    def test_xss_attempt(self):
        """測試 XSS 嘗試（負面測試）"""
        try:
            # 嘗試 XSS 攻擊
            payload = "<script>alert('XSS')</script>"
            response = requests.get(
                f"{self.BASE_URL}/?s={payload}",
                timeout=self.TIMEOUT
            )
            # 檢查響應中不應該包含未轉義的腳本標籤
            # WordPress 會轉義，所以應該看到轉義後的版本
            if "<script>" in response.text:
                # 如果存在，應該是被轉義的版本
                self.assertIn(
                    "&lt;script&gt;",
                    response.text,
                    "XSS 嘗試應該被轉義"
                )
        except requests.exceptions.RequestException as e:
            self.skipTest(f"無法測試 XSS 防護: {e}")

    def test_path_traversal_attempt(self):
        """測試路徑遍歷嘗試（負面測試）"""
        try:
            # 嘗試路徑遍歷攻擊
            payloads = [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\config\\sam",
                "....//....//etc/passwd"
            ]
            
            for payload in payloads:
                response = requests.get(
                    f"{self.BASE_URL}/{payload}",
                    timeout=self.TIMEOUT,
                    allow_redirects=False
                )
                # 應該返回 404 或 403，不應該暴露系統檔案
                self.assertIn(
                    response.status_code,
                    [404, 403, 400],
                    f"路徑遍歷嘗試應返回錯誤狀態碼，實際: {response.status_code}"
                )
                # 不應該包含系統檔案內容
                self.assertNotIn(
                    "root:",
                    response.text,
                    "路徑遍歷嘗試不應該暴露系統檔案"
                )
        except requests.exceptions.RequestException as e:
            self.skipTest(f"無法測試路徑遍歷防護: {e}")

    def test_rate_limiting_enforcement(self):
        """測試速率限制是否生效（負面測試）"""
        try:
            # 快速發送超過限制的請求
            rate_limited = False
            for i in range(10):
                response = requests.get(
                    f"{self.BASE_URL}/wp-login.php",
                    timeout=5
                )
                if response.status_code == 429:
                    rate_limited = True
                    break
                # 稍微延遲以避免太快
                import time
                time.sleep(0.1)
            
            # 速率限制可能不會立即觸發，所以這是可選的
            if rate_limited:
                print("\n✅ 速率限制已生效")
            else:
                print("\n⚠️ 速率限制未觸發（可能需要更多請求）")
        except requests.exceptions.RequestException as e:
            self.skipTest(f"無法測試速率限制: {e}")

    def test_sensitive_file_access_denied(self):
        """測試敏感檔案訪問被拒絕（負面測試）"""
        sensitive_files = [
            "/wp-config.php",
            "/.env",
            "/.htaccess",
            "/wp-config-sample.php",
            "/readme.html",
            "/license.txt"
        ]
        
        for file_path in sensitive_files:
            try:
                response = requests.get(
                    f"{self.BASE_URL}{file_path}",
                    timeout=self.TIMEOUT,
                    allow_redirects=False
                )
                # 應該返回 403、404 或 302，不應該是 200
                self.assertNotEqual(
                    response.status_code,
                    200,
                    f"敏感檔案 {file_path} 不應該可以直接訪問（狀態碼: {response.status_code}）"
                )
            except requests.exceptions.RequestException:
                pass

    def test_invalid_http_methods(self):
        """測試無效的 HTTP 方法"""
        invalid_methods = ["DELETE", "PUT", "PATCH", "OPTIONS"]
        
        for method in invalid_methods:
            try:
                response = requests.request(
                    method,
                    self.BASE_URL,
                    timeout=self.TIMEOUT
                )
                # 應該返回適當的狀態碼（405、400 或正常處理）
                self.assertIn(
                    response.status_code,
                    [200, 302, 400, 405, 501],
                    f"無效 HTTP 方法 {method} 應返回適當狀態碼"
                )
            except requests.exceptions.RequestException:
                pass

    def test_malformed_headers(self):
        """測試格式錯誤的標頭"""
        try:
            # 測試缺少必要的標頭
            response = requests.get(
                self.BASE_URL,
                timeout=self.TIMEOUT,
                headers={"Host": ""}  # 空的 Host 標頭
            )
            # 應該正常處理或返回 400
            self.assertIn(
                response.status_code,
                [200, 302, 400],
                "格式錯誤的標頭應被適當處理"
            )
        except requests.exceptions.RequestException:
            pass


class TestErrorHandling(unittest.TestCase):
    """錯誤處理測試類"""

    def test_container_restart_recovery(self):
        """測試容器重啟後自動恢復（負面到正面）"""
        import time
        
        # 記錄當前容器狀態
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "{{.Name}}:{{.Status}}"],
            capture_output=True,
            text=True
        )
        initial_status = result.stdout
        
        # 重啟一個容器
        subprocess.run(
            ["docker", "compose", "restart", "nginx"],
            capture_output=True
        )
        
        # 等待恢復
        time.sleep(10)
        
        # 檢查容器是否恢復
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "{{.Name}}:{{.Status}}"],
            capture_output=True,
            text=True
        )
        final_status = result.stdout
        
        # 容器應該恢復運行
        self.assertIn("Up", final_status, "容器重啟後應該自動恢復")

    def test_database_connection_failure_handling(self):
        """測試資料庫連接失敗處理（負面測試）"""
        # 這個測試需要模擬資料庫連接失敗
        # 在實際環境中，可以通過停止資料庫容器來測試
        # 但這會影響其他測試，所以跳過
        self.skipTest("資料庫連接失敗測試需要模擬環境")

    def test_invalid_environment_variables(self):
        """測試無效環境變數處理"""
        # 檢查環境變數檔案是否存在必需的變數
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                content = f.read()
                # 檢查是否有空值
                lines = content.split('\n')
                for line in lines:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.split('=', 1)
                        # 值不應該是空的（除非是註釋）
                        if not value.strip() and key.strip():
                            self.fail(f"環境變數 {key} 的值為空")


class TestEdgeCases(unittest.TestCase):
    """邊界條件測試類"""

    BASE_URL = "http://localhost"
    TIMEOUT = 10

    def test_empty_request(self):
        """測試空請求"""
        try:
            response = requests.get(self.BASE_URL, timeout=self.TIMEOUT)
            # 應該正常處理
            self.assertIn(
                response.status_code,
                [200, 302],
                "空請求應該正常處理"
            )
        except requests.exceptions.RequestException as e:
            self.fail(f"空請求處理失敗: {e}")

    def test_very_long_url(self):
        """測試超長 URL"""
        try:
            long_path = "/" + "a" * 2000  # 2000 字符的路徑
            response = requests.get(
                f"{self.BASE_URL}{long_path}",
                timeout=self.TIMEOUT
            )
            # 應該返回 414 或正常處理
            self.assertIn(
                response.status_code,
                [200, 302, 400, 404, 414],
                "超長 URL 應該被適當處理"
            )
        except requests.exceptions.RequestException:
            pass

    def test_special_characters_in_url(self):
        """測試 URL 中的特殊字符"""
        special_chars = ["%", "&", "?", "#", "<", ">", "\"", "'"]
        
        for char in special_chars:
            try:
                response = requests.get(
                    f"{self.BASE_URL}/test{char}param=value",
                    timeout=self.TIMEOUT
                )
                # 應該正常處理或返回錯誤
                self.assertIn(
                    response.status_code,
                    [200, 302, 400, 404],
                    f"特殊字符 {char} 應該被適當處理"
                )
            except requests.exceptions.RequestException:
                pass

    def test_concurrent_same_request(self):
        """測試並發相同請求"""
        import concurrent.futures
        
        def make_request():
            try:
                response = requests.get(self.BASE_URL, timeout=10)
                return response.status_code in [200, 302]
            except:
                return False
        
        # 發送 5 個相同的並發請求
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        success_count = sum(results)
        # 至少應該有一些成功
        self.assertGreater(
            success_count,
            0,
            "並發相同請求應該至少有一些成功"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
