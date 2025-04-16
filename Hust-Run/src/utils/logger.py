#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志工具模块，提供应用日志功能
"""

import os
import sys
import time
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

# 全局日志对象
_logger = None

def setup_logger(log_file: Optional[str] = None, 
                level: str = "INFO",
                max_bytes: int = 10485760,  # 10MB
                backup_count: int = 5) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        log_file: 日志文件路径，如果为None则使用默认路径
        level: 日志级别
        max_bytes: 日志文件最大字节数
        backup_count: 备份文件数量
        
    Returns:
        日志记录器对象
    """
    global _logger
    
    if _logger is not None:
        return _logger
    
    # 默认日志文件路径
    if log_file is None:
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_dir = os.path.join(project_root, "logs")
        
        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)
        
        # 设置日志文件路径
        log_file = os.path.join(log_dir, "app.log")
    
    # 创建日志记录器
    logger = logging.getLogger("hust_run")
    logger.setLevel(getattr(logging, level.upper()))
    
    # 防止重复添加处理器
    if logger.handlers:
        return logger
    
    # 创建文件处理器
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=max_bytes, 
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    
    # 设置日志格式
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # 记录初始日志
    logger.info("日志系统初始化完成")
    
    # 保存全局日志对象
    _logger = logger
    
    return logger

def get_logger() -> logging.Logger:
    """
    获取日志记录器
    
    Returns:
        日志记录器对象
    """
    global _logger
    
    # 如果日志记录器未初始化，使用默认配置进行初始化
    if _logger is None:
        _logger = setup_logger()
    
    return _logger

def set_level(level: str) -> None:
    """
    设置日志级别
    
    Args:
        level: 日志级别
    """
    logger = get_logger()
    logger.setLevel(getattr(logging, level.upper()))
    logger.info(f"日志级别已设置为: {level}")

def format_exception(e: Exception) -> str:
    """
    格式化异常信息
    
    Args:
        e: 异常对象
        
    Returns:
        格式化后的异常信息
    """
    import traceback
    return f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"