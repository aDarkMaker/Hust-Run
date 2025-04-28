#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import time
import logging
import configparser
from typing import List, Tuple, Dict, Any
import random
from connect import DeviceConnector

class LocationSimulator:
    """位置模拟器，实现模拟运动轨迹"""
    
    def __init__(self, config_path='config.ini'):
        """初始化位置模拟器"""
        self.logger = logging.getLogger('HustRun.LocationSimulator')
        self.config = configparser.ConfigParser()
        self.config.read(config_path, encoding='utf-8')
        
        # 读取配置
        self.distance = self.config.getint('Basic', 'distance')  # 单位米
        self.speed = self.config.getfloat('Basic', 'speed')  # 单位km/h
        self.time_interval = self.config.getint('Basic', 'time_interval')  # 单位秒
        
        # 位置信息
        self.start_lat = self.config.getfloat('Location', 'start_latitude')
        self.start_lon = self.config.getfloat('Location', 'start_longitude')
        self.track_type = self.config.get('Location', 'track_type')
        
        # 计算参数
        self.speed_mps = self.speed * 1000 / 3600  # 转换为米/秒
        self.step_distance = self.speed_mps * self.time_interval  # 每步移动的距离
        self.total_steps = math.ceil(self.distance / self.step_distance)  # 总步数
        
        # 设备连接器
        self.connector = DeviceConnector(config_path)
        
        self.logger.info(f"初始化完成: 距离={self.distance}米, 速度={self.speed}km/h, 总步数={self.total_steps}")
        
    def generate_circular_track(self) -> List[Tuple[float, float]]:
        """生成圆形跑道轨迹"""
        # 计算圆形跑道的半径 (假设是标准400米跑道)
        track_length = 400  # 标准跑道周长
        radius = track_length / (2 * math.pi)  # 半径
        
        # 计算完成一圈所需的步数
        steps_per_lap = track_length / self.step_distance
        
        # 计算需要跑多少圈
        laps = self.distance / track_length
        
        # 生成轨迹点
        track_points = []
        current_lat = self.start_lat
        current_lon = self.start_lon
        
        # 将跑步距离转换为经纬度坐标序列
        for step in range(self.total_steps):
            # 每一步的角度变化
            angle = (step % steps_per_lap) * (2 * math.pi / steps_per_lap)
            
            # 转换为地理坐标 (简化模型，实际应考虑地球曲率)
            # 纬度1度约等于111公里，经度1度随纬度变化
            lat_offset = radius * math.sin(angle) / 111000
            lon_offset = radius * math.cos(angle) / (111000 * math.cos(math.radians(self.start_lat)))
            
            new_lat = self.start_lat + lat_offset
            new_lon = self.start_lon + lon_offset
            
            # 添加微小随机抖动以模拟真实性
            jitter_lat = random.uniform(-0.000005, 0.000005)
            jitter_lon = random.uniform(-0.000005, 0.000005)
            
            track_points.append((new_lat + jitter_lat, new_lon + jitter_lon))
        
        return track_points
    
    def generate_rectangular_track(self) -> List[Tuple[float, float]]:
        """生成矩形跑道轨迹"""
        # 假设矩形标准跑道，直边长100米，弯道半径约31.83米
        straight_length = 100  # 直道长度
        track_width = 80  # 跑道宽度
        
        # 计算矩形跑道周长
        track_length = 2 * straight_length + 2 * math.pi * track_width / 2
        
        # 步数与圈数
        steps_per_lap = track_length / self.step_distance
        laps = self.distance / track_length
        
        # 生成轨迹
        track_points = []
        
        # 将跑道分为四段：两个直道和两个弯道
        straight1_steps = int(straight_length / self.step_distance)
        curve1_steps = int(math.pi * track_width / 2 / self.step_distance)
        straight2_steps = int(straight_length / self.step_distance)
        curve2_steps = int(math.pi * track_width / 2 / self.step_distance)
        
        # 计算每一步的位置
        for step in range(self.total_steps):
            # 确定当前在哪个段
            step_in_lap = step % steps_per_lap
            
            lat_offset, lon_offset = 0, 0
            
            if step_in_lap < straight1_steps:
                # 第一直道
                progress = step_in_lap / straight1_steps
                lat_offset = 0
                lon_offset = progress * straight_length / 111000 / math.cos(math.radians(self.start_lat))
            elif step_in_lap < straight1_steps + curve1_steps:
                # 第一弯道
                angle = (step_in_lap - straight1_steps) / curve1_steps * math.pi
                radius = track_width / 2
                lat_offset = radius * math.sin(angle) / 111000
                lon_offset = straight_length / 111000 / math.cos(math.radians(self.start_lat)) + radius * (1 - math.cos(angle)) / 111000 / math.cos(math.radians(self.start_lat))
            elif step_in_lap < straight1_steps + curve1_steps + straight2_steps:
                # 第二直道
                progress = (step_in_lap - straight1_steps - curve1_steps) / straight2_steps
                lat_offset = track_width / 111000
                lon_offset = (1 - progress) * straight_length / 111000 / math.cos(math.radians(self.start_lat))
            else:
                # 第二弯道
                angle = (step_in_lap - straight1_steps - curve1_steps - straight2_steps) / curve2_steps * math.pi
                radius = track_width / 2
                lat_offset = radius * math.sin(angle + math.pi) / 111000 + track_width / 111000
                lon_offset = radius * (1 - math.cos(angle + math.pi)) / 111000 / math.cos(math.radians(self.start_lat))
            
            # 添加微小随机抖动
            jitter_lat = random.uniform(-0.000005, 0.000005)
            jitter_lon = random.uniform(-0.000005, 0.000005)
            
            track_points.append((self.start_lat + lat_offset + jitter_lat, self.start_lon + lon_offset + jitter_lon))
        
        return track_points
    
    def generate_track(self) -> List[Tuple[float, float]]:
        """根据配置生成轨迹"""
        if self.track_type.lower() == 'circular':
            return self.generate_circular_track()
        elif self.track_type.lower() == 'rectangular':
            return self.generate_rectangular_track()
        else:
            self.logger.error(f"未知的轨迹类型: {self.track_type}")
            return []
    
    def run(self) -> bool:
        """执行模拟运动"""
        self.logger.info("开始模拟运动")
        
        # 连接设备
        if not self.connector.wait_for_device(30):
            self.logger.error("设备连接失败，无法继续")
            return False
            
        # 生成轨迹
        track_points = self.generate_track()
        if not track_points:
            self.logger.error("生成轨迹失败")
            return False
        
        # 显示运动信息
        total_time = self.time_interval * self.total_steps
        minutes = total_time // 60
        seconds = total_time % 60
        
        self.logger.info(f"运动信息: 距离={self.distance}米, 预计时间={minutes}分{seconds}秒")
        print(f"\n准备开始模拟{self.distance}米的校园跑")
        print(f"速度: {self.speed} km/h")
        print(f"预计用时: {minutes}分{seconds}秒")
        print(f"总计步数: {self.total_steps}\n")
        
        input("请先在手机上打开校园跑应用，准备开始跑步后按回车键开始...")
        
        # 执行运动模拟
        progress_interval = max(1, self.total_steps // 20)  # 分20段显示进度
        
        try:
            for i, (lat, lon) in enumerate(track_points):
                # 发送位置
                success = self.connector.mock_location(lat, lon)
                if not success:
                    self.logger.error(f"模拟位置失败，步骤 {i+1}/{self.total_steps}")
                    return False
                
                # 显示进度
                if i % progress_interval == 0 or i == self.total_steps - 1:
                    progress = (i + 1) / self.total_steps * 100
                    elapsed = (i + 1) * self.time_interval
                    elapsed_min = elapsed // 60
                    elapsed_sec = elapsed % 60
                    
                    meters_done = (i + 1) * self.step_distance
                    
                    print(f"进度: {progress:.1f}% | 已完成: {meters_done:.1f}米 | 已用时间: {elapsed_min}分{elapsed_sec}秒")
                
                # 间隔等待
                time.sleep(self.time_interval)
                
            self.logger.info("模拟运动完成")
            print("\n运动模拟完成! 请在应用中确认运动结束。")
            return True
            
        except KeyboardInterrupt:
            self.logger.info("用户中断运动模拟")
            print("\n运动模拟已中断")
            return False

# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    simulator = LocationSimulator()
    simulator.run()