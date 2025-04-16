#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
初始化配置脚本，用于首次设置或重置应用配置
"""

import os
import sys
import time
import getpass
from typing import Optional, Tuple

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from src.utils.logger import setup_logger, get_logger
from src.utils.config_utils import ConfigManager
from src.login import LoginHandler
from src.utils.adb_utils import ADBController

# 初始化日志
setup_logger()
logger = get_logger()

class SetupWizard:
    """设置向导类"""
    
    def __init__(self):
        """初始化设置向导"""
        self.config = ConfigManager()
        self.adb = ADBController()
        self.login_handler = LoginHandler(self.adb, self.config)
        
        # 创建必要的目录
        os.makedirs(os.path.join(project_root, "logs"), exist_ok=True)
        os.makedirs(os.path.join(project_root, "data"), exist_ok=True)
        os.makedirs(os.path.join(project_root, "config", "routes"), exist_ok=True)
        
        logger.info("设置向导已初始化")
    
    def setup_credentials(self) -> bool:
        """
        设置登录凭证
        
        Returns:
            是否成功设置
        """
        print("\n===== 设置登录凭证 =====")
        print("请输入华中大体育软件的登录信息：")
        
        # 获取用户名和密码
        username = input("用户名/学号: ").strip()
        password = getpass.getpass("密码: ").strip()
        
        if not username or not password:
            print("错误: 用户名和密码不能为空")
            return False
        
        # 保存凭证
        self.login_handler.save_credentials(username, password)
        print("登录凭证已保存")
        return True
    
    def setup_adb(self) -> bool:
        """
        设置ADB配置
        
        Returns:
            是否成功设置
        """
        print("\n===== 设置ADB =====")
        print("ADB是与Android设备通信的工具，需要正确配置才能模拟位置。")
        
        # 尝试自动查找ADB
        adb_path = self.adb._find_adb_path()
        
        if adb_path != "adb":
            print(f"已自动找到ADB路径: {adb_path}")
            use_found = input("是否使用此路径? (y/n): ").strip().lower()
            
            if use_found != 'y':
                adb_path = input("请输入ADB路径: ").strip()
        else:
            print("未自动找到ADB路径，请手动输入")
            adb_path = input("ADB路径 (直接回车使用'adb'命令): ").strip() or "adb"
        
        # 保存ADB路径
        self.config.set("System", "adb_path", adb_path)
        self.config.save()
        
        # 更新ADB实例
        self.adb.adb_path = adb_path
        
        # 测试ADB连接
        print("测试ADB连接...")
        try:
            output = self.adb.run_command("version")
            if "Android Debug Bridge" in output:
                print("ADB连接成功！")
                
                # 查找设备
                devices_output = self.adb.run_command("devices", "-l")
                print(f"\n设备列表:\n{devices_output}")
                
                # 如果有多个设备，让用户选择
                if devices_output.count("device") > 1:
                    device_id = input("检测到多个设备，请输入要使用的设备ID: ").strip()
                    if device_id:
                        self.config.set("Device", "device_id", device_id)
                        self.config.save()
                
                return True
            else:
                print(f"警告: ADB连接测试不完全成功，输出: {output}")
                return False
        except Exception as e:
            print(f"错误: ADB连接测试失败 - {str(e)}")
            return False
    
    def setup_run_settings(self) -> bool:
        """
        设置运动参数
        
        Returns:
            是否成功设置
        """
        print("\n===== 设置运动参数 =====")
        
        try:
            # 选择运动类型
            print("请选择默认运动类型:")
            print("0 - 跑步")
            print("1 - 骑行")
            print("2 - 行走")
            
            while True:
                activity_type = input("请输入选项 (0-2): ").strip()
                if activity_type in ["0", "1", "2"]:
                    self.config.set("Run", "activity_type", activity_type)
                    break
                else:
                    print("无效的选项，请重新输入")
            
            # 设置目标距离
            while True:
                distance = input("请输入目标距离 (米) [默认 3000]: ").strip()
                if not distance:
                    distance = "3000"
                
                try:
                    distance_value = float(distance)
                    if distance_value > 0:
                        self.config.set("Run", "target_distance", distance)
                        break
                    else:
                        print("距离必须大于0")
                except ValueError:
                    print("请输入有效的数字")
            
            # 设置速度
            while True:
                speed = input("请输入跑步速度 (米/秒) [默认 2.5]: ").strip()
                if not speed:
                    speed = "2.5"
                
                try:
                    speed_value = float(speed)
                    if speed_value > 0:
                        self.config.set("Run", "avg_speed", speed)
                        break
                    else:
                        print("速度必须大于0")
                except ValueError:
                    print("请输入有效的数字")
            
            # 设置运动时间
            while True:
                duration = input("请输入运动持续时间 (分钟) [默认 30]: ").strip()
                if not duration:
                    duration = "30"
                
                try:
                    duration_value = int(duration)
                    if duration_value > 0:
                        self.config.set("Run", "duration", duration)
                        break
                    else:
                        print("时间必须大于0")
                except ValueError:
                    print("请输入有效的整数")
            
            # 保存配置
            self.config.save()
            print("运动参数设置完成")
            return True
            
        except Exception as e:
            logger.exception(f"设置运动参数时出错: {str(e)}")
            print(f"错误: 设置运动参数失败 - {str(e)}")
            return False
    
    def setup_app_settings(self) -> bool:
        """
        设置应用参数
        
        Returns:
            是否成功设置
        """
        print("\n===== 设置应用参数 =====")
        
        try:
            package_name = input("请输入应用包名 [默认 com.hust.sport]: ").strip()
            if package_name:
                self.config.set("App", "package_name", package_name)
            
            main_activity = input(f"请输入主活动名 [默认 {self.config.get('App', 'main_activity')}]: ").strip()
            if main_activity:
                self.config.set("App", "main_activity", main_activity)
            
            login_activity = input(f"请输入登录活动名 [默认 {self.config.get('App', 'login_activity')}]: ").strip()
            if login_activity:
                self.config.set("App", "login_activity", login_activity)
            
            # 保存配置
            self.config.save()
            print("应用参数设置完成")
            return True
            
        except Exception as e:
            logger.exception(f"设置应用参数时出错: {str(e)}")
            print(f"错误: 设置应用参数失败 - {str(e)}")
            return False
    
    def run_wizard(self) -> bool:
        """
        运行设置向导
        
        Returns:
            是否成功完成设置
        """
        print("=" * 60)
        print(" " * 15 + "华中大体育自动化脚本设置向导")
        print("=" * 60)
        print("本向导将帮助您设置脚本所需的各项参数。\n")
        
        try:
            # 设置登录凭证
            self.setup_credentials()
            
            # 设置ADB
            self.setup_adb()
            
            # 设置运动参数
            self.setup_run_settings()
            
            # 设置应用参数
            self.setup_app_settings()
            
            print("\n===== 设置完成 =====")
            print("所有设置已保存。您现在可以使用以下命令运行脚本：")
            print("python src/main.py auto    - 执行完整自动化流程")
            print("python src/main.py login   - 仅执行登录")
            print("python src/main.py run     - 仅执行模拟运动")
            print("python src/main.py --help  - 查看更多命令\n")
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n设置已取消")
            return False
        except Exception as e:
            logger.exception(f"设置向导运行出错: {str(e)}")
            print(f"\n错误: 设置过程中出现错误 - {str(e)}")
            return False


if __name__ == "__main__":
    wizard = SetupWizard()
    wizard.run_wizard()