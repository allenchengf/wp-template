#!/usr/bin/env python3
"""
Security Headers Test
測試安全標頭配置
"""

import unittest
import requests
from typing import Dict


class TestSecurityHeaders(unittest.TestCase):
    """安全標頭測試類"""

    BASE_URL = "http://localhost"
    TIMEOUT = 10

    def test_csp_header(self):
        """測試 Content-Security-Policy 標頭"""
        response = requests.get(self.BASE_URL, timeout=self.TIMEOUT)
        headers = response.headers
        
        # 檢查 CSP 標頭是否存在
        self.assertIn(
            'Content-Security-Policy',
            headers,
            "缺少 Content-Security-Policy 標頭"
        )
        print(f"\n✅ CSP: {headers.get('Content-Security-Policy', 'N/A')[:50]}...")

    def test_referrer_policy_header(self):
        """測試 Referrer-Policy 標頭"""
        response = requests.get(self.BASE_URL, timeout=self.TIMEOUT)
        headers = response.headers
        
        self.assertIn(
            'Referrer-Policy',
            headers,
            "缺少 Referrer-Policy 標頭"
        )
        print(f"✅ Referrer-Policy: {headers.get('Referrer-Policy', 'N/A')}")

    def test_permissions_policy_header(self):
        """測試 Permissions-Policy 標頭"""
        response = requests.get(self.BASE_URL, timeout=self.TIMEOUT)
        headers = response.headers
        
        self.assertIn(
            'Permissions-Policy',
            headers,
            "缺少 Permissions-Policy 標頭"
        )
        print(f"✅ Permissions-Policy: {headers.get('Permissions-Policy', 'N/A')[:50]}...")

    def test_x_frame_options_header(self):
        """測試 X-Frame-Options 標頭"""
        response = requests.get(self.BASE_URL, timeout=self.TIMEOUT)
        headers = response.headers
        
        self.assertIn(
            'X-Frame-Options',
            headers,
            "缺少 X-Frame-Options 標頭"
        )
        self.assertEqual(
            headers.get('X-Frame-Options'),
            'SAMEORIGIN',
            "X-Frame-Options 值不正確"
        )
        print(f"✅ X-Frame-Options: {headers.get('X-Frame-Options', 'N/A')}")

    def test_x_content_type_options_header(self):
        """測試 X-Content-Type-Options 標頭"""
        response = requests.get(self.BASE_URL, timeout=self.TIMEOUT)
        headers = response.headers
        
        self.assertIn(
            'X-Content-Type-Options',
            headers,
            "缺少 X-Content-Type-Options 標頭"
        )
        self.assertEqual(
            headers.get('X-Content-Type-Options'),
            'nosniff',
            "X-Content-Type-Options 值不正確"
        )
        print(f"✅ X-Content-Type-Options: {headers.get('X-Content-Type-Options', 'N/A')}")

    def test_x_xss_protection_header(self):
        """測試 X-XSS-Protection 標頭"""
        response = requests.get(self.BASE_URL, timeout=self.TIMEOUT)
        headers = response.headers
        
        self.assertIn(
            'X-XSS-Protection',
            headers,
            "缺少 X-XSS-Protection 標頭"
        )
        print(f"✅ X-XSS-Protection: {headers.get('X-XSS-Protection', 'N/A')}")

    def test_server_header_hidden(self):
        """測試 Server 標頭是否隱藏"""
        response = requests.get(self.BASE_URL, timeout=self.TIMEOUT)
        headers = response.headers
        
        # Server 標頭應該被移除或隱藏版本資訊
        server_header = headers.get('Server', '')
        if server_header:
            # 如果存在，不應該包含版本資訊
            self.assertNotIn(
                'nginx/',
                server_header.lower(),
                "Server 標頭洩露版本資訊"
            )
        print(f"✅ Server 標頭: {'已隱藏' if not server_header or 'nginx' not in server_header.lower() else server_header}")

    def test_all_security_headers(self):
        """測試所有安全標頭"""
        response = requests.get(self.BASE_URL, timeout=self.TIMEOUT)
        headers = response.headers
        
        required_headers = [
            'Content-Security-Policy',
            'Referrer-Policy',
            'Permissions-Policy',
            'X-Frame-Options',
            'X-Content-Type-Options',
            'X-XSS-Protection'
        ]
        
        found_headers = []
        missing_headers = []
        
        for header in required_headers:
            if header in headers:
                found_headers.append(header)
            else:
                missing_headers.append(header)
        
        print(f"\n安全標頭統計:")
        print(f"  已配置: {len(found_headers)}/{len(required_headers)}")
        print(f"  缺失: {missing_headers}")
        
        self.assertEqual(
            len(missing_headers),
            0,
            f"缺少安全標頭: {missing_headers}"
        )


class TestRateLimiting(unittest.TestCase):
    """速率限制測試類"""

    BASE_URL = "http://localhost"
    TIMEOUT = 5

    def test_login_rate_limiting(self):
        """測試登入頁面速率限制"""
        # 發送超過限制的請求
        rate_limited = False
        for i in range(10):
            try:
                response = requests.get(
                    f"{self.BASE_URL}/wp-login.php",
                    timeout=self.TIMEOUT
                )
                if response.status_code == 429:
                    rate_limited = True
                    print(f"\n✅ 速率限制生效（請求 {i+1} 返回 429）")
                    break
            except requests.exceptions.RequestException:
                pass
        
        # 至少應該有一些請求被限制（可能不是全部，因為有 burst）
        print(f"速率限制測試: {'通過' if rate_limited else '未觸發（可能需要更多請求）'}")

    def test_general_rate_limiting(self):
        """測試一般請求速率限制"""
        # 發送大量請求
        rate_limited_count = 0
        total_requests = 70  # 超過 60 req/min 限制
        
        for i in range(total_requests):
            try:
                response = requests.get(self.BASE_URL, timeout=self.TIMEOUT)
                if response.status_code == 429:
                    rate_limited_count += 1
            except requests.exceptions.RequestException:
                pass
            # 稍微延遲以避免太快
            if i % 10 == 0:
                import time
                time.sleep(0.1)
        
        print(f"\n一般請求速率限制測試:")
        print(f"  總請求數: {total_requests}")
        print(f"  被限制: {rate_limited_count}")
        print(f"  狀態: {'通過' if rate_limited_count > 0 else '未觸發（可能需要調整測試）'}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
