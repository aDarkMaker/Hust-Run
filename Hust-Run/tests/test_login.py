#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
登录模块测试
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.login import LoginHandler
from src.utils.adb_utils import ADBController
from src.utils.config_utils import ConfigManager

class TestLoginHandler(unittest.TestCase):
    """登录处理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟对象
        self.mock_adb = MagicMock(spec=ADBController)
        self.mock_config = MagicMock(spec=ConfigManager)
        
        # 设置模拟返回值
        self.mock_config.get.return_value = "com.hust.sport"
        
        # 创建测试对象
        self.login_handler = LoginHandler(self.mock_adb, self.mock_config)
        
        # 设置测试用户名和密码
        self.login_handler.username = "test_user"
        self.login_handler.password = "test_password"
    
    def test_encrypt_decrypt_credentials(self):
        """测试凭证加密和解密"""
        original_text = "test_credential"
        encrypted = self.login_handler.encrypt_credentials(original_text)
        decrypted = self.login_handler.decrypt_credentials(encrypted)
        
        self.assertNotEqual(original_text, encrypted, "加密后的文本应与原文不同")
        self.assertEqual(original_text, decrypted, "解密后的文本应与原文相同")
    
    def test_save_credentials(self):
        """测试保存凭证"""
        username = "new_user"
        password = "new_password"
        
        self.login_handler.save_credentials(username, password)
        
        # 验证配置是否被正确设置
        self.mock_config.set.assert_any_call("User", "username", self.login_handler.encrypt_credentials(username))
        self.mock_config.set.assert_any_call("User", "password", self.login_handler.encrypt_credentials(password))
        self.mock_config.save.assert_called_once()
        
        # 验证属性是否被正确设置
        self.assertEqual(username, self.login_handler.username)
        self.assertEqual(password, self.login_handler.password)
    
    def test_is_on_login_page(self):
        """测试是否在登录页面"""
        # 模拟在登录页面
        self.mock_adb.get_current_activity.return_value = "com.hust.sport.LoginActivity"
        self.login_handler.login_activity = "com.hust.sport.LoginActivity"
        
        result = self.login_handler.is_on_login_page()
        self.assertTrue(result, "应检测到在登录页面")
        
        # 模拟不在登录页面
        self.mock_adb.get_current_activity.return_value = "com.hust.sport.MainActivity"
        
        result = self.login_handler.is_on_login_page()
        self.assertFalse(result, "应检测到不在登录页面")
    
    def test_is_logged_in(self):
        """测试是否已登录"""
        # 模拟已登录（不在登录页面）
        self.mock_adb.get_current_activity.return_value = "com.hust.sport.MainActivity"
        self.login_handler.login_activity = "com.hust.sport.LoginActivity"
        
        result = self.login_handler.is_logged_in()
        self.assertTrue(result, "应检测到已登录")
        
        # 模拟未登录（在登录页面）
        self.mock_adb.get_current_activity.return_value = "com.hust.sport.LoginActivity"
        
        result = self.login_handler.is_logged_in()
        self.assertFalse(result, "应检测到未登录")
    
    @patch('os.path.exists')
    def test_auto_login_already_logged_in(self, mock_exists):
        """测试已登录状态下的自动登录"""
        # 模拟已登录
        mock_exists.return_value = True
        self.login_handler.is_logged_in = MagicMock(return_value=True)
        
        result = self.login_handler.auto_login()
        
        self.assertTrue(result, "已登录情况下应直接返回成功")
        self.login_handler.input_credentials.assert_not_called()
        self.login_handler.click_login_button.assert_not_called()
    
    @patch('os.path.exists')
    def test_auto_login_success(self, mock_exists):
        """测试成功登录"""
        # 模拟未登录但登录成功
        mock_exists.return_value = True
        self.login_handler.is_logged_in = MagicMock(side_effect=[False, True])
        self.login_handler.go_to_login_page = MagicMock(return_value=True)
        self.login_handler.input_credentials = MagicMock(return_value=True)
        self.login_handler.click_login_button = MagicMock(return_value=True)
        
        result = self.login_handler.auto_login()
        
        self.assertTrue(result, "登录过程应成功")
        self.login_handler.go_to_login_page.assert_called_once()
        self.login_handler.input_credentials.assert_called_once()
        self.login_handler.click_login_button.assert_called_once()
    
    @patch('os.path.exists')
    def test_auto_login_failure(self, mock_exists):
        """测试登录失败"""
        # 模拟未登录且登录失败
        mock_exists.return_value = True
        self.login_handler.is_logged_in = MagicMock(side_effect=[False, False])
        self.login_handler.go_to_login_page = MagicMock(return_value=True)
        self.login_handler.input_credentials = MagicMock(return_value=True)
        self.login_handler.click_login_button = MagicMock(return_value=False)
        self.login_handler.handle_login_prompt = MagicMock(return_value=True)
        
        result = self.login_handler.auto_login()
        
        self.assertFalse(result, "登录过程应失败")
        self.login_handler.go_to_login_page.assert_called_once()
        self.login_handler.input_credentials.assert_called_once()
        self.login_handler.click_login_button.assert_called_once()
        self.login_handler.handle_login_prompt.assert_called_once()


if __name__ == '__main__':
    unittest.main()