#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
环境创建模块，整合路线生成功能
"""

import os
import json
import random
import math
from typing import List, Dict, Optional, Tuple

import numpy as np
from geopy.distance import geodesic

from src.logger import get_logger
from src.database import HistoryDatabase

logger = get_logger()

class EnvironmentCreator:
    """环境创建器类"""
    
    def __init__(self):
        """初始化环境创建器"""
        self.db = HistoryDatabase()
        self.routes_dir = os.path.join(os.path.dirname(__file__), "..", "config", "routes")
        os.makedirs(self.routes_dir, exist_ok=True)
    
    def generate_route(self, start_lat: float, start_lng: float, 
                      distance: float, is_loop: bool = True) -> List[Dict]:
        """
        生成运动路线
        
        Args:
            start_lat: 起点纬度
            start_lng: 起点经度
            distance: 路线总距离(米)
            is_loop: 是否为环形路线
            
        Returns:
            路径点列表
        """
        try:
            points = []
            
            # 如果是环形路线
            if is_loop:
                radius = distance / (2 * math.pi)
                num_points = 8
                
                # 生成环形路线点
                waypoints = []
                for i in range(num_points + 1):
                    angle = 2 * math.pi * i / num_points
                    lat_offset = radius * math.sin(angle) / 111000
                    lng_offset = radius * math.cos(angle) / (111000 * math.cos(math.radians(start_lat)))
                    waypoints.append({
                        "latitude": start_lat + lat_offset,
                        "longitude": start_lng + lng_offset
                    })
            else:
                # 生成往返路线
                bearing = random.uniform(0, 360)
                half_distance = distance / 2
                end_point = geodesic(kilometers=half_distance/1000).destination(
                    (start_lat, start_lng), bearing
                )
                waypoints = [
                    {"latitude": start_lat, "longitude": start_lng},
                    {"latitude": (start_lat + end_point.latitude)/2, "longitude": (start_lng + end_point.longitude)/2},
                    {"latitude": end_point.latitude, "longitude": end_point.longitude},
                    {"latitude": (start_lat + end_point.latitude)/2, "longitude": (start_lng + end_point.longitude)/2},
                    {"latitude": start_lat, "longitude": start_lng}
                ]
            
            # 生成详细路径点
            for i in range(len(waypoints) - 1):
                start = waypoints[i]
                end = waypoints[i + 1]
                segment_distance = geodesic(
                    (start["latitude"], start["longitude"]), 
                    (end["latitude"], end["longitude"])
                ).meters
                
                num_segment_points = max(1, int(segment_distance / 10))
                
                for j in range(num_segment_points + 1):
                    progress = j / num_segment_points
                    lat = start["latitude"] + (end["latitude"] - start["latitude"]) * progress
                    lng = start["longitude"] + (end["longitude"] - start["longitude"]) * progress
                    
                    # 添加随机偏移和海拔变化
                    lat += 0.000005 * random.uniform(-1, 1)
                    lng += 0.000005 * random.uniform(-1, 1)
                    altitude = 20 + 5 * math.sin(2 * math.pi * (progress + i/len(waypoints)))
                    
                    points.append({
                        "latitude": lat,
                        "longitude": lng,
                        "altitude": altitude
                    })
            
            logger.info(f"已生成{len(points)}个路径点")
            return points
            
        except Exception as e:
            logger.exception(f"生成路线时出错: {str(e)}")
            return []
    
    def save_route(self, route_name: str, points: List[Dict]) -> bool:
        """
        保存路线到数据库
        
        Args:
            route_name: 路线名称
            points: 路径点列表
            
        Returns:
            是否保存成功
        """
        try:
            # 保存到数据库
            record_id = self.db.add_record(
                activity_type=0,  # 跑步
                activity_name=route_name,
                distance=sum(
                    geodesic(
                        (points[i]["latitude"], points[i]["longitude"]),
                        (points[i+1]["latitude"], points[i+1]["longitude"])
                    ).meters
                    for i in range(len(points)-1)
                ),
                duration=len(points)/2,  # 假设每点0.5秒
                route_name=route_name
            )
            
            # 保存路径点
            for point in points:
                self.db.add_location_point(
                    record_id=record_id,
                    latitude=point["latitude"],
                    longitude=point["longitude"],
                    altitude=point.get("altitude", 10)
                )
            
            # 保存到文件
            route_path = os.path.join(self.routes_dir, f"{route_name}.json")
            with open(route_path, "w") as f:
                json.dump({
                    "name": route_name,
                    "points": points
                }, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.exception(f"保存路线时出错: {str(e)}")
            return False

def creat_env():
    """创建运动环境"""
    try:
        creator = EnvironmentCreator()
        
        # 示例: 生成并保存环形路线
        points = creator.generate_route(
            start_lat=30.52,
            start_lng=114.36,
            distance=3000
        )
        
        if points:
            creator.save_route("default_route", points)
            return True
        return False
        
    except Exception as e:
        logger.exception(f"创建运动环境时出错: {str(e)}")
        return False
