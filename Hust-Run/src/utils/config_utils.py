#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置工具模块，提供配置文件的读写功能
"""

import os
import configparser
from typing import Any, Optional, Dict, List

from src.utils.logger import get_logger

logger = get_logger()

class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        if config_path is None:
            # 默认路径: 项目根目录/config/config.ini
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(project_root, "config", "config.ini")
        
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        
        # 加载配置
        self.load()
    
    def load(self) -> bool:
        """
        加载配置文件
        
        Returns:
            是否成功加载
        """
        try:
            if os.path.exists(self.config_path):
                logger.debug(f"加载配置文件: {self.config_path}")
                self.config.read(self.config_path, encoding='utf-8')
                return True
            else:
                logger.warning(f"配置文件不存在: {self.config_path}")
                return False
                
        except Exception as e:
            logger.exception(f"加载配置文件时出错: {str(e)}")
            return False
    
    def save(self) -> bool:
        """
        保存配置文件
        
        Returns:
            是否成功保存
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            
            logger.debug(f"配置已保存到: {self.config_path}")
            return True
            
        except Exception as e:
            logger.exception(f"保存配置文件时出错: {str(e)}")
            return False
    
    def get(self, section: str, option: str, fallback: Any = None) -> str:
        """
        获取配置项
        
        Args:
            section: 配置节
            option: 配置项
            fallback: 默认值
            
        Returns:
            配置值
        """
        try:
            return self.config.get(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is not None:
                return fallback
            logger.warning(f"配置项不存在: [{section}] {option}")
            return ""
        except Exception as e:
            logger.exception(f"获取配置项时出错: {str(e)}")
            return fallback if fallback is not None else ""
    
    def get_int(self, section: str, option: str, fallback: int = 0) -> int:
        """
        获取整数配置项
        
        Args:
            section: 配置节
            option: 配置项
            fallback: 默认值
            
        Returns:
            配置值
        """
        try:
            return self.config.getint(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            if fallback is not None:
                return fallback
            logger.warning(f"配置项不存在或非整数: [{section}] {option}")
            return 0
        except Exception as e:
            logger.exception(f"获取整数配置项时出错: {str(e)}")
            return fallback
    
    def get_float(self, section: str, option: str, fallback: float = 0.0) -> float:
        """
        获取浮点数配置项
        
        Args:
            section: 配置节
            option: 配置项
            fallback: 默认值
            
        Returns:
            配置值
        """
        try:
            return self.config.getfloat(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            if fallback is not None:
                return fallback
            logger.warning(f"配置项不存在或非浮点数: [{section}] {option}")
            return 0.0
        except Exception as e:
            logger.exception(f"获取浮点数配置项时出错: {str(e)}")
            return fallback
    
    def get_bool(self, section: str, option: str, fallback: bool = False) -> bool:
        """
        获取布尔配置项
        
        Args:
            section: 配置节
            option: 配置项
            fallback: 默认值
            
        Returns:
            配置值
        """
        try:
            return self.config.getboolean(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            if fallback is not None:
                return fallback
            logger.warning(f"配置项不存在或非布尔值: [{section}] {option}")
            return False
        except Exception as e:
            logger.exception(f"获取布尔配置项时出错: {str(e)}")
            return fallback
    
    def get_list(self, section: str, option: str, 
                sep: str = ',', fallback: Optional[List] = None) -> List[str]:
        """
        获取列表配置项
        
        Args:
            section: 配置节
            option: 配置项
            sep: 分隔符
            fallback: 默认值
            
        Returns:
            配置值列表
        """
        try:
            value = self.get(section, option)
            if not value:
                return fallback or []
            
            return [item.strip() for item in value.split(sep)]
            
        except Exception as e:
            logger.exception(f"获取列表配置项时出错: {str(e)}")
            return fallback or []
    
    def set(self, section: str, option: str, value: Any) -> bool:
        """
        设置配置项
        
        Args:
            section: 配置节
            option: 配置项
            value: 配置值
            
        Returns:
            是否成功设置
        """
        try:
            # 确保配置节存在
            if not self.config.has_section(section):
                self.config.add_section(section)
            
            # 设置配置项
            self.config.set(section, option, str(value))
            
            logger.debug(f"设置配置项: [{section}] {option} = {value}")
            return True
            
        except Exception as e:
            logger.exception(f"设置配置项时出错: {str(e)}")
            return False
    
    def has_option(self, section: str, option: str) -> bool:
        """
        检查配置项是否存在
        
        Args:
            section: 配置节
            option: 配置项
            
        Returns:
            配置项是否存在
        """
        try:
            return self.config.has_option(section, option)
        except configparser.NoSectionError:
            return False
        except Exception as e:
            logger.exception(f"检查配置项是否存在时出错: {str(e)}")
            return False
    
    def remove_option(self, section: str, option: str) -> bool:
        """
        删除配置项
        
        Args:
            section: 配置节
            option: 配置项
            
        Returns:
            是否成功删除
        """
        try:
            if self.config.has_section(section):
                result = self.config.remove_option(section, option)
                if result:
                    logger.debug(f"已删除配置项: [{section}] {option}")
                return result
            return False
            
        except Exception as e:
            logger.exception(f"删除配置项时出错: {str(e)}")
            return False
    
    def get_sections(self) -> List[str]:
        """
        获取所有配置节
        
        Returns:
            配置节列表
        """
        try:
            return self.config.sections()
        except Exception as e:
            logger.exception(f"获取配置节时出错: {str(e)}")
            return []
    
    def get_options(self, section: str) -> List[str]:
        """
        获取配置节中的所有配置项
        
        Args:
            section: 配置节
            
        Returns:
            配置项列表
        """
        try:
            if self.config.has_section(section):
                return self.config.options(section)
            else:
                logger.warning(f"配置节不存在: {section}")
                return []
                
        except Exception as e:
            logger.exception(f"获取配置项时出错: {str(e)}")
            return []
    
    def get_section_dict(self, section: str) -> Dict[str, str]:
        """
        获取配置节的所有配置项及其值
        
        Args:
            section: 配置节
            
        Returns:
            配置项字典
        """
        try:
            if self.config.has_section(section):
                return dict(self.config.items(section))
            else:
                logger.warning(f"配置节不存在: {section}")
                return {}
                
        except Exception as e:
            logger.exception(f"获取配置节字典时出错: {str(e)}")
            return {}