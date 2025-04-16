#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
路线生成器模块，用于生成和管理运动路线
"""

import os
import json
import random
import math
from typing import List, Dict, Optional, Union, Tuple

import numpy as np
from geopy.distance import geodesic

from src.utils.logger import get_logger
from src.utils.config_utils import ConfigManager

logger = get_logger()

class RouteGenerator:
    """路线生成器类"""
    
    def __init__(self, config: ConfigManager):
        """
        初始化路线生成器
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.routes_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "config", "routes"
        )
        
        # 确保路线目录存在
        os.makedirs(self.routes_dir, exist_ok=True)
    
    def list_routes(self) -> List[str]:
        """
        列出所有可用的路线
        
        Returns:
            路线名称列表
        """
        try:
            routes = []
            for file in os.listdir(self.routes_dir):
                if file.endswith('.json'):
                    route_name = file[:-5]  # 移除.json后缀
                    routes.append(route_name)
            return routes
        except Exception as e:
            logger.exception(f"列出路线时出错: {str(e)}")
            return []
    
    def load_route(self, route_name: str) -> Optional[Dict]:
        """
        加载指定路线
        
        Args:
            route_name: 路线名称
            
        Returns:
            路线数据字典，如果路线不存在则返回None
        """
        try:
            route_path = os.path.join(self.routes_dir, f"{route_name}.json")
            if not os.path.exists(route_path):
                logger.error(f"路线文件不存在: {route_path}")
                return None
            
            with open(route_path, 'r', encoding='utf-8') as f:
                route_data = json.load(f)
            
            logger.debug(f"已加载路线: {route_name}")
            return route_data
            
        except Exception as e:
            logger.exception(f"加载路线时出错: {str(e)}")
            return None
    
    def save_route(self, route_name: str, route_data: Dict) -> bool:
        """
        保存路线数据
        
        Args:
            route_name: 路线名称
            route_data: 路线数据字典
            
        Returns:
            是否成功保存
        """
        try:
            route_path = os.path.join(self.routes_dir, f"{route_name}.json")
            
            with open(route_path, 'w', encoding='utf-8') as f:
                json.dump(route_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"已保存路线: {route_name}")
            return True
            
        except Exception as e:
            logger.exception(f"保存路线时出错: {str(e)}")
            return False
    
    def delete_route(self, route_name: str) -> bool:
        """
        删除指定路线
        
        Args:
            route_name: 路线名称
            
        Returns:
            是否成功删除
        """
        try:
            route_path = os.path.join(self.routes_dir, f"{route_name}.json")
            if not os.path.exists(route_path):
                logger.error(f"路线文件不存在: {route_path}")
                return False
            
            os.remove(route_path)
            logger.info(f"已删除路线: {route_name}")
            return True
            
        except Exception as e:
            logger.exception(f"删除路线时出错: {str(e)}")
            return False
    
    def generate_points(self, route_data: Dict) -> List[Dict]:
        """
        根据路线数据生成详细的路径点
        
        Args:
            route_data: 路线数据字典
            
        Returns:
            路径点列表
        """
        try:
            points = []
            waypoints = route_data.get('waypoints', [])
            repeat = route_data.get('repeat', 1)
            
            if len(waypoints) < 2:
                logger.error("路线中的路点不足，至少需要起点和终点")
                return []
            
            # 处理路线重复
            all_waypoints = []
            for _ in range(repeat):
                all_waypoints.extend(waypoints)
            
            # 确保起点和终点相同（如果是环形路线）
            if route_data.get('start_point') == route_data.get('end_point'):
                all_waypoints.append(all_waypoints[0])
            
            # 生成详细路径点
            for i in range(len(all_waypoints) - 1):
                start = all_waypoints[i]
                end = all_waypoints[i + 1]
                
                # 计算两点之间的距离
                start_point = (start['latitude'], start['longitude'])
                end_point = (end['latitude'], end['longitude'])
                distance = geodesic(start_point, end_point).meters
                
                # 根据距离确定插值点数量，每10米一个点
                num_points = max(1, int(distance / 10))
                
                # 生成插值点
                for j in range(num_points + 1):
                    progress = j / num_points
                    lat = start['latitude'] + (end['latitude'] - start['latitude']) * progress
                    lng = start['longitude'] + (end['longitude'] - start['longitude']) * progress
                    
                    # 添加一些随机偏移，使路线更自然
                    jitter = 0.000005 * random.uniform(-1, 1)  # 约0.5米
                    lat += jitter
                    lng += jitter
                    
                    # 处理海拔变化（如果有）
                    altitude = 0
                    if 'elevation_profile' in route_data and route_data['elevation_profile']['enabled']:
                        profile = route_data['elevation_profile']
                        min_elev = profile['min_elevation']
                        max_elev = profile['max_elevation']
                        variation = profile['variation']
                        
                        # 使用正弦函数模拟起伏
                        base_altitude = (min_elev + max_elev) / 2
                        amplitude = (max_elev - min_elev) / 2
                        phase = 2 * math.pi * (progress + i / len(all_waypoints))
                        
                        altitude = base_altitude + amplitude * math.sin(phase)
                        # 添加随机变化
                        altitude += amplitude * variation * random.uniform(-1, 1)
                    
                    point = {
                        'latitude': lat,
                        'longitude': lng,
                        'altitude': altitude,
                        'segment': i,
                        'progress': progress
                    }
                    
                    points.append(point)
            
            logger.info(f"已生成{len(points)}个路径点")
            return points
            
        except Exception as e:
            logger.exception(f"生成路径点时出错: {str(e)}")
            return []
    
    def create_route(self, name: str, description: str, type_str: str,
                     start_lat: float, start_lng: float,
                     end_lat: float = None, end_lng: float = None,
                     distance: float = None, is_loop: bool = True) -> bool:
        """
        创建新的运动路线
        
        Args:
            name: 路线名称
            description: 路线描述
            type_str: 路线类型（跑步、骑行、行走）
            start_lat: 起点纬度
            start_lng: 起点经度
            end_lat: 终点纬度（如果为None，则使用起点）
            end_lng: 终点经度（如果为None，则使用起点）
            distance: 路线总距离（米）
            is_loop: 是否为环形路线
            
        Returns:
            是否成功创建路线
        """
        try:
            # 设置默认值
            if end_lat is None:
                end_lat = start_lat
            if end_lng is None:
                end_lng = start_lng
            
            # 如果未指定距离，使用配置中的默认值
            if distance is None:
                distance = self.config.get_float("Run", "target_distance")
            
            # 创建路线数据结构
            route_data = {
                "name": name,
                "description": description,
                "type": type_str,
                "distance": distance,
                "start_point": {
                    "latitude": start_lat,
                    "longitude": start_lng,
                    "name": "起点"
                },
                "end_point": {
                    "latitude": end_lat,
                    "longitude": end_lng,
                    "name": "终点"
                },
                "waypoints": [
                    {"latitude": start_lat, "longitude": start_lng, "name": "起点"}
                ],
                "repeat": 1,
                "elevation_profile": {
                    "enabled": True,
                    "min_elevation": 20,
                    "max_elevation": 25,
                    "variation": 0.1
                }
            }
            
            # 如果是环形路线，生成一个简单的环形
            if is_loop:
                # 计算需要的半径（米）
                radius = distance / (2 * math.pi)
                
                # 生成环形路线上的点
                num_points = 8  # 8个点组成一个环形
                for i in range(1, num_points):
                    angle = 2 * math.pi * i / num_points
                    
                    # 计算偏移（经度1度约111km，纬度1度约111km）
                    lat_offset = radius * math.sin(angle) / 111000
                    lng_offset = radius * math.cos(angle) / (111000 * math.cos(math.radians(start_lat)))
                    
                    point = {
                        "latitude": start_lat + lat_offset,
                        "longitude": start_lng + lng_offset,
                        "name": f"路点{i}"
                    }
                    route_data["waypoints"].append(point)
                
                # 添加终点（与起点相同）
                route_data["waypoints"].append({
                    "latitude": start_lat,
                    "longitude": start_lng, 
                    "name": "终点"
                })
            
            # 否则，生成一条直线往返路线
            else:
                # 计算方向向量
                bearing = random.uniform(0, 360)  # 随机方向
                
                # 计算距离（单程）
                single_distance = distance / 2
                
                # 计算终点坐标
                from geopy.distance import geodesic, distance
                end_point = geodesic(kilometers=single_distance/1000).destination(
                    (start_lat, start_lng), bearing
                )
                end_lat, end_lng = end_point.latitude, end_point.longitude
                
                # 更新路线数据
                route_data["end_point"]["latitude"] = end_lat
                route_data["end_point"]["longitude"] = end_lng
                
                # 添加中间点
                midpoint = {
                    "latitude": (start_lat + end_lat) / 2,
                    "longitude": (start_lng + end_lng) / 2,
                    "name": "中途点"
                }
                
                # 添加路点
                route_data["waypoints"].append(midpoint)
                route_data["waypoints"].append({
                    "latitude": end_lat,
                    "longitude": end_lng, 
                    "name": "折返点"
                })
                route_data["waypoints"].append(midpoint)
                route_data["waypoints"].append({
                    "latitude": start_lat,
                    "longitude": start_lng, 
                    "name": "终点"
                })
            
            # 保存路线
            route_name = name.lower().replace(" ", "_")
            return self.save_route(route_name, route_data)
            
        except Exception as e:
            logger.exception(f"创建路线时出错: {str(e)}")
            return False