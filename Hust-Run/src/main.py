#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
华中大体育软件辅助脚本主程序入口
"""

import os
import sys
import time
import click
from typing import Optional, List

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.utils.logger import setup_logger, get_logger
from src.utils.adb_utils import ADBController
from src.utils.config_utils import ConfigManager
from src.login import LoginHandler
from src.location import LocationSimulator
from src.route_generator import RouteGenerator
from src.database import HistoryDatabase

# 初始化日志
setup_logger()
logger = get_logger()

class HustRunApp:
    """华中大体育软件辅助脚本应用类"""
    
    def __init__(self):
        """初始化应用"""
        self.config = ConfigManager()
        self.adb = ADBController(self.config.get("System", "adb_path"), self.config.get("Device", "device_id"))
        self.login_handler = LoginHandler(self.adb, self.config)
        self.location_simulator = LocationSimulator(self.adb, self.config)
        self.route_generator = RouteGenerator(self.config)
        self.db = HistoryDatabase()
        
        # 创建必要的目录
        os.makedirs(os.path.join(project_root, "logs"), exist_ok=True)
        os.makedirs(os.path.join(project_root, "data"), exist_ok=True)
        os.makedirs(os.path.join(project_root, "data", "screenshots"), exist_ok=True)
        
        logger.info("华中大体育辅助脚本已初始化")
    
    def connect_device(self) -> bool:
        """连接设备"""
        if self.adb.connect():
            logger.info("设备连接成功")
            return True
        else:
            logger.error("设备连接失败")
            return False
    
    def auto_run(self) -> bool:
        """执行完整的自动化流程"""
        try:
            # 连接设备
            if not self.connect_device():
                return False
                
            # 启动应用
            logger.info("启动华中大体育应用")
            app_package = self.config.get("App", "package_name")
            app_activity = self.config.get("App", "main_activity")
            self.adb.start_app(f"{app_package}/{app_activity}")
            time.sleep(3)
            
            # 登录
            if not self.login_handler.auto_login():
                logger.error("登录失败")
                return False
            
            # 开始运动
            logger.info("准备开始运动")
            if not self.start_exercise():
                logger.error("开始运动失败")
                return False
            
            # 模拟运动
            logger.info("开始模拟运动")
            self.simulate_exercise()
            
            # 结束运动
            logger.info("结束运动")
            self.end_exercise()
            
            # 保存历史记录
            if self.config.get_bool("System", "save_history"):
                self.save_history()
            
            logger.info("自动化流程完成")
            return True
            
        except Exception as e:
            logger.exception(f"自动运行过程中出错: {str(e)}")
            return False
    
    def start_exercise(self) -> bool:
        """开始运动"""
        try:
            # 点击开始运动按钮
            logger.info("点击开始锻炼按钮")
            # 这里需要根据实际应用界面调整坐标或UI元素ID
            self.adb.tap(521 , 950)  # 假设这是开始运动按钮的位置
            time.sleep(2)
            
            # 选择运动类型
            activity_type = self.config.get_int("Run", "activity_type")
            logger.info(f"选择运动类型: {activity_type}")
            
            # 根据不同运动类型选择不同按钮
            logger.info("开始课外锻炼")
            if activity_type == 0:  # 跑步
                self.adb.tap(550, 1860)
            elif activity_type == 1:  # 骑行
                self.adb.tap(540, 800)
            elif activity_type == 2:  # 行走
                self.adb.tap(780, 800)
            # 1和2是写着玩的，其实没这个选项
            
            time.sleep(2)
            
            # 点击确认按钮
            logger.info("确认开始运动")
            self.adb.tap(500, 371)
            time.sleep(2)
            
            self.adb.tap(500, 371)
            time.sleep(2)
            
            return True
            
        except Exception as e:
            logger.exception(f"开始运动时出错: {str(e)}")
            return False
    
    def simulate_exercise(self) -> bool:
        """模拟运动过程"""
        try:
            # 获取运动路线
            route_name = self.config.get("Run", "default_route")
            route = self.route_generator.load_route(route_name)
            
            if not route:
                logger.error(f"未找到路线: {route_name}")
                return False
            
            # 计算运动参数
            duration = self.config.get_int("Run", "duration") * 60  # 转换为秒
            points = self.route_generator.generate_points(route)
            
            # 开始模拟位置
            logger.info(f"开始模拟位置, 路线: {route['name']}, 预计时间: {duration}秒")
            start_time = time.time()
            
            # 遍历所有路点
            for i, point in enumerate(points):
                # 检查是否超时
                elapsed = time.time() - start_time
                if elapsed >= duration:
                    logger.info("达到预设时间，结束模拟")
                    break
                
                # 更新位置
                lat, lng = point['latitude'], point['longitude']
                # logger.debug(f"更新位置: {lat}, {lng}")
                logger.info(f"更新位置: {lat}, {lng}")
                self.location_simulator.set_location(lat, lng)
                
                # 计算等待时间
                if i < len(points) - 1:
                    wait_time = min(3, duration / len(points))  # 最多等待3秒
                    time.sleep(wait_time)
                
                # 显示进度
                progress = min(100, int((i + 1) / len(points) * 100))
                logger.info(f"运动进度: {progress}%, 已用时间: {int(elapsed)}秒")
            
            logger.info("位置模拟完成")
            return True
            
        except Exception as e:
            logger.exception(f"模拟运动过程中出错: {str(e)}")
            return False
    
    def end_exercise(self) -> bool:
        """结束运动"""
        try:
            # 点击结束运动按钮
            logger.info("点击结束运动按钮")
            self.adb.tap(824, 1607)  # 假设这是结束按钮的位置
            time.sleep(2)
            
            # 确认结束运动
            logger.info("确认结束运动")
            self.adb.tap(548, 1455)  # 假设这是确认按钮的位置
            time.sleep(5)
            
            # 关闭结果页面
            logger.info("关闭结果页面")
            self.adb.tap(540, 1800)
            
            return True
            
        except Exception as e:
            logger.exception(f"结束运动时出错: {str(e)}")
            return False
    
    def save_history(self) -> bool:
        """保存运动历史记录"""
        try:
            # 获取当前时间
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 获取运动类型
            activity_type = self.config.get_int("Run", "activity_type")
            activity_names = ["跑步", "骑行", "行走"]
            activity_name = activity_names[activity_type] if activity_type < len(activity_names) else "未知"
            
            # 获取运动数据
            distance = self.config.get_float("Run", "target_distance")
            duration = self.config.get_int("Run", "duration")
            
            # 保存到数据库
            self.db.add_record(
                activity_type=activity_type,
                activity_name=activity_name,
                distance=distance,
                duration=duration,
                timestamp=current_time
            )
            
            logger.info(f"已保存运动记录: {activity_name}, 距离: {distance}米, 时长: {duration}分钟")
            return True
            
        except Exception as e:
            logger.exception(f"保存历史记录时出错: {str(e)}")
            return False


@click.group()
def cli():
    """华中大体育软件辅助脚本"""
    pass


@cli.command()
def connect():
    """连接设备"""
    app = HustRunApp()
    app.connect_device()


@cli.command()
def auto():
    """执行完整自动化流程"""
    app = HustRunApp()
    app.auto_run()


@cli.command()
def login():
    """仅执行登录"""
    app = HustRunApp()
    if app.connect_device():
        app.login_handler.auto_login()


@cli.command()
def run():
    """仅执行模拟运动"""
    app = HustRunApp()
    if app.connect_device():
        app.start_exercise()
        app.simulate_exercise()
        app.end_exercise()


@cli.command()
@click.option('--route', '-r', help='指定运动路线名称')
def simulate(route):
    """仅执行位置模拟"""
    app = HustRunApp()
    if app.connect_device():
        if route:
            app.config.set("Run", "default_route", route)
        app.simulate_exercise()


if __name__ == "__main__":
    cli()