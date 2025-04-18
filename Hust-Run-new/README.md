# Hust-Run - Android

华中大体育软件自动化辅助脚本，实现自动登录、自动开始运动、虚拟定位模拟运动等功能。

## 功能特性

- 自动登录：使用保存的账号密码自动登录华中大体育软件
- 自动开始运动：一键启动运动会话
- 虚拟位置模拟：自动修改 GPS 位置，模拟运动轨迹
- 运动轨迹定制：支持自定义运动路线
- 运动数据统计：记录和统计运动数据

## 安装与使用

### 环境要求

- Python 3.8 或更高版本
- Android Debug Bridge (ADB) 命令行工具
- 下载华中大体育，将 apk 文件直接拖拽到模拟器上即可

### 安装步骤

1. 克隆本仓库：

   ```
   git clone https://github.com/aDarkMaker/Hust-Run.git
   cd Hust-Run
   ```

2. 安装依赖：

   ```
   pip install -r requirements.txt
   ```

3. 配置个人信息：
   ```
   python setup.py
   ```

### 使用方法

1. 连接设备：

   ```
   python src/main.py connect
   ```

2. 自动运行所有功能：

   ```
   python src/main.py auto
   ```

3. 仅进行登录：

   ```
   python src/main.py login
   ```

4. 开始模拟运动：

   ```
   python src/main.py run
   ```

5. 查看帮助信息：
   ```
   python src/main.py --help
   ```

## 免责声明

本项目仅供学习研究，请勿商用，使用本项目需遵循相关法律法规。作者不对因使用本项目而导致的任何损失或后果负责。

## 项目结构

```
Hust-Run/
├── config/                   # 配置文件目录
│   ├── config.ini           # 主配置文件
│   └── routes/              # 预设路线目录
│       ├── default.json     # 默认运动路线
│       └── ...              # 其他自定义路线
├── data/                    # 数据存储目录
│   └── history.db           # 运动历史记录数据库
├── logs/                    # 日志目录
│   └── app.log              # 应用日志
├── src/                     # 源代码目录
│   ├── main.py              # 主程序入口
│   ├── login.py             # 登录模块
│   ├── location.py          # 位置模拟模块
│   ├── route_generator.py   # 路线生成器
│   ├── database.py          # 数据库操作
│   ├── utils/               # 工具函数目录
│   │   ├── adb_utils.py     # ADB操作工具
│   │   ├── config_utils.py  # 配置文件工具
│   │   └── logger.py        # 日志工具
│   └── gui/                 # 图形界面目录(可选) ——未实现
│       ├── main_window.py   # 主窗口
│       └── widgets.py       # 界面组件
├── tests/                   # 测试目录
│   ├── test_login.py        # 登录测试
│   └── test_location.py     # 位置模拟测试
├── setup.py                 # 初始化配置脚本
├── requirements.txt         # 项目依赖
└── README.md                # 项目说明文档
```

## 开发问题（这并不意味着上述项目结构废弃）

1. 软件版本不支持 64 位系统

华中大体育是一个基于 32x 位系统的较为低级的 java 项目，因此并不支持在高于 Android 9 以上的模拟器上进行运行，并且软件本身无法监听广播，因此无法通过 adb broadcast 进行模拟定位以及移动，因此基本放弃使用模拟器这一方案 ———— 2025.04.18

2. 解决问题

基于以上问题我们给出如下的解决方案，利用数据线连接使用的手机进行操作，这样可以解决华中大体育在模拟器 Android 9 环境下无法监听广播的情况，但是相应的限制了用户范围，尤其是使用 IOS 系统的用户，这意味着这个软件只会在 Windows + Android 框架下生效，但与之对应，这也是个小问题~

3. 目前理想框架

模拟 sever + main.py + 手机 + 数据线

4. 工作流程

- 手机通过数据线连接电脑
- 电脑通过 adb 系列指令创建虚拟的定位环境
- 模拟运动并完成（暂时不考虑自动化）

```
Hust-Run-new/
├── data/                    # 数据存储目录
│   └── history.db           # 运动历史记录数据库
├── logs/                    # 日志目录
│   └── app.log              # 应用日志
├── src/                     # 源代码目录
│   ├── main.py              # 主程序入口
│   ├── run.py               # 模拟运动
│   ├── creat_env.py         # 隔离操作系统
│   ├── logger.py            # 日志模块
│   ├── database.py          # 数据库操作
├── requirements.txt         # 项目依赖
└── README.md                # 项目说明文档
```
