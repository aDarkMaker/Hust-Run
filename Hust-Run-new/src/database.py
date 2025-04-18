#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库模块，处理运动历史记录的存储和查询
"""

import os
import sqlite3
import time
from typing import List, Dict, Optional, Tuple

from src.logger import get_logger

logger = get_logger()

class HistoryDatabase:
    """历史记录数据库类"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径，如果为None则使用默认路径
        """
        if db_path is None:
            # 默认路径: 项目根目录/data/history.db
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(project_root, "data", "history.db")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        
        # 初始化数据库
        self._init_db()
    
    def _connect(self) -> None:
        """建立数据库连接"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # 使查询结果可通过列名访问
            self.cursor = self.connection.cursor()
        except Exception as e:
            logger.exception(f"连接数据库时出错: {str(e)}")
            raise
    
    def _close(self) -> None:
        """关闭数据库连接"""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
                self.cursor = None
        except Exception as e:
            logger.exception(f"关闭数据库连接时出错: {str(e)}")
    
    def _init_db(self) -> None:
        """初始化数据库表结构"""
        try:
            self._connect()
            
            # 创建运动记录表
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS exercise_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_type INTEGER NOT NULL,
                activity_name TEXT NOT NULL,
                distance REAL NOT NULL,
                duration INTEGER NOT NULL,
                avg_speed REAL,
                avg_heart_rate INTEGER,
                calories INTEGER,
                timestamp TEXT NOT NULL,
                notes TEXT,
                route_name TEXT,
                created_at TEXT NOT NULL
            )
            """)
            
            # 创建路线点表
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS location_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                altitude REAL,
                heart_rate INTEGER,
                speed REAL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (record_id) REFERENCES exercise_records (id) ON DELETE CASCADE
            )
            """)
            
            self.connection.commit()
            logger.debug("数据库初始化完成")
            
        except Exception as e:
            logger.exception(f"初始化数据库时出错: {str(e)}")
            raise
        finally:
            self._close()
    
    def add_record(self, activity_type: int, activity_name: str, 
                   distance: float, duration: int, 
                   avg_speed: Optional[float] = None, 
                   avg_heart_rate: Optional[int] = None,
                   calories: Optional[int] = None, 
                   timestamp: Optional[str] = None,
                   notes: Optional[str] = None, 
                   route_name: Optional[str] = None) -> int:
        """
        添加运动记录
        
        Args:
            activity_type: 活动类型ID
            activity_name: 活动名称
            distance: 运动距离（米）
            duration: 运动时长（分钟）
            avg_speed: 平均速度（米/秒）
            avg_heart_rate: 平均心率
            calories: 消耗卡路里
            timestamp: 运动时间戳
            notes: 备注
            route_name: 路线名称
            
        Returns:
            新记录的ID
        """
        try:
            self._connect()
            
            # 设置默认值
            if timestamp is None:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            if avg_speed is None and distance > 0 and duration > 0:
                avg_speed = distance / (duration * 60)  # 转换为米/秒
            
            created_at = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 插入记录
            self.cursor.execute("""
            INSERT INTO exercise_records (
                activity_type, activity_name, distance, duration, 
                avg_speed, avg_heart_rate, calories, timestamp, 
                notes, route_name, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                activity_type, activity_name, distance, duration,
                avg_speed, avg_heart_rate, calories, timestamp,
                notes, route_name, created_at
            ))
            
            self.connection.commit()
            record_id = self.cursor.lastrowid
            
            logger.info(f"已添加运动记录: ID={record_id}")
            return record_id
            
        except Exception as e:
            logger.exception(f"添加运动记录时出错: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return -1
        finally:
            self._close()
    
    def add_location_point(self, record_id: int, latitude: float, longitude: float,
                          altitude: Optional[float] = None, heart_rate: Optional[int] = None,
                          speed: Optional[float] = None, timestamp: Optional[str] = None) -> int:
        """
        添加位置点记录
        
        Args:
            record_id: 关联的运动记录ID
            latitude: 纬度
            longitude: 经度
            altitude: 海拔（米）
            heart_rate: 心率
            speed: 速度（米/秒）
            timestamp: 时间戳
            
        Returns:
            新记录的ID
        """
        try:
            self._connect()
            
            # 设置默认值
            if timestamp is None:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 插入记录
            self.cursor.execute("""
            INSERT INTO location_points (
                record_id, latitude, longitude, altitude, 
                heart_rate, speed, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                record_id, latitude, longitude, altitude,
                heart_rate, speed, timestamp
            ))
            
            self.connection.commit()
            point_id = self.cursor.lastrowid
            
            logger.debug(f"已添加位置点: ID={point_id}")
            return point_id
            
        except Exception as e:
            logger.exception(f"添加位置点时出错: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return -1
        finally:
            self._close()
    
    def get_records(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        获取运动记录列表
        
        Args:
            limit: 返回记录数量限制
            offset: 起始偏移量
            
        Returns:
            运动记录列表
        """
        try:
            self._connect()
            
            self.cursor.execute("""
            SELECT * FROM exercise_records
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
            """, (limit, offset))
            
            # 将查询结果转换为字典列表
            records = [dict(row) for row in self.cursor.fetchall()]
            
            logger.debug(f"获取到{len(records)}条运动记录")
            return records
            
        except Exception as e:
            logger.exception(f"获取运动记录时出错: {str(e)}")
            return []
        finally:
            self._close()
    
    def get_record_by_id(self, record_id: int) -> Optional[Dict]:
        """
        通过ID获取运动记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            运动记录字典，如果不存在则返回None
        """
        try:
            self._connect()
            
            self.cursor.execute("""
            SELECT * FROM exercise_records
            WHERE id = ?
            """, (record_id,))
            
            row = self.cursor.fetchone()
            if row:
                return dict(row)
            else:
                logger.warning(f"未找到ID为{record_id}的运动记录")
                return None
                
        except Exception as e:
            logger.exception(f"获取运动记录时出错: {str(e)}")
            return None
        finally:
            self._close()
    
    def get_location_points(self, record_id: int) -> List[Dict]:
        """
        获取运动记录关联的位置点
        
        Args:
            record_id: 运动记录ID
            
        Returns:
            位置点列表
        """
        try:
            self._connect()
            
            self.cursor.execute("""
            SELECT * FROM location_points
            WHERE record_id = ?
            ORDER BY timestamp ASC
            """, (record_id,))
            
            # 将查询结果转换为字典列表
            points = [dict(row) for row in self.cursor.fetchall()]
            
            logger.debug(f"获取到{len(points)}个位置点")
            return points
            
        except Exception as e:
            logger.exception(f"获取位置点时出错: {str(e)}")
            return []
        finally:
            self._close()
    
    def get_statistics(self, start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> Dict:
        """
        获取运动统计数据
        
        Args:
            start_date: 起始日期，格式为"YYYY-MM-DD"
            end_date: 结束日期，格式为"YYYY-MM-DD"
            
        Returns:
            统计数据字典
        """
        try:
            self._connect()
            
            query = """
            SELECT 
                COUNT(*) as total_count,
                SUM(distance) as total_distance,
                SUM(duration) as total_duration,
                AVG(avg_speed) as avg_speed,
                AVG(avg_heart_rate) as avg_heart_rate,
                SUM(calories) as total_calories
            FROM exercise_records
            """
            
            params = []
            if start_date or end_date:
                query += " WHERE "
                clauses = []
                
                if start_date:
                    clauses.append("date(timestamp) >= date(?)")
                    params.append(start_date)
                
                if end_date:
                    clauses.append("date(timestamp) <= date(?)")
                    params.append(end_date)
                
                query += " AND ".join(clauses)
            
            self.cursor.execute(query, params)
            row = self.cursor.fetchone()
            
            # 将查询结果转换为字典
            stats = dict(row)
            
            # 按活动类型统计
            self.cursor.execute("""
            SELECT 
                activity_type,
                activity_name,
                COUNT(*) as count,
                SUM(distance) as distance,
                SUM(duration) as duration
            FROM exercise_records
            GROUP BY activity_type
            ORDER BY count DESC
            """)
            
            stats['by_activity'] = [dict(row) for row in self.cursor.fetchall()]
            
            logger.debug(f"获取到运动统计数据")
            return stats
            
        except Exception as e:
            logger.exception(f"获取统计数据时出错: {str(e)}")
            return {
                'total_count': 0,
                'total_distance': 0,
                'total_duration': 0,
                'avg_speed': 0,
                'avg_heart_rate': 0,
                'total_calories': 0,
                'by_activity': []
            }
        finally:
            self._close()
    
    def delete_record(self, record_id: int) -> bool:
        """
        删除运动记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            是否成功删除
        """
        try:
            self._connect()
            
            # 检查记录是否存在
            self.cursor.execute("SELECT id FROM exercise_records WHERE id = ?", (record_id,))
            if not self.cursor.fetchone():
                logger.warning(f"未找到ID为{record_id}的运动记录")
                return False
            
            # 删除关联的位置点
            self.cursor.execute("DELETE FROM location_points WHERE record_id = ?", (record_id,))
            
            # 删除运动记录
            self.cursor.execute("DELETE FROM exercise_records WHERE id = ?", (record_id,))
            
            self.connection.commit()
            logger.info(f"已删除ID为{record_id}的运动记录")
            return True
            
        except Exception as e:
            logger.exception(f"删除运动记录时出错: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False
        finally:
            self._close()