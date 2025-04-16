#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
登录模块，处理华中大体育软件的登录功能
"""

import os
import time
import base64
from typing import Tuple, Optional

from src.utils.logger import get_logger
from src.utils.adb_utils import ADBController
from src.utils.config_utils import ConfigManager
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

logger = get_logger()

class LoginHandler:
    """登录处理类"""
    
    def __init__(self, adb: ADBController, config: ConfigManager):
        """
        初始化登录处理器
        
        Args:
            adb: ADB控制器实例
            config: 配置管理器实例
        """
        self.adb = adb
        self.config = config
        self.package_name = self.config.get("App", "package_name")
        self.login_activity = self.config.get("App", "login_activity")
        self.username = self.decrypt_credentials(self.config.get("User", "username"))
        self.password = self.decrypt_credentials(self.config.get("User", "password"))
        
    def encrypt_credentials(self, text: str) -> str:
        """
        简单加密凭证
        
        Args:
            text: 要加密的文本
            
        Returns:
            加密后的文本
        """
        if not text:
            return ""
            
        # 使用简单的加密密钥 (实际应用中应使用更安全的方法)
        key = b'HustSportAppKey!'
        iv = b'HustSportAppIV!!'
        
        # 确保文本长度为16的倍数
        padded_text = text + ' ' * (16 - len(text) % 16)
        
        # 加密
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(padded_text.encode()) + encryptor.finalize()
        
        # 转为Base64
        return base64.b64encode(encrypted).decode()
    
    def decrypt_credentials(self, encrypted_text: str) -> str:
        """
        解密凭证
        
        Args:
            encrypted_text: 加密的文本
            
        Returns:
            解密后的文本
        """
        if not encrypted_text:
            return ""
            
        try:
            # 使用相同的密钥进行解密
            key = b'HustSportAppKey!'
            iv = b'HustSportAppIV!!'
            
            # 解码Base64
            encrypted = base64.b64decode(encrypted_text)
            
            # 解密
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(encrypted) + decryptor.finalize()
            
            # 去除填充
            return decrypted.decode().rstrip()
        
        except Exception as e:
            logger.error(f"解密凭证失败: {str(e)}")
            return ""
    
    def save_credentials(self, username: str, password: str) -> None:
        """
        保存加密的凭证到配置文件
        
        Args:
            username: 用户名
            password: 密码
        """
        encrypted_username = self.encrypt_credentials(username)
        encrypted_password = self.encrypt_credentials(password)
        
        self.config.set("User", "username", encrypted_username)
        self.config.set("User", "password", encrypted_password)
        self.config.save()
        
        self.username = username
        self.password = password
        
        logger.info("凭证已保存")
    
    def is_on_login_page(self) -> bool:
        """
        检查是否在登录页面
        
        Returns:
            是否在登录页面
        """
        current_activity = self.adb.get_current_activity()
        return self.login_activity in current_activity
    
    def is_logged_in(self) -> bool:
        """
        检查是否已登录
        
        Returns:
            是否已登录
        """
        # 截图并检查登录状态
        screenshot_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                       "data", "screenshots", "login_check.png")
        self.adb.take_screenshot(screenshot_path)
        
        # 可以根据实际情况在这里添加图像识别代码来检测登录状态
        # 此处简化为通过检查当前Activity判断
        current_activity = self.adb.get_current_activity()
        
        # 如果不在登录页面，则认为已登录
        return self.login_activity not in current_activity
    
    def go_to_login_page(self) -> bool:
        """
        导航到登录页面
        
        Returns:
            是否成功导航到登录页面
        """
        try:
            # 如果应用未启动，则启动应用
            if not self.adb.is_app_running(self.package_name):
                logger.info("启动应用")
                self.adb.start_app(f"{self.package_name}/{self.login_activity}")
                time.sleep(5)
                return self.is_on_login_page()
            
            # 如果已经在登录页面，返回True
            if self.is_on_login_page():
                return True
            
            # 如果已登录，退出登录
            if self.is_logged_in():
                logger.info("已登录，尝试退出登录")
                # 点击"我的"选项卡 - 需要根据实际界面调整坐标
                self.adb.tap(900, 2000)
                time.sleep(1)
                
                # 点击设置按钮 - 需要根据实际界面调整坐标
                self.adb.tap(900, 300)
                time.sleep(1)
                
                # 点击退出登录按钮 - 需要根据实际界面调整坐标
                self.adb.tap(540, 1800)
                time.sleep(1)
                
                # 确认退出 - 需要根据实际界面调整坐标
                self.adb.tap(700, 1100)
                time.sleep(3)
            
            # 检查是否成功到达登录页面
            return self.is_on_login_page()
            
        except Exception as e:
            logger.exception(f"导航到登录页面时出错: {str(e)}")
            return False
    
    def input_credentials(self) -> bool:
        """
        输入登录凭证
        
        Returns:
            是否成功输入凭证
        """
        try:
            if not self.username or not self.password:
                logger.error("用户名或密码为空")
                return False
            
            # 清除用户名输入框 - 需要根据实际界面调整坐标
            self.adb.tap(540, 800)
            time.sleep(0.5)
            self.adb.long_press(540, 800, 1000)
            time.sleep(0.5)
            self.adb.tap(700, 900)  # 点击"全选"
            time.sleep(0.5)
            self.adb.key_event(67)  # DEL键
            time.sleep(0.5)
            
            # 输入用户名
            logger.info(f"输入用户名: {self.username}")
            self.adb.input_text(self.username)
            time.sleep(1)
            
            # 点击密码输入框 - 需要根据实际界面调整坐标
            self.adb.tap(540, 1000)
            time.sleep(0.5)
            
            # 清除密码输入框
            self.adb.long_press(540, 1000, 1000)
            time.sleep(0.5)
            self.adb.tap(700, 1100)  # 点击"全选"
            time.sleep(0.5)
            self.adb.key_event(67)  # DEL键
            time.sleep(0.5)
            
            # 输入密码
            logger.info("输入密码")
            self.adb.input_text(self.password)
            time.sleep(1)
            
            return True
            
        except Exception as e:
            logger.exception(f"输入凭证时出错: {str(e)}")
            return False
    
    def click_login_button(self) -> bool:
        """
        点击登录按钮
        
        Returns:
            是否成功点击登录按钮
        """
        try:
            # 点击登录按钮 - 需要根据实际界面调整坐标
            logger.info("点击登录按钮")
            self.adb.tap(540, 1300)
            
            # 等待登录过程
            time.sleep(5)
            
            # 检查是否登录成功
            if self.is_logged_in():
                logger.info("登录成功")
                return True
            else:
                logger.error("登录失败")
                return False
                
        except Exception as e:
            logger.exception(f"点击登录按钮时出错: {str(e)}")
            return False
    
    def handle_login_prompt(self) -> bool:
        """
        处理登录提示或验证码等特殊情况
        
        Returns:
            是否成功处理
        """
        try:
            # 截图以检查是否有提示
            screenshot_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                           "data", "screenshots", "login_prompt.png")
            self.adb.take_screenshot(screenshot_path)
            
            # 这里可以添加图像识别代码来检测和处理特殊提示
            # 例如，检测验证码或错误消息
            
            # 简化处理: 检查是否有可能的"确定"按钮
            self.adb.tap(540, 1200)  # 假设这是确定按钮的位置
            time.sleep(1)
            
            return True
            
        except Exception as e:
            logger.exception(f"处理登录提示时出错: {str(e)}")
            return False
    
    def auto_login(self) -> bool:
        """
        自动完成登录流程
        
        Returns:
            是否成功登录
        """
        try:
            # 检查是否已经登录
            if self.is_logged_in():
                logger.info("已经登录，无需再次登录")
                return True
            
            # 导航到登录页面
            logger.info("导航到登录页面")
            if not self.go_to_login_page():
                logger.error("无法导航到登录页面")
                return False
            
            # 如果凭证为空，提示用户
            if not self.username or not self.password:
                logger.error("用户名或密码为空，请先设置凭证")
                return False
            
            # 输入凭证
            logger.info("开始输入凭证")
            if not self.input_credentials():
                logger.error("输入凭证失败")
                return False
            
            # 点击登录按钮
            logger.info("点击登录按钮")
            if not self.click_login_button():
                # 处理可能的登录提示
                logger.info("尝试处理登录提示")
                self.handle_login_prompt()
                
                # 再次检查登录状态
                time.sleep(2)
                if not self.is_logged_in():
                    logger.error("登录失败")
                    return False
            
            logger.info("登录成功")
            return True
            
        except Exception as e:
            logger.exception(f"自动登录过程中出错: {str(e)}")
            return False