#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主程序入口，协调各模块工作
"""

import argparse
from typing import Optional

from adb import ADBController
from run import RunSimulator
from creat_env import EnvironmentCreator
from logger import get_logger

logger = get_logger()

def connect_device() -> bool:
    """连接设备"""
    try:
        adb = ADBController()
        if adb.connect():
            logger.info("设备连接成功")
            return True
        logger.error("设备连接失败")
        return False
    except Exception as e:
        logger.exception(f"连接设备时出错: {str(e)}")
        return False

def run_simulation() -> bool:
    """执行运动模拟"""
    try:
        # 初始化各模块
        adb = ADBController()
        simulator = RunSimulator(adb)
        creator = EnvironmentCreator()
        
        # 连接设备
        if not adb.connect():
            return False
        
        # 创建运动环境
        if not creator.creat_env():
            logger.error("创建运动环境失败")
            return False
        
        # 启用模拟位置
        if not simulator.enable_mock_location():
            return False
        
        # 加载默认路线
        points = creator.generate_route(
            start_lat=30.52,  # 武汉大致坐标
            start_lng=114.36,
            distance=3000     # 3公里
        )
        
        if not points:
            return False
        
        # 执行运动模拟
        for i in range(len(points) - 1):
            current = points[i]
            next_point = points[i + 1]
            
            simulator.set_location(
                current["latitude"],
                current["longitude"],
                current.get("altitude", 10)
            )
            
            simulator.move_to(
                next_point["latitude"],
                next_point["longitude"],
                speed=2.5  # 2.5米/秒
            )
        
        # 禁用模拟位置
        simulator.disable_mock_location()
        return True
        
    except Exception as e:
        logger.exception(f"执行运动模拟时出错: {str(e)}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="华中大体育自动化脚本")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # connect命令
    connect_parser = subparsers.add_parser("connect", help="连接设备")
    
    # auto命令
    auto_parser = subparsers.add_parser("auto", help="自动执行完整流程")
    
    # run命令
    run_parser = subparsers.add_parser("run", help="执行运动模拟")
    
    args = parser.parse_args()
    
    if args.command == "connect":
        connect_device()
    elif args.command == "auto":
        run_simulation()
    elif args.command == "run":
        run_simulation()

if __name__ == "__main__":
    main()
