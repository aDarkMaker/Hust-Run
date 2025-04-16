#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
位置模拟模块测试
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.location import LocationSimulator
from src.utils.adb_utils import ADBController
from src.utils.config_utils import ConfigManager

class TestLocationSimulator(unittest.TestCase):
    """位置模拟器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟对象
        self.mock_adb = MagicMock(spec=ADBController)
        self.mock_config = MagicMock(spec=ConfigManager)
        
        # 设置模拟返回值
        self.mock_config.get.return_value = "gps"
        self.mock_config.get_float.return_value = 10.0
        
        # 创建测试对象
        self.location_simulator = LocationSimulator(self.mock_adb, self.mock_config)
    
    def test_enable_mock_location(self):
        """测试启用模拟位置"""
        # 设置模拟返回值
        self.mock_adb.shell.return_value = "success"
        self.mock_config.get.return_value = "com.hust.sport"
        
        result = self.location_simulator.enable_mock_location()
        
        self.assertTrue(result, "启用模拟位置应成功")
        self.assertTrue(self.location_simulator.is_mocking, "is_mocking标志应为True")
        
        # 验证调用
        self.mock_adb.shell.assert_any_call("appops set com.hust.sport android:mock_location allow")
        self.mock_adb.shell.assert_any_call("settings put secure mock_location 1")
    
    def test_disable_mock_location(self):
        """测试禁用模拟位置"""
        # 设置初始状态
        self.location_simulator.is_mocking = True
        
        # 设置模拟返回值
        self.mock_adb.shell.return_value = "success"
        self.mock_config.get.return_value = "com.hust.sport"
        
        result = self.location_simulator.disable_mock_location()
        
        self.assertTrue(result, "禁用模拟位置应成功")
        self.assertFalse(self.location_simulator.is_mocking, "is_mocking标志应为False")
        
        # 验证调用
        self.mock_adb.shell.assert_any_call("appops set com.hust.sport android:mock_location default")
        self.mock_adb.shell.assert_any_call("settings put secure mock_location 0")
    
    def test_set_location(self):
        """测试设置位置"""
        # 设置模拟返回值
        self.mock_adb.shell.return_value = "success"
        
        # 测试位置
        latitude = 30.513137
        longitude = 114.421432
        altitude = 20.0
        
        result = self.location_simulator.set_location(latitude, longitude, altitude)
        
        self.assertTrue(result, "设置位置应成功")
        
        # 验证调用
        self.mock_adb.shell.assert_any_call(f"geo fix {longitude} {latitude} {altitude}")
        
        # 验证当前位置是否更新
        self.assertIsNotNone(self.location_simulator.current_location, "当前位置应被更新")
        self.assertEqual(self.location_simulator.current_location['latitude'], latitude, "纬度应匹配")
        self.assertEqual(self.location_simulator.current_location['longitude'], longitude, "经度应匹配")
        self.assertEqual(self.location_simulator.current_location['altitude'], altitude, "海拔应匹配")
    
    @patch('time.sleep')
    def test_move_to(self, mock_sleep):
        """测试移动到目标位置"""
        # 设置当前位置
        self.location_simulator.current_location = {
            'latitude': 30.513137,
            'longitude': 114.421432,
            'altitude': 20.0,
            'timestamp': 1234567890
        }
        
        # 模拟set_location方法
        self.location_simulator.set_location = MagicMock(return_value=True)
        
        # 测试目标位置
        target_lat = 30.514000
        target_lng = 114.423000
        speed = 1.0  # 1米/秒
        steps = 5
        
        result = self.location_simulator.move_to(target_lat, target_lng, speed, steps)
        
        self.assertTrue(result, "移动到目标位置应成功")
        
        # 验证调用次数
        self.assertEqual(self.location_simulator.set_location.call_count, steps, f"set_location应被调用{steps}次")
        mock_sleep.assert_called()
    
    def test_simulate_heart_rate(self):
        """测试模拟心率"""
        # 设置当前位置和时间戳
        self.location_simulator.current_location = {
            'latitude': 30.513137,
            'longitude': 114.421432,
            'altitude': 20.0,
            'timestamp': 1234567890
        }
        
        # 设置活动类型
        self.mock_config.get_int.return_value = 0  # 跑步
        
        heart_rate = self.location_simulator.simulate_heart_rate()
        
        self.assertIsInstance(heart_rate, int, "心率应为整数")
        self.assertGreaterEqual(heart_rate, 60, "心率应大于等于60")
        self.assertLessEqual(heart_rate, 180, "心率应小于等于180")
    
    def test_check_developer_options(self):
        """测试检查开发者选项"""
        # 模拟开发者选项已启用
        self.mock_adb.shell.side_effect = ["1", "1"]
        
        result = self.location_simulator._check_developer_options()
        
        self.assertTrue(result, "检查开发者选项应返回True")
        
        # 模拟开发者选项未启用
        self.mock_adb.shell.side_effect = ["0", "0"]
        
        result = self.location_simulator._check_developer_options()
        
        self.assertFalse(result, "检查开发者选项应返回False")


if __name__ == '__main__':
    unittest.main()