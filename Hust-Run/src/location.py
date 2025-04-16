#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
位置模拟模块，处理GPS位置模拟功能
"""

import time
import random
import geopy
import subprocess
from typing import Tuple, List, Dict, Optional, Union

from src.utils.logger import get_logger
from src.utils.adb_utils import ADBController
from src.utils.config_utils import ConfigManager

logger = get_logger()

class LocationSimulator:
    """位置模拟器类"""
    
    def __init__(self, adb: ADBController, config: ConfigManager):
        """
        初始化位置模拟器
        
        Args:
            adb: ADB控制器实例
            config: 配置管理器实例
        """
        self.adb = adb
        self.config = config
        self.mock_provider = self.config.get("Device", "mock_provider")
        self.accuracy = self.config.get_float("Device", "location_accuracy")
        self.is_mocking = False
        self.current_location = None
        self.is_ld_player = self._detect_ld_player()
    
    def enable_mock_location(self) -> bool:
        """
        启用模拟位置
        
        Returns:
            是否成功启用
        """
        try:
            logger.info("启用模拟位置功能")
            
            # 检查是否已启用开发者选项和模拟位置
            if not self._check_developer_options():
                logger.warning("请确保设备已启用开发者选项和模拟位置权限")
            
            # 添加模拟位置提供者
            result = self.adb.shell(
                f"appops set {self.config.get('App', 'package_name')} " +
                f"android:mock_location allow"
            )
            
            # 添加位置提供者
            provider_result = self.adb.shell(
                f"settings put secure mock_location 1"
            )
            
            logger.info("模拟位置功能已启用")
            self.is_mocking = True
            return True
            
        except Exception as e:
            logger.exception(f"启用模拟位置时出错: {str(e)}")
            return False
    
    def disable_mock_location(self) -> bool:
        """
        禁用模拟位置
        
        Returns:
            是否成功禁用
        """
        try:
            if not self.is_mocking:
                return True
                
            logger.info("禁用模拟位置功能")
            
            # 移除模拟位置提供者
            result = self.adb.shell(
                f"appops set {self.config.get('App', 'package_name')} " +
                f"android:mock_location default"
            )
            
            # 禁用位置模拟
            provider_result = self.adb.shell(
                f"settings put secure mock_location 0"
            )
            
            logger.info("模拟位置功能已禁用")
            self.is_mocking = False
            return True
            
        except Exception as e:
            logger.exception(f"禁用模拟位置时出错: {str(e)}")
            return False
    
    def set_location(self, latitude: float, longitude: float, altitude: float = 10.0) -> bool:
        try:
            # 确保已启用模拟位置
            if not self.is_mocking:
                self.enable_mock_location()
            
            # 添加一些随机变化，使位置更真实
            jitter = self.accuracy * random.uniform(-0.5, 0.5) / 111000  # 约111km = 1度
            latitude += jitter
            longitude += jitter
            
            logger.debug(f"设置模拟位置: 纬度={latitude}, 经度={longitude}, 海拔={altitude}")
            
            if self.is_ld_player:
                # 雷电模拟器使用wke命令
                return self._set_ld_location(latitude, longitude, altitude)
            else:
                # 其他设备使用ADB命令
                return self._set_adb_location(latitude, longitude, altitude)
            
        except Exception as e:
            logger.exception(f"设置模拟位置时出错: {str(e)}")
            return False
    
    def move_to(self, target_lat: float, target_lng: float, 
                speed: Optional[float] = None, steps: int = 10) -> bool:
        """
        平滑移动到目标位置
        
        Args:
            target_lat: 目标纬度
            target_lng: 目标经度
            speed: 移动速度(米/秒)，如果为None则使用配置中的值
            steps: 分几步完成移动
            
        Returns:
            是否成功移动
        """
        try:
            if not self.current_location:
                logger.warning("当前位置未知，直接设置到目标位置")
                return self.set_location(target_lat, target_lng)
            
            # 获取当前位置和目标位置
            start_lat = self.current_location['latitude']
            start_lng = self.current_location['longitude']
            
            # 计算距离和方向
            from geopy.distance import geodesic
            start_point = (start_lat, start_lng)
            end_point = (target_lat, target_lng)
            
            # 计算总距离（米）
            distance = geodesic(start_point, end_point).meters
            
            # 如果没有指定速度，使用配置中的速度
            if speed is None:
                speed = self.config.get_float("Run", "avg_speed")
                # 添加随机变化
                variation = self.config.get_float("Run", "speed_variation")
                speed *= (1 + random.uniform(-variation, variation))
            
            # 计算总时间（秒）
            total_time = distance / speed if speed > 0 else 0
            
            # 如果距离太短或总时间太短，直接设置到目标位置
            if distance < 1 or total_time < 0.1:
                return self.set_location(target_lat, target_lng)
            
            logger.info(f"开始移动: 距离={distance:.2f}m, 速度={speed:.2f}m/s, 预计时间={total_time:.2f}s")
            
            # 分步移动
            step_time = total_time / steps
            for i in range(1, steps + 1):
                # 计算当前步骤的位置
                progress = i / steps
                current_lat = start_lat + (target_lat - start_lat) * progress
                current_lng = start_lng + (target_lng - start_lng) * progress
                
                # 设置位置
                self.set_location(current_lat, current_lng)
                
                # 等待下一步，最后一步不等待
                if i < steps:
                    time.sleep(step_time)
            
            logger.debug(f"移动完成: 已到达目标位置({target_lat}, {target_lng})")
            return True
            
        except Exception as e:
            logger.exception(f"移动到目标位置时出错: {str(e)}")
            return False
    
    def simulate_heart_rate(self) -> int:
        """
        模拟心率数据
        
        Returns:
            模拟的心率值
        """
        try:
            # 基础心率范围
            base_rate = random.randint(70, 90)
            
            # 根据运动情况调整心率
            if self.current_location:
                elapsed = time.time() - self.current_location['timestamp']
                # 运动时间越长，心率越高，最高不超过180
                time_factor = min(elapsed / 300, 1.0)  # 5分钟达到最大
                activity_type = self.config.get_int("Run", "activity_type")
                
                if activity_type == 0:  # 跑步
                    max_increase = 90  # 最高可达160-180
                elif activity_type == 1:  # 骑行
                    max_increase = 70  # 最高可达140-160
                else:  # 行走
                    max_increase = 50  # 最高可达120-140
                
                heart_rate = base_rate + int(max_increase * time_factor)
                
                # 添加随机波动
                heart_rate += random.randint(-5, 5)
                
                # 确保心率在合理范围内
                heart_rate = max(60, min(heart_rate, 180))
            else:
                heart_rate = base_rate
            
            logger.debug(f"模拟心率: {heart_rate}")
            return heart_rate
            
        except Exception as e:
            logger.exception(f"模拟心率数据时出错: {str(e)}")
            return 75  # 返回一个默认值
    
    def _detect_ld_player(self) -> bool:
        """
        检测是否为雷电模拟器
        
        Returns:
            是否为雷电模拟器
        """
        try:
            # 检查设备型号
            model = self.adb.shell("getprop ro.product.model")
            if "LDPlayer" in model:
                logger.info("检测到雷电模拟器环境")
                return True
            return False
        except Exception as e:
            logger.warning(f"检测模拟器类型时出错: {str(e)}")
            return False

    def _set_ld_location(self, latitude: float, longitude: float, altitude: float) -> bool:
        """
        雷电模拟器专用定位方法
        
        Args:
            latitude: 纬度
            longitude: 经度
            altitude: 海拔
            
        Returns:
            是否设置成功
        """
        try:
            # 使用wke命令设置位置
            cmd = f"wke.exe --imei {self.adb.device_id} geo fix {longitude} {latitude}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"雷电模拟器定位失败: {result.stderr}")
                return False
                
            # 记录当前位置
            self.current_location = {
                'latitude': latitude,
                'longitude': longitude,
                'altitude': altitude,
                'timestamp': time.time()
            }
            return True
        except Exception as e:
            logger.exception(f"雷电模拟器定位时出错: {str(e)}")
            return False

    def _set_adb_location(self, latitude: float, longitude: float, altitude: float) -> bool:
        """
        ADB通用定位方法
        
        Args:
            latitude: 纬度
            longitude: 经度
            altitude: 海拔
            
        Returns:
            是否设置成功
        """
        try:
            # 检查位置服务状态
            if not self._check_location_service():
                logger.warning("位置服务可能不可用")
                
            # 使用 am broadcast 命令设置位置
            cmd = (
                f"am broadcast -a android.intent.action.MOCK_LOCATION "
                f"--ef latitude {latitude} --ef longitude {longitude} --ef altitude {altitude}"
            )
            result = self.adb.shell(cmd)
        
            # 检查命令执行结果
            if "error" in result.lower() or "unknown" in result.lower():
                logger.error(f"设置位置失败: {result}")
                return False
            
            # 记录当前位置
            self.current_location = {
                'latitude': latitude,
                'longitude': longitude,
                'altitude': altitude,
                'timestamp': time.time()
            }
            return True
        except Exception as e:
            logger.exception(f"ADB定位时出错: {str(e)}")
            return False

    def _check_location_service(self) -> bool:
        """
        检查位置服务状态(包括com.android.location.fused)
        
        Returns:
            位置服务是否可用
        """
        try:
            # 检查位置服务状态
            output = self.adb.shell("dumpsys location")
            if "com.android.location.fused" not in output:
                logger.warning("位置服务可能不可用")
                return False
            return True
        except Exception as e:
            logger.exception(f"检查位置服务时出错: {str(e)}")
            return False

    def _check_developer_options(self) -> bool:
        """
        检查设备是否已启用开发者选项和模拟位置
        
        Returns:
            是否已启用
        """
        try:
            # 检查开发者选项是否已启用
            dev_result = self.adb.shell("settings get global development_settings_enabled")
            if "1" not in dev_result:
                logger.warning("设备未启用开发者选项")
                return False
            
            # 检查模拟位置是否已启用
            mock_result = self.adb.shell("settings get secure mock_location")
            if "1" not in mock_result:
                logger.warning("设备未启用模拟位置")
                return False
            
            return True
            
        except Exception as e:
            logger.exception(f"检查开发者选项时出错: {str(e)}")
            return False
