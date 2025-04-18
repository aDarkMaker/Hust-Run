#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import subprocess
import re
from typing import List, Optional, Tuple, Union

from src.logger import get_logger

logger = get_logger()

class ADBController:
    """ADB控制器类"""
    
    def __init__(self, adb_path: Optional[str] = None, device_id: Optional[str] = None):
        """
        初始化ADB控制器
        
        Args:
            adb_path: ADB可执行文件路径，如果为None则尝试自动查找
            device_id: 设备ID，如果为None则使用第一个可用设备
        """
        self.adb_path = adb_path or self._find_adb_path()
        self.device_id = device_id
        self.connected = False
        
        logger.debug(f"ADB路径: {self.adb_path}")
        logger.debug(f"设备ID: {self.device_id or '自动检测'}")
    
    def _find_adb_path(self) -> str:
        """
        查找ADB可执行文件路径
        
        Returns:
            ADB路径，如果未找到则返回'adb'
        """
        try:
            # 常见的ADB路径
            common_paths = [
                "adb",  # 如果已在PATH中
                "/usr/bin/adb",
                "/usr/local/bin/adb",
                "C:\\Program Files\\Android\\platform-tools\\adb.exe",
                "C:\\Program Files (x86)\\Android\\platform-tools\\adb.exe",
                os.path.expanduser("~/Library/Android/sdk/platform-tools/adb"),
                os.path.expanduser("~/Android/Sdk/platform-tools/adb")
            ]
            
            # 尝试运行各路径
            for path in common_paths:
                try:
                    subprocess.run(
                        [path, "version"], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE, 
                        check=True,
                        timeout=2
                    )
                    logger.debug(f"找到ADB路径: {path}")
                    return path
                except (subprocess.SubprocessError, FileNotFoundError, PermissionError):
                    continue
            
            # 如果都不可用，返回默认值
            logger.warning("未找到ADB路径，使用默认值'adb'")
            return "adb"
            
        except Exception as e:
            logger.exception(f"查找ADB路径时出错: {str(e)}")
            return "adb"
    
    def _build_command(self, *args) -> List[str]:
        """
        构建ADB命令
        
        Args:
            *args: 命令参数
            
        Returns:
            完整的命令列表
        """
        cmd = [self.adb_path]
        
        # 如果指定了设备ID，添加-s参数
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        
        # 添加其他参数
        cmd.extend(args)
        
        return cmd
    
    def run_command(self, *args, timeout: int = 30) -> str:
        """
        运行ADB命令
        
        Args:
            *args: 命令参数
            timeout: 命令超时时间（秒）
            
        Returns:
            命令输出
        """
        try:
            cmd = self._build_command(*args)
            logger.debug(f"运行命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                logger.warning(f"命令返回非零状态码: {result.returncode}")
                logger.warning(f"错误输出: {result.stderr}")
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            logger.error(f"命令超时: {' '.join(args)}")
            return ""
        except Exception as e:
            logger.exception(f"运行命令时出错: {str(e)}")
            return ""
    
    def connect(self) -> bool:
        """
        连接设备
        
        Returns:
            是否成功连接
        """
        try:
            # 检查ADB服务器状态
            self.run_command("start-server")
            
            # 获取设备列表
            devices_output = self.run_command("devices", "-l")
            
            # 检查是否有可用设备
            device_pattern = r"^([^\s]+)\s+device\b"
            devices = re.findall(device_pattern, devices_output, re.MULTILINE)
            
            if not devices:
                logger.error("未检测到已连接的设备")
                return False
            
            # 如果未指定设备ID，使用第一个可用设备
            if not self.device_id:
                self.device_id = devices[0]
                logger.info(f"自动选择设备: {self.device_id}")
            
            # 检查指定的设备是否在列表中
            elif self.device_id not in devices:
                logger.error(f"指定的设备 {self.device_id} 未连接")
                return False
            
            # 测试设备连接
            output = self.run_command("shell", "echo", "connection_test")
            if "connection_test" in output:
                logger.info(f"成功连接到设备: {self.device_id}")
                self.connected = True
                return True
            else:
                logger.error(f"设备连接测试失败")
                return False
                
        except Exception as e:
            logger.exception(f"连接设备时出错: {str(e)}")
            return False
    
    def disconnect(self) -> bool:
        """
        断开设备连接
        
        Returns:
            是否成功断开
        """
        try:
            if not self.connected:
                return True
            
            if self.device_id and ":" in self.device_id:  # TCP/IP设备需要断开
                self.run_command("disconnect", self.device_id)
            
            self.connected = False
            return True
            
        except Exception as e:
            logger.exception(f"断开设备时出错: {str(e)}")
            return False
    
    def shell(self, *args) -> str:
        """
        执行shell命令
        
        Args:
            *args: shell命令及参数
            
        Returns:
            命令输出
        """
        shell_args = ["shell"]
        
        # 如果args是一个字符串，直接添加
        if len(args) == 1 and isinstance(args[0], str):
            shell_args.append(args[0])
        else:
            shell_args.extend(args)
        
        return self.run_command(*shell_args)
    
    def tap(self, x: int, y: int) -> bool:
        """
        点击屏幕
        
        Args:
            x: 横坐标
            y: 纵坐标
            
        Returns:
            是否成功执行
        """
        try:
            self.shell(f"input tap {x} {y}")
            return True
        except Exception as e:
            logger.exception(f"点击屏幕时出错: {str(e)}")
            return False
    
    def long_press(self, x: int, y: int, duration: int = 1000) -> bool:
        """
        长按屏幕
        
        Args:
            x: 横坐标
            y: 纵坐标
            duration: 持续时间（毫秒）
            
        Returns:
            是否成功执行
        """
        try:
            self.shell(f"input swipe {x} {y} {x} {y} {duration}")
            return True
        except Exception as e:
            logger.exception(f"长按屏幕时出错: {str(e)}")
            return False
    
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 500) -> bool:
        """
        滑动屏幕
        
        Args:
            x1: 起点横坐标
            y1: 起点纵坐标
            x2: 终点横坐标
            y2: 终点纵坐标
            duration: 持续时间（毫秒）
            
        Returns:
            是否成功执行
        """
        try:
            self.shell(f"input swipe {x1} {y1} {x2} {y2} {duration}")
            return True
        except Exception as e:
            logger.exception(f"滑动屏幕时出错: {str(e)}")
            return False
    
    def input_text(self, text: str) -> bool:
        """
        输入文本
        
        Args:
            text: 要输入的文本
            
        Returns:
            是否成功执行
        """
        try:
            # 替换特殊字符
            safe_text = text.replace(" ", "%s").replace("&", "\\&")
            self.shell(f"input text '{safe_text}'")
            return True
        except Exception as e:
            logger.exception(f"输入文本时出错: {str(e)}")
            return False
    
    def key_event(self, keycode: int) -> bool:
        """
        发送按键事件
        
        Args:
            keycode: 按键代码
            
        Returns:
            是否成功执行
        """
        try:
            self.shell(f"input keyevent {keycode}")
            return True
        except Exception as e:
            logger.exception(f"发送按键事件时出错: {str(e)}")
            return False
    
    def start_app(self, component: str) -> bool:
        """
        启动应用
        
        Args:
            component: 应用组件名 (包名/活动名)
            
        Returns:
            是否成功执行
        """
        try:
            self.shell(f"am start -n {component}")
            return True
        except Exception as e:
            logger.exception(f"启动应用时出错: {str(e)}")
            return False
    
    def stop_app(self, package: str) -> bool:
        """
        停止应用
        
        Args:
            package: 应用包名
            
        Returns:
            是否成功执行
        """
        try:
            self.shell(f"am force-stop {package}")
            return True
        except Exception as e:
            logger.exception(f"停止应用时出错: {str(e)}")
            return False
    
    def install_app(self, apk_path: str) -> bool:
        """
        安装应用
        
        Args:
            apk_path: APK文件路径
            
        Returns:
            是否成功执行
        """
        try:
            result = self.run_command("install", "-r", apk_path)
            return "Success" in result
        except Exception as e:
            logger.exception(f"安装应用时出错: {str(e)}")
            return False
    
    def uninstall_app(self, package: str) -> bool:
        """
        卸载应用
        
        Args:
            package: 应用包名
            
        Returns:
            是否成功执行
        """
        try:
            result = self.run_command("uninstall", package)
            return "Success" in result
        except Exception as e:
            logger.exception(f"卸载应用时出错: {str(e)}")
            return False
    
    def get_current_activity(self) -> str:
        """
        获取当前活动
        
        Returns:
            当前活动名称
        """
        try:
            # 获取当前窗口信息
            output = self.shell("dumpsys window windows | grep -E 'mCurrentFocus|mFocusedApp'")
            
            # 解析活动名称
            match = re.search(r'(\S+/\S+)', output)
            if match:
                return match.group(1)
            else:
                logger.warning("无法获取当前活动")
                return ""
                
        except Exception as e:
            logger.exception(f"获取当前活动时出错: {str(e)}")
            return ""
    
    def is_app_running(self, package: str) -> bool:
        """
        检查应用是否运行
        
        Args:
            package: 应用包名
            
        Returns:
            应用是否运行
        """
        try:
            output = self.shell(f"pidof {package}")
            return bool(output.strip())
        except Exception as e:
            logger.exception(f"检查应用是否运行时出错: {str(e)}")
            return False