#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import logging
import configparser
import time
import sys

class DeviceConnector:
    """实现与Android设备的连接与通信"""
    
    def __init__(self, config_path='config.ini'):
        """初始化连接器"""
        self.logger = logging.getLogger('HustRun.DeviceConnector')
        self.config = configparser.ConfigParser()
        self.config.read(config_path, encoding='utf-8')
        
        # 获取ADB配置
        self.adb_path = self._get_adb_path()
        self.device_id = self._get_device_id()
        self.logger.info(f"ADB路径: {self.adb_path}")
        self.logger.info(f"设备ID: {self.device_id}")
    
    def _get_adb_path(self):
        """获取ADB路径，如果配置为auto则自动查找"""
        adb_path = self.config.get('Device', 'adb_path')
        
        if adb_path.lower() == 'auto':
            # 尝试从环境变量中获取
            if os.system('adb version > nul 2>&1') == 0:
                return 'adb'
            
            # 常见的ADB安装路径
            common_paths = [
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'Sdk', 'platform-tools', 'adb.exe'),
                os.path.join(os.environ.get('ANDROID_HOME', ''), 'platform-tools', 'adb.exe'),
                os.path.join(os.environ.get('ANDROID_SDK_ROOT', ''), 'platform-tools', 'adb.exe'),
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    return path
                
            self.logger.error("无法找到ADB路径，请在config.ini中手动设置")
            sys.exit(1)
        
        return adb_path
    
    def _get_device_id(self):
        """获取设备ID，如果配置为auto则自动获取已连接的设备"""
        device_id = self.config.get('Device', 'device_id')
        
        if device_id.lower() == 'auto':
            # 获取已连接的设备列表
            try:
                result = subprocess.run(
                    [self.adb_path, 'devices'], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                
                lines = result.stdout.strip().split('\n')[1:]  # 跳过第一行"List of devices attached"
                devices = [line.split('\t')[0] for line in lines if '\t' in line and 'device' in line]
                
                if not devices:
                    self.logger.error("未找到已连接的设备，请检查USB连接")
                    sys.exit(1)
                
                if len(devices) > 1:
                    self.logger.warning(f"发现多个设备: {devices}，将使用第一个设备")
                
                return devices[0]
                
            except subprocess.CalledProcessError as e:
                self.logger.error(f"获取设备列表失败: {e}")
                sys.exit(1)
        
        return device_id
    
    def is_connected(self):
        """检查设备是否连接"""
        try:
            result = subprocess.run(
                [self.adb_path, '-s', self.device_id, 'shell', 'echo', 'connected'], 
                capture_output=True, 
                text=True,
                check=True
            )
            return 'connected' in result.stdout
        except subprocess.CalledProcessError:
            return False
    
    def wait_for_device(self, timeout=60):
        """等待设备连接，带超时"""
        self.logger.info(f"等待设备连接，超时时间: {timeout}秒")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_connected():
                self.logger.info("设备已连接")
                return True
            time.sleep(1)
            
        self.logger.error(f"等待设备连接超时（{timeout}秒）")
        return False
    
    def mock_location(self, latitude, longitude, package_name='net.crigh.hzkjsport'):
        """模拟位置，使用Android的模拟位置API直接设置
         参考参考.txt中MockLocationManager的实现方式
         """
        try:
            # 检查位置模拟权限
            self._check_mock_location_permission(package_name)
            
            # 第一种方式: 使用应用程序自身的LocationManager实现
            # 根据参考.txt中的代码，尝试通过发送特定意图让应用自行实现模拟位置
            cmd_app_mock = [
                self.adb_path, '-s', self.device_id, 'shell', 
                'am', 'broadcast', 
                '-a', 'net.crigh.hzkjsport.MOCK_LOCATION',
                '-e', 'latitude', str(latitude), 
                '-e', 'longitude', str(longitude),
                '-e', 'accuracy', '0.1',
                '-e', 'provider', 'gps',
                '-n', f'{package_name}/.receiver.LocationMockReceiver'
            ]
            
            # 第二种方式: 通过应用程序的服务接口发送模拟位置
            cmd_service = [
                self.adb_path, '-s', self.device_id, 'shell', 
                'am', 'startservice', 
                '-e', 'latitude', str(latitude), 
                '-e', 'longitude', str(longitude),
                '-e', 'accuracy', '3.0',
                '-n', f'{package_name}/.service.LocationMockService'
            ]
            
            # 第三种方式: 使用Android的geo fix命令直接模拟GPS位置
            # 注意：geo fix命令使用经度在前，纬度在后
            cmd_geo_fix = [
                self.adb_path, '-s', self.device_id, 'shell', 
                'geo', 'fix', str(longitude), str(latitude)
            ]
            
            # 第四种方式: 使用标准Android模拟位置广播
            cmd_android_mock = [
                self.adb_path, '-s', self.device_id, 'shell',
                'am', 'broadcast', 
                '-a', 'android.intent.action.MOCK_LOCATION',
                '-e', 'latitude', str(latitude), 
                '-e', 'longitude', str(longitude),
                '-e', 'accuracy', '0.1',
                '--ez', 'enabled', 'true'
            ]
            
            # 首先尝试设置应用的模拟位置权限
            try:
                appops_cmd = [
                    self.adb_path, '-s', self.device_id, 'shell', 
                    'appops', 'set', package_name, 'android:mock_location', 'allow'
                ]
                subprocess.run(appops_cmd, check=True, capture_output=True)
                self.logger.info("已设置应用的模拟位置权限")
            except subprocess.CalledProcessError:
                self.logger.warning("设置应用模拟位置权限失败，可能已经设置")
            
            success = False
            
            # 首先尝试应用特定的广播接收器方式（基于参考.txt）
            try:
                self.logger.info("尝试通过应用广播接收器发送模拟位置...")
                result = subprocess.run(cmd_app_mock, check=False, capture_output=True, text=True)
                if "Broadcast completed: result=0" in result.stdout:
                    self.logger.info("应用广播接收器方式发送模拟位置成功")
                    success = True
                else:
                    self.logger.warning(f"应用广播接收器方式失败: {result.stdout}")
            except Exception as e:
                self.logger.warning(f"应用广播接收器方式异常: {e}")
            
            # 如果应用广播接收器方式失败，尝试服务方式
            if not success:
                try:
                    self.logger.info("尝试通过服务方式发送模拟位置...")
                    result = subprocess.run(cmd_service, check=False, capture_output=True, text=True)
                    if "Error" not in result.stdout and result.returncode == 0:
                        self.logger.info("通过应用服务发送位置成功")
                        success = True
                    else:
                        self.logger.warning(f"通过应用服务发送位置失败: {result.stdout}")
                except Exception as e:
                    self.logger.warning(f"应用服务模拟位置异常: {e}")
            
            # 如果应用服务方式失败，尝试geo fix命令
            if not success:
                try:
                    self.logger.info("尝试通过geo fix命令发送模拟位置...")
                    result = subprocess.run(cmd_geo_fix, check=False, capture_output=True, text=True)
                    if result.returncode == 0:
                        self.logger.info("通过geo fix命令发送位置成功")
                        success = True
                    else:
                        self.logger.warning(f"通过geo fix命令发送位置失败: {result.stdout}")
                except Exception as e:
                    self.logger.warning(f"geo fix模拟位置异常: {e}")
            
            # 如果以上方法都失败，尝试Android标准模拟位置广播
            if not success:
                try:
                    self.logger.info("尝试通过Android标准广播发送模拟位置...")
                    result = subprocess.run(cmd_android_mock, check=False, capture_output=True, text=True)
                    if "Broadcast completed: result=0" in result.stdout:
                        self.logger.info("Android标准广播发送模拟位置成功")
                        success = True
                    else:
                        self.logger.warning(f"Android标准广播发送模拟位置失败: {result.stdout}")
                except Exception as e:
                    self.logger.warning(f"Android标准广播模拟位置异常: {e}")
            
            # 作为最后的尝试，提示用户使用第三方应用
            if not success:
                self.logger.warning("所有模拟位置方法都失败，建议尝试使用第三方模拟位置应用")
                print("\n警告：自动模拟位置失败！您可能需要：")
                print("1. 确保已在开发者选项中将华中科技大学体育应用设置为模拟位置应用")
                print("2. 尝试使用第三方模拟位置应用（如Fake GPS或Mock Locations）")
                print("3. 如果您已经安装了第三方模拟位置应用，请在该应用中设置位置后再尝试\n")
                if input("是否继续尝试运行？(y/n): ").lower() != 'y':
                    return False
                
                # 继续尝试，但返回True以继续执行，由应用自行处理位置
                success = True
            
            return success
            
        except Exception as e:
            self.logger.error(f"模拟位置失败: {e}")
            return False
    
    def _check_mock_location_permission(self, package_name):
        """检查应用是否有模拟位置权限"""
        try:
            # 1. 检查开发者选项是否启用
            dev_settings = subprocess.run(
                [self.adb_path, '-s', self.device_id, 'shell', 'settings', 'get', 'global', 'development_settings_enabled'],
                capture_output=True, text=True, check=True
            )
            
            if '1' not in dev_settings.stdout:
                self.logger.warning("开发者选项未启用，尝试启用...")
                subprocess.run(
                    [self.adb_path, '-s', self.device_id, 'shell', 'settings', 'put', 'global', 'development_settings_enabled', '1'],
                    check=True
                )
            
            # 2. 检查模拟位置应用设置
            mock_app = subprocess.run(
                [self.adb_path, '-s', self.device_id, 'shell', 'settings', 'get', 'secure', 'mock_location'],
                capture_output=True, text=True
            )
            
            # 如果未设置或不是目标应用
            if package_name not in mock_app.stdout and 'net.crigh.hzkjsport' not in mock_app.stdout:
                self.logger.warning("应用未设置为模拟位置应用，请在开发者选项中手动设置")
                # 显示一条提示
                print("\n请在手机的开发者选项中将'选择模拟位置信息应用'设置为'华中科技大学体育'应用\n")
                input("设置完成后按回车键继续...")
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"检查模拟位置权限失败: {e}")
            
    def install_app(self, apk_path):
        """安装APK"""
        try:
            self.logger.info(f"正在安装应用: {apk_path}")
            result = subprocess.run(
                [self.adb_path, '-s', self.device_id, 'install', '-r', apk_path],
                capture_output=True, text=True, check=True
            )
            self.logger.info("安装成功")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"安装应用失败: {e.stdout}")
            return False
            
    def start_app(self, package_name='net.crigh.hzkjsport'):
        """启动应用"""
        try:
            self.logger.info(f"启动应用: {package_name}")
            subprocess.run(
                [self.adb_path, '-s', self.device_id, 'shell', 'monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1'],
                capture_output=True, check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"启动应用失败: {e}")
            return False

# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    connector = DeviceConnector()
    
    if connector.wait_for_device(30):
        print("设备连接成功!")
    else:
        print("设备连接失败")