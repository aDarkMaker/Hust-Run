#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
运动执行模块，整合位置模拟功能
"""

import time
import random
import geopy
from typing import Dict, Optional

from src.logger import get_logger
from src.adb import ADBController

logger = get_logger()

class RunSimulator:
    """运动模拟器类"""
    
    def __init__(self, adb: ADBController):
        """
        初始化运动模拟器
        
        Args:
            adb: ADB控制器实例
        """
        self.adb = adb
        self.is_mocking = False
        self.current_location = None
    
    def enable_mock_location(self) -> bool:
        """启用模拟位置功能"""
        try:
            logger.info("启用模拟位置功能")
            
            # 添加模拟位置权限
            result = self.adb.shell(
                "appops set com.hust.sport android:mock_location allow"
            )
            
            # 启用位置模拟
            provider_result = self.adb.shell(
                "settings put secure mock_location 1"
            )
            
            logger.info("模拟位置功能已启用")
            self.is_mocking = True
            return True
            
        except Exception as e:
            logger.exception(f"启用模拟位置时出错: {str(e)}")
            return False
    
    def disable_mock_location(self) -> bool:
        """禁用模拟位置功能"""
        try:
            if not self.is_mocking:
                return True
                
            logger.info("禁用模拟位置功能")
            
            # 移除模拟位置权限
            result = self.adb.shell(
                "appops set com.hust.sport android:mock_location default"
            )
            
            # 禁用位置模拟
            provider_result = self.adb.shell(
                "settings put secure mock_location 0"
            )
            
            logger.info("模拟位置功能已禁用")
            self.is_mocking = False
            return True
            
        except Exception as e:
            logger.exception(f"禁用模拟位置时出错: {str(e)}")
            return False
    
    def set_location(self, latitude: float, longitude: float, altitude: float = 10.0) -> bool:
        """
        设置设备位置
        
        Args:
            latitude: 纬度
            longitude: 经度
            altitude: 海拔
            
        Returns:
            是否设置成功
        """
        try:
            # 确保已启用模拟位置
            if not self.is_mocking:
                self.enable_mock_location()
            
            # 添加随机变化使位置更真实
            jitter = 0.000005 * random.uniform(-1, 1)  # 约0.5米
            latitude += jitter
            longitude += jitter
            
            logger.debug(f"设置位置: 纬度={latitude}, 经度={longitude}, 海拔={altitude}")
            
            # 使用ADB命令设置位置
            cmd = (
                f"am broadcast -a android.intent.action.MOCK_LOCATION "
                f"--ef latitude {latitude} --ef longitude {longitude} --ef altitude {altitude}"
            )
            result = self.adb.shell(cmd)
        
            # 记录当前位置
            self.current_location = {
                'latitude': latitude,
                'longitude': longitude,
                'altitude': altitude,
                'timestamp': time.time()
            }
            return True
            
        except Exception as e:
            logger.exception(f"设置位置时出错: {str(e)}")
            return False
    
    def move_to(self, target_lat: float, target_lng: float, 
                speed: float, steps: int = 10) -> bool:
        """
        平滑移动到目标位置
        
        Args:
            target_lat: 目标纬度
            target_lng: 目标经度
            speed: 移动速度(米/秒)
            steps: 分几步完成移动
            
        Returns:
            是否移动成功
        """
        try:
            if not self.current_location:
                logger.warning("当前位置未知，直接设置到目标位置")
                return self.set_location(target_lat, target_lng)
            
            # 计算距离和方向
            from geopy.distance import geodesic
            start_point = (self.current_location['latitude'], self.current_location['longitude'])
            end_point = (target_lat, target_lng)
            distance = geodesic(start_point, end_point).meters
            
            # 计算总时间（秒）
            total_time = distance / speed if speed > 0 else 0
            
            # 分步移动
            step_time = total_time / steps
            for i in range(1, steps + 1):
                progress = i / steps
                current_lat = self.current_location['latitude'] + (target_lat - self.current_location['latitude']) * progress
                current_lng = self.current_location['longitude'] + (target_lng - self.current_location['longitude']) * progress
                
                self.set_location(current_lat, current_lng)
                
                if i < steps:
                    time.sleep(step_time)
            
            logger.debug(f"移动完成: 已到达目标位置({target_lat}, {target_lng})")
            return True
            
        except Exception as e:
            logger.exception(f"移动到目标位置时出错: {str(e)}")
            return False
    
    def simulate_heart_rate(self) -> int:
        """模拟心率数据"""
        try:
            # 基础心率范围
            base_rate = random.randint(70, 90)
            
            # 根据运动情况调整心率
            if self.current_location:
                elapsed = time.time() - self.current_location['timestamp']
                time_factor = min(elapsed / 300, 1.0)  # 5分钟达到最大
                heart_rate = base_rate + int(90 * time_factor)  # 最高可达160-180
                heart_rate += random.randint(-5, 5)  # 随机波动
                heart_rate = max(60, min(heart_rate, 180))  # 确保合理范围
            else:
                heart_rate = base_rate
            
            logger.debug(f"模拟心率: {heart_rate}")
            return heart_rate
            
        except Exception as e:
            logger.exception(f"模拟心率数据时出错: {str(e)}")
            return 75  # 默认值

def run():
    """执行运动模拟"""
    try:
        adb = ADBController()
        simulator = RunSimulator(adb)
        
        # 连接设备
        if not adb.connect():
            logger.error("设备连接失败")
            return False
        
        # 启用模拟位置
        if not simulator.enable_mock_location():
            return False
        
        # 示例: 设置初始位置
        simulator.set_location(30.52, 114.36)  # 武汉大致坐标
        
        # 示例: 模拟移动
        simulator.move_to(30.53, 114.37, speed=2.5)
        
        # 禁用模拟位置
        simulator.disable_mock_location()
        return True
        
    except Exception as e:
        logger.exception(f"执行运动模拟时出错: {str(e)}")
        return False
