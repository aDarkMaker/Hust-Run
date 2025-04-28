#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import configparser
from typing import Dict, Any, Optional
import time
import argparse

from connect import DeviceConnector
from run import LocationSimulator

# 配置日志系统
def setup_logging(config: configparser.ConfigParser) -> logging.Logger:
    """设置日志系统"""
    log_level_str = config.get('Log', 'log_level', fallback='INFO')
    log_level = getattr(logging, log_level_str.upper())
    log_to_file = config.getboolean('Log', 'log_to_file', fallback=True)
    
    # 创建logger
    logger = logging.getLogger('HustRun')
    logger.setLevel(log_level)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(console_handler)
    
    # 如果需要，添加文件处理器
    if log_to_file:
        log_file = os.path.join(os.path.dirname(__file__), 'log.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def check_apk_exists() -> Optional[str]:
    """检查APK文件是否存在"""
    # 查找项目根目录中的APK文件
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for file in os.listdir(root_dir):
        if file.endswith('.apk'):
            return os.path.join(root_dir, file)
    return None

def parse_args() -> Dict[str, Any]:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='华中科技大学校园跑模拟工具')
    parser.add_argument('--install', action='store_true', help='安装或更新APK')
    parser.add_argument('--distance', type=int, help='运行距离（米）')
    parser.add_argument('--speed', type=float, help='运行速度（km/h）')
    
    return vars(parser.parse_args())

def main():
    """主函数"""
    # 获取程序所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 解析命令行参数
    args = parse_args()
    
    # 加载配置
    config = configparser.ConfigParser()
    config_path = os.path.join(script_dir, 'config.ini')
    
    if not os.path.exists(config_path):
        print(f"错误: 配置文件不存在: {config_path}")
        sys.exit(1)
        
    config.read(config_path, encoding='utf-8')
    
    # 设置日志
    logger = setup_logging(config)
    logger.info("启动华中科技大学校园跑模拟工具")
    
    # 应用命令行参数覆盖配置
    if args.get('distance'):
        config.set('Basic', 'distance', str(args['distance']))
        logger.info(f"使用命令行参数设置距离: {args['distance']}米")
        
    if args.get('speed'):
        config.set('Basic', 'speed', str(args['speed']))
        logger.info(f"使用命令行参数设置速度: {args['speed']}km/h")
    
    # 检查是否需要安装APK
    if args.get('install'):
        apk_path = check_apk_exists()
        if not apk_path:
            logger.error("未找到APK文件，请确保APK文件在项目根目录中")
            sys.exit(1)
            
        logger.info(f"找到APK文件: {apk_path}")
        connector = DeviceConnector(config_path)
        
        if not connector.wait_for_device(30):
            logger.error("无法连接设备，请检查USB连接")
            sys.exit(1)
            
        if connector.install_app(apk_path):
            logger.info("应用安装成功")
            print("华中科技大学体育应用已安装成功！")
            
            # 启动应用
            if connector.start_app():
                logger.info("应用启动成功")
                print("请在手机上配置必要的权限（位置权限和模拟位置权限）")
                print("在开发者选项中将'选择模拟位置信息应用'设置为'华中科技大学体育'应用")
            
        else:
            logger.error("应用安装失败")
            sys.exit(1)
            
        # 安装后退出
        print("配置完成后，请重新运行程序开始模拟运动")
        sys.exit(0)
    
    # 显示欢迎信息
    print("\n" + "=" * 50)
    print("  华中科技大学校园跑模拟工具  ")
    print("=" * 50)
    print("该工具通过模拟GPS位置来完成校园跑步任务")
    print(f"当前配置: 距离 {config.get('Basic', 'distance')}米, 速度 {config.get('Basic', 'speed')}km/h")
    print("=" * 50 + "\n")
    
    try:
        # 创建并运行模拟器
        simulator = LocationSimulator(config_path)
        simulator.run()
    except KeyboardInterrupt:
        logger.info("用户手动终止程序")
        print("\n程序已终止")
    except Exception as e:
        logger.exception("程序发生异常")
        print(f"\n程序发生错误: {e}")
    
    print("\n感谢使用！")

if __name__ == "__main__":
    main()