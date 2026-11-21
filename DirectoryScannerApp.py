import os
import sys
import pickle  # 用于保存扫描状态

# 设置环境变量屏蔽PyTorch
os.environ['TORCH_DYNAMO'] = '0'
os.environ['TORCH_COMPILE_DEBUG'] = '0'
os.environ['PYTORCH_NO_CUDA_MEMORY_CACHING'] = '1'
os.environ['PYTORCH_JIT'] = '0'

# 强制屏蔽PyTorch模块导入
import builtins
original_import = builtins.__import__

def block_torch_import(name, *args, **kwargs):
    """阻止PyTorch相关模块导入"""
    blocked_modules = [
        'torch', 'torchvision', 'torchaudio',
        'torch._dynamo', 'torch._inductor', 'torch._functorch',
        'torch._lazy', 'torch.compiler', 'torch.fx',
        'tensorflow', 'tensorflow_core',
        'cupy', 'cupyx',
        'Cython', 'Cython.Compiler'
    ]
    
    for blocked in blocked_modules:
        if name == blocked or name.startswith(blocked + '.'):
            # 返回一个空模块
            class EmptyModule:
                __all__ = []
                def __getattr__(self, _):
                    return None
                def __call__(self, *args, **kwargs):
                    return None
            return EmptyModule()
    
    return original_import(name, *args, **kwargs)

builtins.__import__ = block_torch_import

os.environ['QT_LOGGING_RULES'] = 'qt.gui.icc.warning=false'




import shutil
import sqlite3
import datetime
import time
import re
import hashlib
import subprocess
import http.server
import socketserver
import threading
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from PySide6.QtCore import (QObject, Signal, Slot, QTimer, QDateTime, QSize, 
                             QSettings, QThread, QMetaObject, Q_ARG, Qt, QDate, 
                             QTime, QRect, QPoint)
from PySide6.QtGui import QIcon, QColor, QFont, QPixmap, QBrush, QAction
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QDialog, QComboBox, QSpinBox, 
                             QCheckBox, QFileDialog, QTabWidget, QGridLayout, QGroupBox,
                             QDateEdit, QToolButton, QSizePolicy, QStackedWidget,
                             QMenu, QSystemTrayIcon, QScrollArea, QInputDialog, QFrame, 
                             QTextEdit, QProgressDialog, QProgressBar, QTreeWidget, QTreeWidgetItem,
                             QListWidget, QListWidgetItem, QLayout)
# PySide6的SQL模块（按需使用）
from PySide6.QtSql import QSqlDatabase, QSqlQuery

import json
import urllib.parse
from http import HTTPStatus
from threading import Lock
import queue

# 添加拼音转换库
try:
    from pypinyin import pinyin, Style
except ImportError:
    # 如果没有安装pypinyin，使用简单的拼音映射
    pinyin_available = False
else:
    pinyin_available = True

# 全局变量标记库是否可用
TORCH_AVAILABLE = False
TENSORFLOW_AVAILABLE = False
# 库实例缓存
_torch_instance = None
_tensorflow_instance = None
def lazy_import_torch():
    """延迟导入PyTorch，只在需要时加载"""
    global TORCH_AVAILABLE, _torch_instance
    
    if _torch_instance is not None:
        return _torch_instance
        
    try:
        import torch
        TORCH_AVAILABLE = True
        _torch_instance = torch
        print("PyTorch loaded successfully")
        return torch
    except ImportError:
        TORCH_AVAILABLE = False
        print("PyTorch not available, skipping...")
        return None
def lazy_import_tensorflow():
    """延迟导入TensorFlow，只在需要时加载"""
    global TENSORFLOW_AVAILABLE, _tensorflow_instance
    
    if _tensorflow_instance is not None:
        return _tensorflow_instance
        
    try:
        import tensorflow
        TENSORFLOW_AVAILABLE = True
        _tensorflow_instance = tensorflow
        print("TensorFlow loaded successfully")
        return tensorflow
    except ImportError:
        TENSORFLOW_AVAILABLE = False
        print("TensorFlow not available, skipping...")
        return None
def is_torch_available():
    """检查PyTorch是否可用"""
    return TORCH_AVAILABLE
def is_tensorflow_available():
    """检查TensorFlow是否可用"""
    return TENSORFLOW_AVAILABLE
# 如果需要，还可以添加工具函数来安全地使用这些库
def safe_torch_operation(func):
    """安全执行PyTorch操作的装饰器"""
    def wrapper(*args, **kwargs):
        if not TORCH_AVAILABLE:
            lazy_import_torch()
        if TORCH_AVAILABLE:
            return func(*args, **kwargs)
        else:
            print("PyTorch operation skipped: PyTorch not available")
            return None
    return wrapper
def safe_tensorflow_operation(func):
    """安全执行TensorFlow操作的装饰器"""
    def wrapper(*args, **kwargs):
        if not TENSORFLOW_AVAILABLE:
            lazy_import_tensorflow()
        if TENSORFLOW_AVAILABLE:
            return func(*args, **kwargs)
        else:
            print("TensorFlow operation skipped: TensorFlow not available")
            return None
    return wrapper



class ProjectInfo:
    """项目信息元数据（集中管理所有项目相关信息）"""
    VERSION = "4.2.1"
    BUILD_DATE = "2026-10-16"
    # 注意：本项目只 import datetime 模块，模块级没有 now/strptime 等函数，
    # 必须写成 datetime.datetime.now() / datetime.datetime.strptime() /
    # datetime.datetime.fromtimestamp()；绝不能写成 datetime.now()（本机
    # Python 3.10 会抛 AttributeError: module 'datetime' has no attribute 'now'）。
    # 同理禁止 from datetime import datetime —— 那会把模块名 datetime 覆盖成类，
    # 令 datetime.datetime.now() 抛 AttributeError:
    # type object 'datetime.datetime' has no attribute 'datetime'。
    # 本项目实际可用的写法只有一种：import datetime + datetime.datetime.*。
    AUTHOR = "杜玛"
    LICENSE = "MIT"
    COPYRIGHT = "© 永久 杜玛"
    URL = "https://github.com/duma520"
    MAINTAINER_EMAIL = "不提供"
    NAME = "目录扫描管理系统"
    DESCRIPTION = "目录扫描管理系统是一个用于扫描和管理文件系统目录的应用程序，支持多用户和自动备份功能。"

    # 补充完整的版本历史
    VERSION_HISTORY = {
        "4.2.1": "修复 datetime 时间调用：移除 from datetime import datetime, date 恢复 import datetime，并把全部时间调用统一为 datetime.datetime.* 形式（本机模块级 datetime.now 不存在），修复登录/备份/扫描等报 AttributeError",
        "4.2.0": "补齐归档：将已在主程序落地、原 v4.1 记录中描述但未同步进 version\\ 的性能重写正式归档（_pixmap_cache/_cover_cache 改 OrderedDict 真 LRU、find_directory_cover 改单次 listdir 小写集合匹配、移除 main 块重复的 init_server），并清理 __pycache__ 构建残留，使主程序与 version\\ 备份逐字节一致",
        "4.1.0": "全面性能优化：用户库缺失索引自动补齐（keyset 分页 ≈14x）、扫描状态去 O(N^2)（内存字典+批量落盘）、表格占位符样式共用化（≈1.5x）、修复状态文件复活与索引检查线程安全",
        "3.9.0": "全面升级多线程操作，优化多线程扫描性能，提升大目录处理速度",
        "2.91.0": "web客户端增加在线看视频，pdf，epub等功能",
        "2.79.0": "web客户端改为纯HTML5格式，提升兼容性和性能",
        "2.62.0": "增加Web客户端访问功能，支持远程管理",
        "2.53.0": "优化扫描性能，提升用户体验",
        "2.51.0": "后台扫描也显示进度条",
        "2.42.0": "增强保存封面，扫描进度条",
        "2.33.0": "增强图片点击查看功能",
        "2.27.0": "增强拼音搜索功能，优化数据库性能，修复扫描模式设置问题",
        "2.8.0": "添加多用户支持，改进UI界面，增加主目录管理功能",
        "1.4.0": "添加自动备份和恢复功能，支持数据库回滚",
        "1.3.0": "优化目录扫描算法，支持图片预览和缩略图显示",
        "1.2.0": "添加拼音搜索支持，改进搜索体验",
        "1.1.0": "基础目录扫描功能，支持SQLite数据库存储"
    }
    
    # 补充完整的使用说明
    @classmethod
    def get_help_text(cls) -> str:
        """获取完整的帮助文本"""
        return f"""
使用说明:

版本: {cls.VERSION}
作者: {cls.AUTHOR}

主要功能:
1. 多用户目录管理 - 支持多个用户独立管理各自的目录
2. 智能拼音搜索 - 支持中文拼音首字母搜索
3. 自动备份恢复 - 定期自动备份数据库，支持手动恢复
4. 图片预览功能 - 自动识别并预览目录中的图片
5. 可配置扫描 - 支持设置扫描深度和过滤条件
6. 实时进度显示 - 任何扫描活动都会显示详细进度条

使用步骤:
1. 首次使用请创建或选择用户
2. 在"主目录管理"中添加要扫描的目录
3. 设置扫描深度和扫描模式
4. 点击"扫描目录"开始扫描
5. 使用搜索框快速查找目录或文件

扫描模式说明:
- 仅扫描目录: 只扫描文件夹，忽略文件
- 仅扫描文件: 只扫描文件，忽略文件夹  
- 扫描目录和文件: 同时扫描文件夹和文件

进度条说明:
- 文件系统扫描 (0-30%): 正在遍历目录结构
- 数据库保存 (30-50%): 正在保存扫描结果到数据库
- 创建备份 (50-70%): 正在创建数据库备份
- 封面保存 (70-90%): 正在保存封面图片
- 完成 (100%): 扫描完成

搜索功能:
- 支持中文名称搜索
- 支持拼音首字母搜索 (如: "wj" 可匹配 "文件夹")
- 支持路径关键词搜索

快捷键:
- 回车: 执行搜索
- 工具栏按钮提供主要功能入口

数据管理:
- 自动备份: 系统会自动备份数据库
- 手动备份: 可通过"数据库备份"手动创建备份
- 数据恢复: 支持从备份文件恢复数据
- 清除数据: 可清除用户的扫描记录

技术支持: {cls.URL}
"""



    # 新增：技术栈信息
    TECHNOLOGY_STACK = {
        "language": "Python 3.x",
        "gui_framework": "PySide6",  # 改为PySide6
        "database": "SQLite3",
        "features": ["多用户支持", "自动备份", "拼音搜索", "图片预览", "目录管理"]
    }

    # 新增：系统要求
    SYSTEM_REQUIREMENTS = {
        "os": "Windows 7+/macOS 10.12+/Linux",
        "python": "Python 3.6+",
        "memory": "至少 512MB RAM",
        "storage": "至少 100MB 可用空间"
    }

    # 新增：依赖库
    DEPENDENCIES = [
        "PySide6 >= 6.5.0",  # 改为PySide6
        "pypinyin >= 0.48.0 (可选)"
    ]

    @classmethod
    def get_metadata(cls) -> dict:
        """获取主要元数据字典"""
        return {
            'version': cls.VERSION,
            'author': cls.AUTHOR,
            'license': cls.LICENSE,
            'url': cls.URL
        }

    @classmethod
    def get_header(cls) -> str:
        """生成标准化的项目头信息"""
        return f"{cls.NAME} {cls.VERSION} | {cls.LICENSE} License | {cls.URL}"

    @classmethod
    def get_about_info(cls):
        """获取ABOUT信息字典"""
        return {
            "name": cls.NAME,
            "version": cls.VERSION,
            "build_date": cls.BUILD_DATE,
            "author": cls.AUTHOR,
            "license": cls.LICENSE,
            "copyright": cls.COPYRIGHT,
            "url": cls.URL,
            "description": cls.DESCRIPTION,
            "features": [
                "多用户目录管理",
                "智能拼音搜索",
                "自动备份恢复",
                "图片预览功能",
                "可配置扫描深度",
                "实时状态监控"
            ]
        }

    @classmethod
    def get_technical_info(cls) -> dict:
        """获取技术信息"""
        return {
            "technology_stack": cls.TECHNOLOGY_STACK,
            "system_requirements": cls.SYSTEM_REQUIREMENTS,
            "dependencies": cls.DEPENDENCIES
        }

    @classmethod
    def get_version_history(cls) -> dict:
        """获取版本历史（需要补充详细信息）"""
        # 这里可以补充每个版本的详细更新内容
        detailed_history = {
            "2.27.0": "增强拼音搜索功能，优化数据库性能",
            "2.8.0": "添加多用户支持，改进UI界面",
            "1.4.0": "添加自动备份和恢复功能",
            "1.3.0": "优化目录扫描算法，支持图片预览",
            "1.2.0": "添加拼音搜索支持",
            "1.1.0": "基础目录扫描功能"
        }
        return detailed_history

    @classmethod
    def get_help_text(cls) -> str:
        """获取完整的帮助文本"""
        return f"""
{cls.NAME} 使用说明

版本: {cls.VERSION}
作者: {cls.AUTHOR}

主要功能:
1. 多用户目录管理 - 支持多个用户独立管理各自的目录
2. 智能拼音搜索 - 支持中文拼音首字母搜索
3. 自动备份恢复 - 定期自动备份数据库，支持手动恢复
4. 图片预览功能 - 自动识别并预览目录中的图片
5. 可配置扫描 - 支持设置扫描深度和过滤条件

使用步骤:
1. 首次使用请创建或选择用户
2. 添加主目录并设置扫描深度
3. 点击扫描按钮开始扫描
4. 使用搜索框快速查找目录

快捷键:
- 回车: 执行搜索
- 工具栏按钮提供主要功能入口

技术支持: {cls.URL}
"""

    @classmethod
    def to_dict(cls) -> dict:
        """将项目信息转换为完整字典"""
        return {
            'basic_info': cls.get_about_info(),
            'technical_info': cls.get_technical_info(),
            'version_history': cls.get_version_history(),
            'help_text': cls.get_help_text()
        }

    @classmethod
    def display_info(cls):
        """在控制台显示项目信息（用于调试）"""
        info = cls.to_dict()
        print(f"=== {cls.NAME} 项目信息 ===")
        print(f"版本: {cls.VERSION}")
        print(f"构建日期: {cls.BUILD_DATE}")
        print(f"作者: {cls.AUTHOR}")
        print(f"许可证: {cls.LICENSE}")
        print(f"项目地址: {cls.URL}")
        print(f"描述: {cls.DESCRIPTION}")
        print("=" * 50)


# 马卡龙色系定义 360色全色域
class MacaronColors:
    # 马卡龙色系 360色全色域
    PEACH_BLOSSOM = QColor('#F4A8B0')  # 桃红色
    PINK_BLOSSOM = QColor('#F2A9A9') #粉红花
    PINK_CORAL = QColor('#F2A6A4') #粉珊瑚
    PEACH_BLUSH = QColor('#F2A29F') #桃腮红
    SALMON_PINK = QColor('#F19F9B') #鲑鱼粉
    WARM_PEACH = QColor('#F19C96') #暖桃色
    SOFT_APRICOT = QColor('#F19991') #柔杏色
    PEACH_MELBA = QColor('#F1978D') #蜜桃梅尔巴
    CORAL_REEF = QColor('#F09589') #珊瑚礁
    PEACH_SORBET = QColor('#F09385') #桃雪酪
    APRICOT_CREAM = QColor('#EF9282') #杏奶油
    PEACHY_PINK = QColor('#EF917F') #桃粉色
    SUNSET_PINK = QColor('#EE917C') #日落粉
    WARM_SALMON = QColor('#ED917A') #暖鲑色
    SOFT_CORAL = QColor('#ED9178') #柔珊瑚
    PEACH_GLOW = QColor('#EC9276') #桃光色
    CORAL_BLUSH = QColor('#EB9375') #珊瑚腮红
    PEACH_NECTAR = QColor('#EA9475') #桃蜜色
    APRICOT_GLOW = QColor('#E99675') #杏光色
    WARM_APRICOT = QColor('#E89875') #暖杏色
    PEACH_SUNSET = QColor('#E79A76') #桃日落
    SOFT_PEACH = QColor('#E69C77') #柔桃色
    PEACH_HINT = QColor('#E59E78') #桃暗示
    CORAL_SUNSET = QColor('#E4A17A') #珊瑚日落
    WARM_CORAL = QColor('#E3A47D') #暖珊瑚
    PEACH_TWILIGHT = QColor('#E1A67F') #桃暮色
    SOFT_SUNSET = QColor('#E0A982') #柔日落
    PEACH_SKY = QColor('#DFAC85') #桃天色
    WARM_SUNSET = QColor('#DEAF88') #暖日落
    PEACH_MIST = QColor('#DDB18B') #桃雾
    SOFT_AMBER = QColor('#DBB48F') #柔琥珀
    PEACH_HONEY = QColor('#DAB692') #桃蜜色
    WARM_BEIGE = QColor('#D9B896') #暖米色
    PEACH_CREAM = QColor('#D8BA99') #桃奶油
    SOFT_SAND = QColor('#D6BC9D') #柔沙色
    WARM_IVORY = QColor('#D5BEA0') #暖象牙
    PEACH_PALE = QColor('#D4BFA3') #淡桃色
    SOFT_LATTE = QColor('#D2C1A6') #柔拿铁
    WARM_ALMOND = QColor('#D1C2A9') #暖杏仁
    PEACH_MILK = QColor('#D0C2AB') #桃奶色
    SOFT_CREAM = QColor('#CFC3AD') #柔奶油
    WARM_MILK = QColor('#CEC3AF') #暖奶色
    PEACH_POWDER = QColor('#CCC4B1') #桃粉
    SOFT_POWDER = QColor('#CBC4B2') #柔粉
    WARM_POWDER = QColor('#CAC4B3') #暖粉
    PEACH_FROST = QColor('#C9C3B3') #桃霜
    SOFT_FROST = QColor('#C8C3B3') #柔霜
    WARM_FROST = QColor('#C7C3B3') #暖霜
    PEACH_MIST_LIGHT = QColor('#C6C2B2') #淡桃雾
    SOFT_MIST = QColor('#C5C1B1') #柔雾
    WARM_MIST = QColor('#C5C1B0') #暖雾
    PEACH_CLOUD = QColor('#C4C0AF') #桃云
    SOFT_CLOUD = QColor('#C3C0AD') #柔云
    WARM_CLOUD = QColor('#C2BFAA') #暖云
    PEACH_SKY_LIGHT = QColor('#C2BFA8') #淡桃天
    SOFT_SKY = QColor('#C1BEA5') #柔天
    WARM_SKY = QColor('#C1BEA2') #暖天
    PEACH_DAWN = QColor('#C0BE9F') #桃黎明
    SOFT_DAWN = QColor('#C0BE9B') #柔黎明
    WARM_DAWN = QColor('#BFBE98') #暖黎明
    PEACH_MORNING = QColor('#BFBE94') #桃晨光
    SOFT_MORNING = QColor('#BFBF90') #柔晨光
    WARM_MORNING = QColor('#BEBF8C') #暖晨光
    PEACH_SUN = QColor('#BDBF89') #桃阳光
    SOFT_SUN = QColor('#BCBF85') #柔阳光
    WARM_SUN = QColor('#BBBF81') #暖阳光
    PEACH_LEMON = QColor('#B9BF7D') #桃柠檬
    SOFT_LEMON = QColor('#B8BF7A') #柔柠檬
    WARM_LEMON = QColor('#B7BF76') #暖柠檬
    PEACH_LIME = QColor('#B5C073') #桃青柠
    SOFT_LIME = QColor('#B4C070') #柔青柠
    WARM_LIME = QColor('#B3C06D') #暖青柠
    PEACH_SPRING = QColor('#B1C16B') #桃春
    SOFT_SPRING = QColor('#B0C168') #柔春
    WARM_SPRING = QColor('#AEC267') #暖春
    PEACH_FRESH = QColor('#ADC365') #桃清新
    SOFT_FRESH = QColor('#ABC364') #柔清新
    WARM_FRESH = QColor('#AAC463') #暖清新
    PEACH_YOUNG = QColor('#A9C563') #桃青春
    SOFT_YOUNG = QColor('#A8C663') #柔青春
    WARM_YOUNG = QColor('#A7C763') #暖青春
    PEACH_VIBRANT = QColor('#A6C864') #桃活力
    SOFT_VIBRANT = QColor('#A6C965') #柔活力
    WARM_VIBRANT = QColor('#A5CA67') #暖活力
    PEACH_ZEST = QColor('#A5CB69') #桃热情
    SOFT_ZEST = QColor('#A5CC6C') #柔热情
    WARM_ZEST = QColor('#A6CD6E') #暖热情
    PEACH_RADIANT = QColor('#A6CE72') #桃灿烂
    SOFT_RADIANT = QColor('#A7CF75') #柔灿烂
    WARM_RADIANT = QColor('#A8D079') #暖灿烂
    PEACH_SUNNY = QColor('#A9D27E') #桃晴朗
    SOFT_SUNNY = QColor('#AAD382') #柔晴朗
    WARM_SUNNY = QColor('#ACD487') #暖晴朗
    PEACH_BRIGHT = QColor('#AED58C') #桃明亮
    SOFT_BRIGHT = QColor('#B0D791') #柔明亮
    WARM_BRIGHT = QColor('#B3D896') #暖明亮
    PEACH_LUSH = QColor('#B5D99B') #桃茂盛
    SOFT_LUSH = QColor('#B8DAA0') #柔茂盛
    WARM_LUSH = QColor('#BADCA6') #暖茂盛
    PEACH_JUICY = QColor('#BDDDAB') #桃多汁
    SOFT_JUICY = QColor('#C0DEB0') #柔多汁
    WARM_JUICY = QColor('#C3DFB5') #暖多汁
    PEACH_CRISP = QColor('#C6E1B9') #桃清脆
    SOFT_CRISP = QColor('#C9E2BE') #柔清脆
    WARM_CRISP = QColor('#CBE3C2') #暖清脆
    PEACH_REFRESH = QColor('#CEE4C5') #桃清新
    SOFT_REFRESH = QColor('#D0E5C9') #柔清新
    WARM_REFRESH = QColor('#D2E6CC') #暖清新
    PEACH_PURE = QColor('#D4E7CE') #桃纯净
    SOFT_PURE = QColor('#D5E8D0') #柔纯净
    WARM_PURE = QColor('#D6E9D2') #暖纯净
    PEACH_CLEAR = QColor('#D7EAD3') #桃清澈
    SOFT_CLEAR = QColor('#D7EBD3') #柔清澈
    WARM_CLEAR = QColor('#D7ECD3') #暖清澈
    PEACH_MINT = QColor('#D6EDD3') #桃薄荷
    SOFT_MINT = QColor('#D5EED2') #柔薄荷
    WARM_MINT = QColor('#D3EED0') #暖薄荷
    PEACH_COOL = QColor('#D1EFCE') #桃凉爽
    SOFT_COOL = QColor('#CEEFCC') #柔凉爽
    WARM_COOL = QColor('#CAF0C9') #暖凉爽
    PEACH_FROSTY = QColor('#C7F0C6') #桃霜白
    SOFT_FROSTY = QColor('#C2F1C2') #柔霜白
    WARM_FROSTY = QColor('#BEF1BF') #暖霜白
    PEACH_ICE = QColor('#BAF1BC') #桃冰
    SOFT_ICE = QColor('#B6F2B9') #柔冰
    WARM_ICE = QColor('#B1F2B5') #暖冰
    PEACH_AQUA = QColor('#ACF2B2') #桃水色
    SOFT_AQUA = QColor('#A7F2AF') #柔水色
    WARM_AQUA = QColor('#A3F2AC') #暖水色
    PEACH_SPA = QColor('#9EF2A9') #桃温泉
    SOFT_SPA = QColor('#99F1A6') #柔温泉
    WARM_SPA = QColor('#94F1A4') #暖温泉
    PEACH_DEW = QColor('#90F1A2') #桃露珠
    SOFT_DEW = QColor('#8CF0A0') #柔露珠
    WARM_DEW = QColor('#88F09E') #暖露珠
    PEACH_FRESHNESS = QColor('#84F09D') #桃新鲜
    SOFT_FRESHNESS = QColor('#81EF9C') #柔新鲜
    WARM_FRESHNESS = QColor('#7EEE9C') #暖新鲜
    PEACH_SPROUT = QColor('#7BEE9C') #桃新芽
    SOFT_SPROUT = QColor('#79ED9C') #柔新芽
    WARM_SPROUT = QColor('#77EC9C') #暖新芽
    PEACH_GROWTH = QColor('#76EB9D') #桃成长
    SOFT_GROWTH = QColor('#75EB9E') #柔成长
    WARM_GROWTH = QColor('#75EAA0') #暖成长
    PEACH_VITALITY = QColor('#75E9A1') #桃活力
    SOFT_VITALITY = QColor('#75E8A3') #柔活力
    WARM_VITALITY = QColor('#76E7A5') #暖活力
    PEACH_SPRINGTIME = QColor('#77E6A7') #桃春日
    SOFT_SPRINGTIME = QColor('#79E5A9') #柔春日
    WARM_SPRINGTIME = QColor('#7BE3AC') #暖春日
    PEACH_MEADOW = QColor('#7DE2AE') #桃草地
    SOFT_MEADOW = QColor('#80E1B1') #柔草地
    WARM_MEADOW = QColor('#83E0B3') #暖草地
    PEACH_PASTURE = QColor('#86DFB5') #桃牧场
    SOFT_PASTURE = QColor('#89DDB8') #柔牧场
    WARM_PASTURE = QColor('#8DDCBA') #暖牧场
    PEACH_FIELD = QColor('#90DBBC') #桃田野
    SOFT_FIELD = QColor('#93DABE') #柔田野
    WARM_FIELD = QColor('#97D8BF') #暖田野
    PEACH_GARDEN = QColor('#9AD7C1') #桃花园
    SOFT_GARDEN = QColor('#9ED6C2') #柔花园
    WARM_GARDEN = QColor('#A1D5C3') #暖花园
    PEACH_PARK = QColor('#A4D3C4') #桃公园
    SOFT_PARK = QColor('#A7D2C5') #柔公园
    WARM_PARK = QColor('#A9D1C6') #暖公园
    PEACH_LAKE = QColor('#ACD0C6') #桃湖
    SOFT_LAKE = QColor('#AECEC6') #柔湖
    WARM_LAKE = QColor('#B0CDC6') #暖湖
    PEACH_OCEAN = QColor('#B1CCC6') #桃海洋
    SOFT_OCEAN = QColor('#B2CBC6') #柔海洋
    WARM_OCEAN = QColor('#B3CAC6') #暖海洋
    PEACH_WAVE = QColor('#B3C9C5') #桃波浪
    SOFT_WAVE = QColor('#B3C8C5') #柔波浪
    WARM_WAVE = QColor('#B3C7C4') #暖波浪
    PEACH_TIDE = QColor('#B2C6C4') #桃潮汐
    SOFT_TIDE = QColor('#B1C5C3') #柔潮汐
    WARM_TIDE = QColor('#B0C4C3') #暖潮汐
    PEACH_CURRENT = QColor('#AEC4C2') #桃洋流
    SOFT_CURRENT = QColor('#ACC3C2') #柔洋流
    WARM_CURRENT = QColor('#AAC2C1') #暖洋流
    PEACH_MARINE = QColor('#A7C2C1') #桃海洋
    SOFT_MARINE = QColor('#A4C1C1') #柔海洋
    WARM_MARINE = QColor('#A1C0C1') #暖海洋
    PEACH_LAGOON = QColor('#9EBFC0') #桃泻湖
    SOFT_LAGOON = QColor('#9ABEC0') #柔泻湖
    WARM_LAGOON = QColor('#97BDBF') #暖泻湖
    PEACH_BAY = QColor('#93BBBF') #桃海湾
    SOFT_BAY = QColor('#8FBABF') #柔海湾
    WARM_BAY = QColor('#8BB9BF') #暖海湾
    PEACH_HARBOR = QColor('#87B7BF') #桃港口
    SOFT_HARBOR = QColor('#83B6BF') #柔港口
    WARM_HARBOR = QColor('#80B4BF') #暖港口
    PEACH_NAVY = QColor('#7CB3BF') #桃海军蓝
    SOFT_NAVY = QColor('#78B1BF') #柔海军蓝
    WARM_NAVY = QColor('#75AFBF') #暖海军蓝
    PEACH_AZURE = QColor('#72AEC0') #桃天蓝
    SOFT_AZURE = QColor('#6FACC0') #柔天蓝
    WARM_AZURE = QColor('#6CAAC1') #暖天蓝
    PEACH_SKY_BLUE = QColor('#6AA8C1') #桃天空蓝
    SOFT_SKY_BLUE = QColor('#68A7C2') #柔天空蓝
    WARM_SKY_BLUE = QColor('#66A5C2') #暖天空蓝
    PEACH_CERULEAN = QColor('#65A3C3') #桃蔚蓝
    SOFT_CERULEAN = QColor('#64A2C4') #柔蔚蓝
    WARM_CERULEAN = QColor('#63A1C4') #暖蔚蓝
    PEACH_TEAL = QColor('#639FC5') #桃水鸭
    SOFT_TEAL = QColor('#639EC6') #柔水鸭
    WARM_TEAL = QColor('#639DC7') #暖水鸭
    PEACH_CYAN = QColor('#649DC8') #桃青色
    SOFT_CYAN = QColor('#669CC9') #柔青色
    WARM_CYAN = QColor('#689CCA') #暖青色
    PEACH_BLUE = QColor('#6A9CCB') #桃蓝色
    SOFT_BLUE = QColor('#6C9CCC') #柔蓝色
    WARM_BLUE = QColor('#709DCD') #暖蓝色
    PEACH_OCEAN_BLUE = QColor('#739ECE') #桃海洋蓝
    SOFT_OCEAN_BLUE = QColor('#779FD0') #柔海洋蓝
    WARM_OCEAN_BLUE = QColor('#7BA0D1') #暖海洋蓝
    PEACH_NAVY_BLUE = QColor('#7FA2D2') #桃海军蓝
    SOFT_NAVY_BLUE = QColor('#84A3D3') #柔海军蓝
    WARM_NAVY_BLUE = QColor('#88A6D5') #暖海军蓝
    PEACH_DEEP_BLUE = QColor('#8DA8D6') #桃深蓝
    SOFT_DEEP_BLUE = QColor('#92AAD7') #柔深蓝
    WARM_DEEP_BLUE = QColor('#98ADD8') #暖深蓝
    PEACH_ROYAL = QColor('#9DB0DA') #桃皇家
    SOFT_ROYAL = QColor('#A2B3DB') #柔皇家
    WARM_ROYAL = QColor('#A7B6DC') #暖皇家
    PEACH_MAJESTY = QColor('#ACBADD') #桃威严
    SOFT_MAJESTY = QColor('#B1BDDF') #柔威严
    WARM_MAJESTY = QColor('#B6C0E0') #暖威严
    PEACH_VIOLET = QColor('#BBC3E1') #桃紫罗兰
    SOFT_VIOLET = QColor('#BFC6E2') #柔紫罗兰
    WARM_VIOLET = QColor('#C3C9E3') #暖紫罗兰
    PEACH_LAVENDER = QColor('#C7CCE5') #桃薰衣草
    SOFT_LAVENDER = QColor('#CACEE6') #柔薰衣草
    WARM_LAVENDER = QColor('#CDD0E7') #暖薰衣草
    PEACH_PURPLE = QColor('#CFD2E8') #桃紫色
    SOFT_PURPLE = QColor('#D1D3E9') #柔紫色
    WARM_PURPLE = QColor('#D2D4EA') #暖紫色
    PEACH_LILAC = QColor('#D3D5EB') #桃丁香
    SOFT_LILAC = QColor('#D3D5EB') #柔丁香
    WARM_LILAC = QColor('#D3D4EC') #暖丁香
    PEACH_ORCHID = QColor('#D3D3ED') #桃兰花
    SOFT_ORCHID = QColor('#D1D1EE') #柔兰花
    WARM_ORCHID = QColor('#D0D0EE') #暖兰花
    PEACH_WISTERIA = QColor('#CFCEEF') #桃紫藤
    SOFT_WISTERIA = QColor('#CDCBF0') #柔紫藤
    WARM_WISTERIA = QColor('#CBC8F0') #暖紫藤
    PEACH_PERIWINKLE = QColor('#C8C5F0') #桃长春花
    SOFT_PERIWINKLE = QColor('#C6C1F1') #柔长春花
    WARM_PERIWINKLE = QColor('#C3BDF1') #暖长春花
    PEACH_IRIS = QColor('#C0B9F1') #桃鸢尾
    SOFT_IRIS = QColor('#BDB4F2') #柔鸢尾
    WARM_IRIS = QColor('#BAAFF2') #暖鸢尾
    PEACH_VIOLET_RED = QColor('#B8ABF2') #桃紫红
    SOFT_VIOLET_RED = QColor('#B5A6F2') #柔紫红
    WARM_VIOLET_RED = QColor('#B2A1F2') #暖紫红
    PEACH_PURPLE_PINK = QColor('#B09CF2') #桃紫粉
    SOFT_PURPLE_PINK = QColor('#AE97F1') #柔紫粉
    WARM_PURPLE_PINK = QColor('#AC93F1') #暖紫粉
    PEACH_LAVENDER_PINK = QColor('#AA8EF1') #桃薰衣草粉
    SOFT_LAVENDER_PINK = QColor('#A98AF0') #柔薰衣草粉
    WARM_LAVENDER_PINK = QColor('#A886F0') #暖薰衣草粉
    PEACH_ROSE = QColor('#A783EF') #桃玫瑰
    SOFT_ROSE = QColor('#A780EF') #柔玫瑰
    WARM_ROSE = QColor('#A67DEE') #暖玫瑰
    PEACH_BLUSH_PINK = QColor('#A67AEE') #桃腮红粉
    SOFT_BLUSH_PINK = QColor('#A778ED') #柔腮红粉
    WARM_BLUSH_PINK = QColor('#A877EC') #暖腮红粉
    PEACH_PINK = QColor('#A976EB') #桃粉色
    SOFT_PINK = QColor('#AA75EA') #柔粉色
    WARM_PINK = QColor('#AB75E9') #暖粉色
    PEACH_CORAL_PINK = QColor('#AD75E8') #桃珊瑚粉
    SOFT_CORAL_PINK = QColor('#AE75E7') #柔珊瑚粉
    WARM_CORAL_PINK = QColor('#B077E6') #暖珊瑚粉
    PEACH_SALMON = QColor('#B278E5') #桃鲑鱼
    SOFT_SALMON = QColor('#B47AE4') #柔鲑鱼
    WARM_SALMON = QColor('#B67CE3') #暖鲑鱼
    PEACH_MELON = QColor('#B87EE2') #桃甜瓜
    SOFT_MELON = QColor('#BA81E1') #柔甜瓜
    WARM_MELON = QColor('#BC84DF') #暖甜瓜
    PEACH_APRICOT = QColor('#BE87DE') #桃杏
    SOFT_APRICOT = QColor('#C08ADD') #柔杏
    WARM_APRICOT = QColor('#C28EDC') #暖杏
    PEACH_PEACH = QColor('#C391DA') #桃桃
    SOFT_PEACH = QColor('#C595D9') #柔桃
    WARM_PEACH = QColor('#C698D8') #暖桃
    PEACH_PINK_LIGHT = QColor('#C79BD7') #淡桃粉
    SOFT_PINK_LIGHT = QColor('#C89FD5') #柔淡粉
    WARM_PINK_LIGHT = QColor('#C8A2D4') #暖淡粉
    PEACH_BLUSH_LIGHT = QColor('#C9A5D3') #淡桃腮红
    SOFT_BLUSH_LIGHT = QColor('#C9A8D2') #柔淡腮红
    WARM_BLUSH_LIGHT = QColor('#C9AAD0') #暖淡腮红
    PEACH_PALE_PINK = QColor('#C9ACCF') #淡桃粉
    SOFT_PALE_PINK = QColor('#C9AECE') #柔淡粉
    WARM_PALE_PINK = QColor('#C9B0CD') #暖淡粉
    PEACH_POWDER_PINK = QColor('#C9B1CC') #桃粉粉
    SOFT_POWDER_PINK = QColor('#C8B2CB') #柔粉粉
    WARM_POWDER_PINK = QColor('#C8B3CA') #暖粉粉
    PEACH_MIST_PINK = QColor('#C7B3C9') #桃雾粉
    SOFT_MIST_PINK = QColor('#C7B3C8') #柔雾粉
    WARM_MIST_PINK = QColor('#C6B3C7') #暖雾粉
    PEACH_FROST_PINK = QColor('#C5B2C6') #桃霜粉
    SOFT_FROST_PINK = QColor('#C5B1C5') #柔霜粉
    WARM_FROST_PINK = QColor('#C4AFC4') #暖霜粉
    PEACH_DUSTY_PINK = QColor('#C3ADC3') #桃灰粉
    SOFT_DUSTY_PINK = QColor('#C3ABC1') #柔灰粉
    WARM_DUSTY_PINK = QColor('#C2A9C0') #暖灰粉
    PEACH_ROSE_DUST = QColor('#C1A6BF') #桃玫瑰尘
    SOFT_ROSE_DUST = QColor('#C1A3BE') #柔玫瑰尘
    WARM_ROSE_DUST = QColor('#C0A0BD') #暖玫瑰尘
    PEACH_MAUVE = QColor('#C09CBB') #桃淡紫
    SOFT_MAUVE = QColor('#C099BA') #柔淡紫
    WARM_MAUVE = QColor('#BF95B8') #暖淡紫
    PEACH_LILAC_PINK = QColor('#BF92B7') #桃丁香粉
    SOFT_LILAC_PINK = QColor('#BF8EB5') #柔丁香粉
    WARM_LILAC_PINK = QColor('#BF8AB3') #暖丁香粉
    PEACH_PINK_PURPLE = QColor('#BF86B2') #桃粉紫
    SOFT_PINK_PURPLE = QColor('#BF82B0') #柔粉紫
    WARM_PINK_PURPLE = QColor('#BF7EAE') #暖粉紫
    PEACH_BERRY = QColor('#BF7BAC') #桃浆果
    SOFT_BERRY = QColor('#BF77AA') #柔浆果
    WARM_BERRY = QColor('#BF74A8') #暖浆果
    PEACH_RASPBERRY = QColor('#C071A6') #桃覆盆子
    SOFT_RASPBERRY = QColor('#C06EA3') #柔覆盆子
    WARM_RASPBERRY = QColor('#C16BA1') #暖覆盆子
    PEACH_CRANBERRY = QColor('#C1699F') #桃蔓越莓
    SOFT_CRANBERRY = QColor('#C2679E') #柔蔓越莓
    WARM_CRANBERRY = QColor('#C2659C') #暖蔓越莓
    PEACH_WINE = QColor('#C3649A') #桃酒红
    SOFT_WINE = QColor('#C46398') #柔酒红
    WARM_WINE = QColor('#C56397') #暖酒红
    PEACH_RED = QColor('#C56396') #桃红
    SOFT_RED = QColor('#C66395') #柔红
    WARM_RED = QColor('#C76494') #暖红
    PEACH_SCARLET = QColor('#C86593') #桃猩红
    SOFT_SCARLET = QColor('#C96693') #柔猩红
    WARM_SCARLET = QColor('#CA6893') #暖猩红
    PEACH_CARMINE = QColor('#CB6B93') #桃胭脂
    SOFT_CARMINE = QColor('#CD6D93') #柔胭脂
    WARM_CARMINE = QColor('#CE7194') #暖胭脂
    PEACH_RUBY = QColor('#CF7495') #桃红宝石
    SOFT_RUBY = QColor('#D07897') #柔红宝石
    WARM_RUBY = QColor('#D17C98') #暖红宝石
    PEACH_GARNET = QColor('#D2819A') #桃石榴
    SOFT_GARNET = QColor('#D4859D') #柔石榴
    WARM_GARNET = QColor('#D58A9F') #暖石榴
    PEACH_BERRY_RED = QColor('#D68FA2') #桃浆果红
    SOFT_BERRY_RED = QColor('#D894A5') #柔浆果红
    WARM_BERRY_RED = QColor('#D999A8') #暖浆果红
    PEACH_PINK_RED = QColor('#DA9FAC') #桃粉红
    SOFT_PINK_RED = QColor('#DBA4AF') #柔粉红
    WARM_PINK_RED = QColor('#DDA9B3') #暖粉红
    PEACH_ROSE_RED = QColor('#DEAEB6') #桃玫瑰红
    SOFT_ROSE_RED = QColor('#DFB3BA') #柔玫瑰红
    WARM_ROSE_RED = QColor('#E0B8BD') #暖玫瑰红
    PEACH_BLUSH_RED = QColor('#E2BCC1') #桃腮红红
    SOFT_BLUSH_RED = QColor('#E3C0C4') #柔腮红红
    WARM_BLUSH_RED = QColor('#E4C4C7') #暖腮红红
    PEACH_PINK_BLUSH = QColor('#E5C8CA') #桃粉腮红
    SOFT_PINK_BLUSH = QColor('#E6CBCC') #柔粉腮红
    WARM_PINK_BLUSH = QColor('#E7CDCE') #暖粉腮红
    PEACH_PALE_BLUSH = QColor('#E8D0D0') #桃淡腮红

# 拼音搜索工具类
class PinyinSearchHelper:
    """拼音搜索辅助工具"""
    
    # 类级别的拼音映射字典
    chinese_to_pinyin_map = {
        '阿': 'a', '八': 'b', '擦': 'c', '大': 'd', '鹅': 'e', '发': 'f', '哥': 'g', '哈': 'h', '我': 'w',
        '一': 'y', '二': 'e', '三': 's', '四': 's', '五': 'w', '六': 'l', '七': 'q', '八': 'b', '九': 'j', '十': 's',
        '爱': 'a', '不': 'b', '从': 'c', '的': 'd', '饿': 'e', '分': 'f', '个': 'g', '好': 'h',
        '可': 'k', '了': 'l', '妈': 'm', '你': 'n', '哦': 'o', '跑': 'p',
        '去': 'q', '人': 'r', '是': 's', '他': 't',
        '小': 'x', '有': 'y', '在': 'z'
    }
    
    @staticmethod
    def get_pinyin_initials(text):
        """获取文本的拼音首字母"""
        if not text or not isinstance(text, str):
            return ""
            
        result = ""
        for char in text:
            if '\u4e00' <= char <= '\u9fff':  # 中文字符
                if pinyin_available:
                    try:
                        # 使用pypinyin库获取拼音首字母
                        pinyin_list = pinyin(char, style=Style.FIRST_LETTER)
                        if pinyin_list and pinyin_list[0]:
                            result += pinyin_list[0][0].lower()
                    except Exception:
                        # 如果pypinyin出错，回退到简单映射
                        initial = PinyinSearchHelper.chinese_to_pinyin_map.get(char)
                        if initial:
                            result += initial
                        else:
                            result += char.lower()
                else:
                    # 使用简单映射
                    initial = PinyinSearchHelper.chinese_to_pinyin_map.get(char)
                    if initial:
                        result += initial
                    else:
                        result += char.lower()
            else:
                # 非中文字符直接转换为小写
                result += char.lower()
                
        return result

    @staticmethod
    def text_to_pinyin_initials(text):
        """将文本转换为拼音首字母字符串 - 新增方法"""
        if not text or not isinstance(text, str):
            return ""
            
        result = ""
        for char in text:
            if '\u4e00' <= char <= '\u9fff':  # 中文字符
                return PinyinSearchHelper.get_pinyin_initials(text)


    @staticmethod
    def contains_pinyin_initials(text, search_initials):
        """检查文本是否包含拼音首字母

        【性能优化】原先每次调用都要用 pypinyin 逐字符重算整串拼音首字母：
        filter_directories 对每一行都要算 name 与 path 各一次（11634 行 = 23268 次
        逐字符 pypinyin 调用），且每次搜索都全部重算。
        改为按「原文本」缓存其首字母串（首字母串只取决于文本本身，与搜索词无关），
        因此跨搜索、跨会话阶段都可复用，结果是完全一致的（纯记忆化，非近似）。

        缓存带上限，避免长期累积；读写加锁，保证多线程（扫描 worker /
        HTTP 请求线程）下安全。
        """
        if not text:
            return False
        text_initials = PinyinSearchHelper.cached_initials(text)
        return search_initials in text_initials

    # ===== 拼音首字母记忆化缓存（类级别，线程安全，带上限） =====
    _initials_cache = {}          # {text: initials}
    _initials_cache_max = 20000   # 上限，防止长期运行无限增长
    _initials_cache_lock = Lock()

    @staticmethod
    def cached_initials(text):
        """返回文本的首字母串（带缓存）。"""
        if not text or not isinstance(text, str):
            return ""
        cache = PinyinSearchHelper._initials_cache
        hit = cache.get(text)
        if hit is not None:
            return hit

        initials = PinyinSearchHelper.get_pinyin_initials(text)

        with PinyinSearchHelper._initials_cache_lock:
            # 双重检查：并发下可能已被别的线程填好
            if text in cache:
                return cache[text]
            if len(cache) >= PinyinSearchHelper._initials_cache_max:
                # 命中率不是关键，简单清空即可（重算成本远低于无限增长的内存）
                cache.clear()
            cache[text] = initials
        return initials




class DirectoryScannerHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """目录扫描系统的HTTP请求处理器 - 线程安全版本"""

    def __init__(self, *args, main_app=None, open_directory_callback=None, **kwargs):
        self.main_app = main_app
        self.open_directory_callback = open_directory_callback
        # 新增：线程锁用于保护共享资源
        self.lock = threading.RLock()
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """处理GET请求 - 线程安全版本

        【性能优化】此前用 `with self.lock:` 包住整个请求分发，包括静态文件服务与
        视频流；而 self.lock 是每个请求处理器实例各自的锁（__init__ 里新建），
        它并不保护任何跨请求共享状态，却把每个连接自己的处理流程整体串行化。
        现将锁收窄到真正共享的状态（EPUB HTML 缓存 _epub_cache），
        静态文件、视频流、各 API 分发不再持锁。
        """
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path

            # print(f"[HTTP DEBUG] 请求路径: {path} (线程: {threading.current_thread().name})")

            # 静态文件服务
            if path.startswith('/static/'):
                self.handle_static_file(path)
            elif path == '/':
                self.send_html_response(self.get_index_html())
            elif path == '/api/directories':
                # 获取查询参数
                query_params = urllib.parse.parse_qs(parsed_path.query)
                filter_type = query_params.get('type', ['all'])[0].lower()
                sort_by = query_params.get('sort', ['name'])[0].lower()
                path_filter = query_params.get('path_filter', [''])[0]  # 新增：路径过滤
                
                self.send_json_response(self.get_directories_data(filter_type, sort_by, path_filter))
            elif path == '/api/directories/search':
                self.handle_search_request(parsed_path.query)
            elif path == '/api/directories/paths':
                # 新增：获取所有目录路径用于过滤选择
                self.handle_paths_request()
            elif path == '/api/cover':
                self.handle_cover_request(parsed_path.query)
            elif path == '/api/video':  
                self.handle_video_request(parsed_path.query)
            elif path == '/api/pdf':
                self.handle_pdf_request(parsed_path.query)
            elif path == '/api/document':
                self.handle_document_request(parsed_path.query)
            elif path == '/api/open':
                self.handle_open_request(parsed_path.query)
            elif path == '/api/scan':
                self.handle_scan_request()
            elif path == '/api/status':
                self.send_json_response(self.get_system_status())
            elif path == '/api/directory/files':
                self.handle_directory_files_request(parsed_path.query)
            elif path == '/api/admin/directories':
                self.handle_admin_directories_get()
            elif path.startswith('/api/directory/'):
                self.handle_get_directory(parsed_path.path)
            else:
                # 尝试提供静态文件
                super().do_GET()
                
        except Exception as e:
            print(f"[HTTP ERROR] 处理GET请求时出错: {e}")
            import traceback
            traceback.print_exc()
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))

    def handle_paths_request(self):
        """获取所有目录路径的树形结构"""
        if not self.main_app or not self.main_app.user_manager.current_db_path:
            self.send_json_response({"paths": [], "tree": []})
            return
        
        try:
            conn = sqlite3.connect(self.main_app.user_manager.current_db_path)
            cursor = conn.cursor()
            
            # 获取所有唯一的目录路径
            cursor.execute("""
                SELECT DISTINCT path FROM directories 
                WHERE is_directory = 1 
                ORDER BY path
            """)
            
            all_paths = [row[0] for row in cursor.fetchall()]
            
            # 构建目录树
            path_tree = self.build_path_tree(all_paths)
            
            conn.close()
            
            self.send_json_response({
                "paths": all_paths,
                "tree": path_tree
            })
            
        except Exception as e:
            print(f"[PATHS API ERROR] {e}")
            self.send_json_response({"paths": [], "tree": [], "error": str(e)})

    def build_path_tree(self, paths):
        """构建路径树形结构

        【性能优化】此前对每个路径的每一段都在 current_level 列表里线性扫描找同名
        节点，整体复杂度 O(N × 深度 × 兄弟数)，目录多时是纯 CPU 瓶颈。
        改为给每个节点挂一个「子节点 name -> node」索引字典（键为 None 时代表根层）：
          - 新节点仍 append 到列表，因此列表顺序（即输出顺序）与原实现完全一致；
          - 命中索引时直接复用同一个 dict 对象，不再线性查找。
        索引挂在节点自身上（而不是按深度共享），因为同一层在不同路径下属于不同的
        父节点，按深度共享会把兄弟节点的子节点串到一起。
        输出结构（name / full_path / children 及顺序）与原实现逐节点等价。
        """
        tree = []
        # 根层的索引：id(None) 作为键，与节点索引放在同一个 dict 里统一查找
        indexes = {}

        for path in paths:
            parts = path.replace('\\', '/').split('/')
            current_level = tree
            current_index = indexes.get(id(None))
            if current_index is None:
                current_index = indexes[id(None)] = {}

            for i, part in enumerate(parts):
                if not part:
                    continue

                node = current_index.get(part)
                if node is None:
                    # 构建完整路径（与旧实现一致：用原始 parts 下标 i+1，
                    # 因此前导空段会体现为前导 '/'，必须原样保留）
                    full_path = '/'.join(parts[:i + 1])
                    node = {
                        'name': part,
                        'full_path': full_path,
                        'children': []
                    }
                    current_level.append(node)
                    current_index[part] = node

                current_level = node['children']
                current_index = indexes.get(id(node))
                if current_index is None:
                    current_index = indexes[id(node)] = {}

        return tree

    def handle_directory_files_request(self, query_string):
        """处理获取目录文件列表请求"""
        query_params = urllib.parse.parse_qs(query_string)
        directory_path = query_params.get('path', [''])[0]
        display_mode = query_params.get('mode', ['all'])[0]
        
        if not directory_path:
            self.send_json_response({"files": [], "totalCount": 0, "error": "Missing path parameter"})
            return
        
        try:
            dir_path = urllib.parse.unquote(directory_path)
            
            # 路径规范化
            if self.main_app and hasattr(self.main_app, 'normalize_path_separators'):
                dir_path = self.main_app.normalize_path_separators(dir_path)
            
            if not os.path.isdir(dir_path):
                self.send_json_response({"files": [], "totalCount": 0, "error": "Directory not found"})
                return
            
            # 文件类型定义
            image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.ico']
            video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg']
            document_extensions = ['.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
                                '.epub', '.mobi', '.azw', '.rtf', '.odt', '.ods', '.odp']
            
            # 获取所有文件
            all_files = []
            try:
                for item in os.listdir(dir_path):
                    item_path = os.path.join(dir_path, item)
                    if os.path.isfile(item_path):
                        all_files.append(item)
            except PermissionError:
                self.send_json_response({"files": [], "totalCount": 0, "error": "Permission denied"})
                return
            
            # 根据显示模式筛选
            display_files = []
            
            if display_mode == 'images':
                display_files = [f for f in all_files if any(f.lower().endswith(ext) for ext in image_extensions)]
            elif display_mode == 'videos':
                display_files = [f for f in all_files if any(f.lower().endswith(ext) for ext in video_extensions)]
            elif display_mode == 'documents':
                display_files = [f for f in all_files if any(f.lower().endswith(ext) for ext in document_extensions)]
            elif display_mode == 'none':
                display_files = []
            else:  # 'all' - 显示所有非图片文件（因为图片已在缩略图列显示）
                display_files = [f for f in all_files if not any(f.lower().endswith(ext) for ext in image_extensions)]
            
            # 限制显示数量
            max_display = 10
            if len(display_files) > max_display:
                display_files = display_files[:max_display]
            
            # 图标映射
            icon_map = {
                '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬', '.mov': '🎬', '.wmv': '🎬', '.flv': '🎬', '.webm': '🎬', '.m4v': '🎬', '.mpg': '🎬', '.mpeg': '🎬',
                '.pdf': '📄', '.doc': '📝', '.docx': '📝', '.txt': '📃',
                '.xls': '📊', '.xlsx': '📊', '.ppt': '📽️', '.pptx': '📽️',
                '.zip': '📦', '.rar': '📦', '.7z': '📦',
                '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵',
                '.exe': '⚙️', '.msi': '⚙️',
                '.epub': '📚', '.mobi': '📚', '.azw': '📚',
                '.html': '🌐', '.htm': '🌐', '.css': '🎨', '.js': '📜',
                '.json': '🔧', '.xml': '🔧'
            }
            
            files_data = []
            for file_name in display_files:
                ext = os.path.splitext(file_name)[1].lower()
                icon = icon_map.get(ext, '📄')
                files_data.append({
                    "name": file_name,
                    "path": os.path.join(dir_path, file_name),
                    "icon": icon,
                    "ext": ext
                })
            
            self.send_json_response({
                "files": files_data,
                "totalCount": len(all_files),
                "displayMode": display_mode
            })
            
        except Exception as e:
            print(f"[FILES API ERROR] {e}")
            import traceback
            traceback.print_exc()
            self.send_json_response({"files": [], "totalCount": 0, "error": str(e)})

    def handle_static_file(self, path):
        """处理静态文件请求"""
        try:
            # 安全的路径处理
            safe_path = path.lstrip('/')
            if '..' in safe_path or safe_path.startswith('static/') is False:
                self.send_error(HTTPStatus.FORBIDDEN, "Invalid path")
                return
            
            # 构建本地文件路径
            static_dir = os.path.join(self.main_app.app_dir, "static")
            file_path = os.path.join(static_dir, safe_path.replace('static/', '', 1))
            
            # 检查文件是否存在
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                self.send_error(HTTPStatus.NOT_FOUND, "File not found")
                return
            
            # 根据文件扩展名设置MIME类型
            ext = os.path.splitext(file_path)[1].lower()
            mime_types = {
                '.js': 'application/javascript',
                '.css': 'text/css',
                '.html': 'text/html',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.ico': 'image/x-icon'
            }
            content_type = mime_types.get(ext, 'application/octet-stream')
            
            # 发送文件
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', content_type)
            self.send_header('Content-Length', str(len(file_data)))
            self.send_header('Cache-Control', 'public, max-age=3600')  # 缓存1小时
            self.end_headers()
            self.wfile.write(file_data)
            
        except Exception as e:
            print(f"[STATIC ERROR] 处理静态文件失败: {e}")
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))

    def handle_video_request(self, query_string):
        """处理视频流请求 - 增强版本，添加连接异常处理"""
        query_params = urllib.parse.parse_qs(query_string)
        path = query_params.get('path', [''])[0]
        
        if not path:
            self.send_error(HTTPStatus.BAD_REQUEST, "Missing path parameter")
            return
        
        try:
            video_path = urllib.parse.unquote(path)
            
            # 路径规范化
            if self.main_app and hasattr(self.main_app, 'normalize_path_separators'):
                video_path = self.main_app.normalize_path_separators(video_path)
            
            # 检查文件是否存在且是视频文件
            if not os.path.exists(video_path):
                self.send_error(HTTPStatus.NOT_FOUND, "Video file not found")
                return
            
            # 检查文件类型
            video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v']
            file_ext = os.path.splitext(video_path)[1].lower()
            if file_ext not in video_extensions:
                self.send_error(HTTPStatus.BAD_REQUEST, "Not a video file")
                return
            
            # 获取文件大小
            file_size = os.path.getsize(video_path)
            
            # 处理范围请求（支持视频seek）
            range_header = self.headers.get('Range', '')
            byte_range = None
            
            if range_header:
                # 解析范围请求，格式：bytes=start-end
                range_match = re.match(r'bytes=(\d+)-(\d+)?', range_header)
                if range_match:
                    start = int(range_match.group(1))
                    end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
                    byte_range = (start, end)
            
            # 发送视频文件
            self.send_video_file(video_path, file_size, byte_range)
            
        except ConnectionResetError:
            # 客户端主动断开连接，这是正常现象，不记录为错误
            print(f"[INFO] 客户端断开视频连接: {path}")
            return
        except Exception as e:
            print(f"[SERVER ERROR] 处理视频请求失败: {e}")
            # 使用安全的错误发送方法
            self.send_safe_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))

    def send_video_file(self, video_path, file_size, byte_range=None):
        """发送视频文件，支持范围请求 - 增强版本"""
        try:
            # 确定MIME类型
            ext = os.path.splitext(video_path)[1].lower()
            mime_types = {
                '.mp4': 'video/mp4',
                '.avi': 'video/x-msvideo',
                '.mkv': 'video/x-matroska',
                '.mov': 'video/quicktime',
                '.wmv': 'video/x-ms-wmv',
                '.flv': 'video/x-flv',
                '.webm': 'video/webm',
                '.m4v': 'video/x-m4v'
            }
            content_type = mime_types.get(ext, 'video/mp4')
            
            if byte_range:
                # 处理部分内容请求
                start, end = byte_range
                content_length = end - start + 1
                
                self.send_response(HTTPStatus.PARTIAL_CONTENT)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(content_length))
                self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                self.send_header('Accept-Ranges', 'bytes')
                self.end_headers()
                
                # 发送指定范围的数据
                with open(video_path, 'rb') as f:
                    f.seek(start)
                    remaining = content_length
                    while remaining > 0:
                        chunk_size = min(8192, remaining)
                        try:
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                            remaining -= len(chunk)
                        except ConnectionResetError:
                            # 客户端断开连接，正常退出
                            print(f"[INFO] 视频流传输中断: {video_path}")
                            return
            else:
                # 发送完整文件
                self.send_response(HTTPStatus.OK)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(file_size))
                self.send_header('Accept-Ranges', 'bytes')
                self.end_headers()
                
                # 发送整个文件
                with open(video_path, 'rb') as f:
                    while chunk := f.read(8192):
                        try:
                            self.wfile.write(chunk)
                        except ConnectionResetError:
                            # 客户端断开连接，正常退出
                            print(f"[INFO] 视频流传输中断: {video_path}")
                            return
                            
        except ConnectionResetError:
            # 客户端主动断开连接，这是正常现象
            print(f"[INFO] 客户端断开视频连接: {video_path}")
            return
        except Exception as e:
            print(f"[SERVER ERROR] 发送视频文件失败: {e}")
            self.send_safe_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))

    def send_safe_error(self, code, message):
        """安全发送错误响应，避免编码问题"""
        try:
            # 确保消息是ASCII安全的
            safe_message = message.encode('ascii', 'ignore').decode('ascii')
            if not safe_message:
                safe_message = "Internal Server Error"
            
            self.send_error(code, safe_message)
        except Exception as e:
            # 如果发送错误也失败，记录日志并返回基本错误
            print(f"[CRITICAL] 发送错误响应失败: {e}")
            try:
                self.send_error(code, "Error")
            except:
                pass  # 最终放弃

    def handle_get_directory(self, path):
        """处理获取单个目录信息的请求"""
        try:
            # 从路径中提取目录ID
            dir_id = path.split('/')[-1]
            if not dir_id.isdigit():
                self.send_error(HTTPStatus.BAD_REQUEST, "Invalid directory ID")
                return
            
            if not self.main_app or not self.main_app.user_manager.current_db_path:
                self.send_json_response({"success": False, "error": "Database not available"})
                return
            
            conn = sqlite3.connect(self.main_app.user_manager.current_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, path, directory_exists, created_time, last_modified, is_directory 
                FROM directories 
                WHERE id = ?
            """, (dir_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                db_id, name, path, exists, created_time, last_modified, is_directory = result
                directory_info = {
                    "id": db_id,
                    "name": name,
                    "path": path,
                    "exists": bool(exists),
                    "created_time": created_time,
                    "last_modified": last_modified,
                    "is_directory": bool(is_directory)
                }
                self.send_json_response({"success": True, "directory": directory_info})
            else:
                self.send_json_response({"success": False, "error": "Directory not found"})
                
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)})

    def handle_document_request(self, query_string):
        """处理文档文件请求"""
        query_params = urllib.parse.parse_qs(query_string)
        path = query_params.get('path', [''])[0]
        preview = query_params.get('preview', [''])[0]
        
        if not path:
            self.send_error(HTTPStatus.BAD_REQUEST, "Missing path parameter")
            return
        
        try:
            doc_path = urllib.parse.unquote(path)
            
            # 路径规范化
            if self.main_app and hasattr(self.main_app, 'normalize_path_separators'):
                doc_path = self.main_app.normalize_path_separators(doc_path)
            
            # 检查文件是否存在且是文档文件
            if not os.path.exists(doc_path):
                self.send_error(HTTPStatus.NOT_FOUND, "Document file not found")
                return
            
            # 检查文件类型
            file_ext = os.path.splitext(doc_path)[1].lower()
            
            # 特殊处理EPUB文件
            if file_ext == '.epub':
                if preview == 'true':
                    # 提供在线阅读器
                    self.handle_epub_preview(doc_path)
                else:
                    # 直接提供EPUB文件下载
                    self.send_document_file(doc_path)
                return
            
            document_extensions = [
                '.pdf', '.txt', '.doc', '.docx', '.ppt', '.pptx', '.xls', 
                '.xlsx', '.rtf', '.odt', '.ods', '.odp', '.pages', '.numbers',
                '.key', '.mobi', '.azw', '.azw3', '.fb2', '.lit',
                '.prc', '.pdb', '.chm', '.djvu', '.djv'
            ]
            
            if file_ext not in document_extensions:
                self.send_error(HTTPStatus.BAD_REQUEST, "Not a document file")
                return
            
            # 发送其他文档文件
            self.send_document_file(doc_path)
            
        except Exception as e:
            print(f"[SERVER ERROR] 处理文档请求失败: {e}")
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))

    def handle_epub_preview(self, epub_path):
        """处理EPUB文件预览 - 添加缓存优化"""
        try:
            # 检查缓存
            cache_key = hashlib.md5(epub_path.encode()).hexdigest()
            cached_html = self.get_cached_epub_html(cache_key)
            
            if cached_html:
                print(f"[EPUB CACHE] 使用缓存的EPUB阅读器页面: {epub_path}")
                self.send_response(HTTPStatus.OK)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(cached_html.encode('utf-8'))))
                self.end_headers()
                self.wfile.write(cached_html.encode('utf-8'))
                return
            
            # 创建新的阅读器页面
            html_content = self.create_epub_reader_html(epub_path)
            
            # 缓存结果
            self.cache_epub_html(cache_key, html_content)
            
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(html_content.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
            
        except Exception as e:
            print(f"[SERVER ERROR] 处理EPUB预览失败: {e}")
            self.handle_epub_fallback(epub_path)

    def get_cached_epub_html(self, cache_key):
        """获取缓存的EPUB HTML"""
        # 简单的内存缓存，可以扩展为文件缓存
        if hasattr(self, '_epub_cache'):
            return self._epub_cache.get(cache_key)
        return None

    def cache_epub_html(self, cache_key, html_content):
        """缓存EPUB HTML"""
        if not hasattr(self, '_epub_cache'):
            self._epub_cache = {}
        self._epub_cache[cache_key] = html_content

    def create_epub_reader_html(self, epub_path):
        """创建智能EPUB阅读器 - 先本地后网络"""
        filename = os.path.basename(epub_path)
        encoded_path = urllib.parse.quote(epub_path)
        
        return f'''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>EPUB阅读器 - {filename}</title>
        
        <!-- 智能加载脚本 - 先本地后网络 -->
        <script>
            // 智能库加载器 - 优先使用本地文件
            class SmartLibraryLoader {{
                constructor() {{
                    this.libraries = {{
                        epubjs: {{
                            local: '/static/epub.js',
                            cdn: 'https://cdn.jsdelivr.net/npm/epubjs/dist/epub.min.js',
                            global: 'ePub',
                            description: 'EPUB.js'
                        }},
                        jszip: {{
                            local: '/static/jszip.min.js',
                            cdn: 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js',
                            global: 'JSZip',
                            description: 'JSZip'
                        }}
                    }};
                    this.loadedLibraries = new Set();
                }}
                
                // 加载单个库 - 优先本地，失败后使用CDN
                async loadLibrary(libName) {{
                    if (this.loadedLibraries.has(libName)) {{
                        return true;
                    }}
                    
                    const lib = this.libraries[libName];
                    if (!lib) {{
                        throw new Error(`未知库: ${{libName}}`);
                    }}
                    
                    console.log(`正在加载 ${{lib.description}}...`);
                    
                    // 策略1: 首先尝试本地文件
                    let success = await this.tryLoad(lib.local, lib.global, lib.description);
                    
                    // 策略2: 如果本地失败，尝试CDN
                    if (!success) {{
                        console.warn(`${{lib.description}} 本地加载失败，尝试CDN...`);
                        success = await this.tryLoad(lib.cdn, lib.global, lib.description);
                    }}
                    
                    if (success) {{
                        this.loadedLibraries.add(libName);
                        console.log(`✓ ${{lib.description}} 加载成功`);
                    }} else {{
                        console.error(`❌ ${{lib.description}} 加载失败`);
                    }}
                    
                    return success;
                }}
                
                // 尝试加载脚本
                async tryLoad(src, globalVar, description) {{
                    return new Promise((resolve) => {{
                        // 检查是否已经全局存在
                        if (window[globalVar]) {{
                            console.log(`${{description}} 已存在`);
                            resolve(true);
                            return;
                        }}
                        
                        const script = document.createElement('script');
                        script.src = src;
                        script.onload = () => {{
                            // 验证是否真正加载成功
                            setTimeout(() => {{
                                if (window[globalVar]) {{
                                    resolve(true);
                                }} else {{
                                    console.warn(`${{description}} 脚本加载但全局变量未定义`);
                                    resolve(false);
                                }}
                            }}, 100);
                        }};
                        script.onerror = () => {{
                            console.warn(`${{description}} 加载失败: ${{src}}`);
                            resolve(false);
                        }};
                        
                        document.head.appendChild(script);
                    }});
                }}
                
                // 加载所有必要库
                async loadAll() {{
                    const results = await Promise.all([
                        this.loadLibrary('epubjs'),
                        this.loadLibrary('jszip')
                    ]);
                    
                    return results.every(success => success);
                }}
            }}
            
            // 全局加载器实例
            window.libraryLoader = new SmartLibraryLoader();
        </script>
        
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                background: #2c3e50;
                color: #ecf0f1;
                overflow: hidden;
                height: 100vh;
            }}
            
            .reader-container {{
                display: flex;
                flex-direction: column;
                height: 100vh;
            }}
            
            /* 顶部工具栏 */
            .reader-header {{
                background: #34495e;
                padding: 12px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 2px solid #1abc9c;
            }}
            
            .reader-title {{
                font-size: 16px;
                font-weight: bold;
                color: #1abc9c;
            }}
            
            .reader-controls {{
                display: flex;
                gap: 10px;
                align-items: center;
            }}
            
            .control-btn {{
                background: rgba(255,255,255,0.1);
                border: 1px solid rgba(255,255,255,0.3);
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
            }}
            
            .nav-btn {{
                background: #1abc9c;
                border: none;
                color: white;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                cursor: pointer;
                font-size: 18px;
            }}
            
            /* 阅读器主体 */
            .reader-main {{
                flex: 1;
                display: flex;
                position: relative;
            }}
            
            #viewer {{
                flex: 1;
                background: white;
                margin: 0;
            }}
            
            /* 加载状态 */
            .loading-container {{
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(44, 62, 80, 0.95);
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                z-index: 1000;
            }}
            
            .loading-spinner {{
                width: 50px;
                height: 50px;
                border: 5px solid rgba(255,255,255,0.3);
                border-top: 5px solid #1abc9c;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-bottom: 20px;
            }}
            
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            
            .loading-text {{
                color: white;
                font-size: 16px;
                text-align: center;
            }}
            
            /* 错误状态 */
            .error-container {{
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(231, 76, 60, 0.95);
                display: none;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                z-index: 1000;
                padding: 20px;
                text-align: center;
            }}
            
            .network-status {{
                position: fixed;
                top: 10px;
                right: 10px;
                background: rgba(0,0,0,0.7);
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
                font-size: 12px;
                z-index: 1001;
            }}

            /* 加载策略指示器 */
            .load-strategy {{
                position: fixed;
                top: 10px;
                left: 10px;
                background: rgba(0,0,0,0.7);
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
                font-size: 12px;
                z-index: 1001;
            }}
        </style>
    </head>
    <body>
        <div class="network-status" id="network-status">检测中...</div>
        <div class="load-strategy" id="load-strategy">加载策略: 先本地后网络</div>
        
        <div class="reader-container">
            <div class="reader-header">
                <div class="reader-title" id="book-title">📖 {filename}</div>
                <div class="reader-controls">
                    <button class="nav-btn" id="prev-btn">‹</button>
                    <div id="progress-info">就绪</div>
                    <button class="nav-btn" id="next-btn">›</button>
                    <button class="control-btn" onclick="downloadEpub()">下载</button>
                    <button class="control-btn" onclick="window.close()">关闭</button>
                </div>
            </div>
            
            <div class="reader-main">
                <div id="viewer"></div>
                
                <div class="loading-container" id="loading-container">
                    <div class="loading-spinner"></div>
                    <div class="loading-text" id="loading-text">正在初始化阅读器...</div>
                    <div class="loading-text" id="load-details" style="font-size: 12px; margin-top: 10px;"></div>
                </div>
                
                <div class="error-container" id="error-container">
                    <div style="font-size: 48px; margin-bottom: 20px;">❌</div>
                    <h3>加载失败</h3>
                    <p id="error-message">未知错误</p>
                    <div style="margin-top: 20px;">
                        <button class="control-btn" onclick="retryLoading()">重试</button>
                        <button class="control-btn" onclick="downloadEpub()">下载文件</button>
                        <button class="control-btn" onclick="window.close()">关闭</button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let book = null;
            let rendition = null;
            let loadStrategy = '先本地后网络';
            
            // 更新网络状态
            function updateNetworkStatus() {{
                const statusElem = document.getElementById('network-status');
                if (navigator.onLine) {{
                    statusElem.innerHTML = '🌐 在线';
                    statusElem.style.background = 'rgba(46, 204, 113, 0.8)';
                }} else {{
                    statusElem.innerHTML = '📴 离线';
                    statusElem.style.background = 'rgba(231, 76, 60, 0.8)';
                }}
            }}
            
            // 显示/隐藏加载状态
            function showLoading(message, details = '') {{
                document.getElementById('loading-text').textContent = message;
                document.getElementById('load-details').textContent = details;
                document.getElementById('loading-container').style.display = 'flex';
                document.getElementById('error-container').style.display = 'none';
            }}
            
            function hideLoading() {{
                document.getElementById('loading-container').style.display = 'none';
            }}
            
            function showError(message) {{
                document.getElementById('error-message').textContent = message;
                document.getElementById('error-container').style.display = 'flex';
                document.getElementById('loading-container').style.display = 'none';
            }}
            
            // 初始化EPUB阅读器
            async function initializeReader() {{
                try {{
                    showLoading('正在加载必要的库...', '策略: ' + loadStrategy);
                    updateNetworkStatus();
                    
                    // 使用智能加载器加载库 - 先本地后网络
                    const loadSuccess = await window.libraryLoader.loadAll();
                    
                    if (!loadSuccess) {{
                        throw new Error('无法加载必要的JavaScript库。请检查网络连接或联系管理员。');
                    }}
                    
                    showLoading('正在加载电子书...', '从服务器获取EPUB文件');
                    
                    // 创建EPUB实例
                    book = ePub('/api/document?path={encoded_path}');
                    
                    // 等待书籍准备就绪
                    await book.ready;
                    
                    // 渲染到视图
                    rendition = book.renderTo('viewer', {{
                        width: '100%',
                        height: '100%',
                        spread: 'auto'
                    }});
                    
                    // 显示内容
                    await rendition.display();
                    
                    // 设置事件
                    rendition.on('relocated', updateProgress);
                    document.getElementById('prev-btn').onclick = () => rendition.prev();
                    document.getElementById('next-btn').onclick = () => rendition.next();
                    
                    // 键盘控制
                    document.onkeydown = (e) => {{
                        if (e.key === 'ArrowLeft') rendition.prev();
                        if (e.key === 'ArrowRight') rendition.next();
                        if (e.key === 'Escape') window.close();
                    }};
                    
                    // 更新标题
                    if (book.package.metadata.title) {{
                        document.getElementById('book-title').textContent = 
                            `📖 ${{book.package.metadata.title}}`;
                    }}
                    
                    hideLoading();
                    console.log('EPUB阅读器初始化成功');
                    
                }} catch (error) {{
                    console.error('初始化失败:', error);
                    showError('初始化失败: ' + error.message);
                }}
            }}
            
            // 更新阅读进度
            function updateProgress(location) {{
                if (book && location) {{
                    try {{
                        const current = location.start.displayed.page;
                        const total = book.spine.length;
                        const percent = Math.round((current / total) * 100);
                        document.getElementById('progress-info').textContent = 
                            `${{current}}/${{total}} (${{percent}}%)`;
                    }} catch (e) {{
                        document.getElementById('progress-info').textContent = '阅读中...';
                    }}
                }}
            }}
            
            // 下载功能
            function downloadEpub() {{
                const link = document.createElement('a');
                link.href = '/api/document?path={encoded_path}';
                link.download = '{filename}';
                link.click();
            }}
            
            // 重试加载
            function retryLoading() {{
                document.getElementById('error-container').style.display = 'none';
                initializeReader();
            }}
            
            // 网络状态监听
            window.addEventListener('online', updateNetworkStatus);
            window.addEventListener('offline', updateNetworkStatus);
            
            // 页面加载完成后初始化
            window.addEventListener('load', () => {{
                setTimeout(initializeReader, 100);
            }});
        </script>
    </body>
    </html>
    '''
    
    def handle_epub_fallback(self, epub_path):
        """EPUB阅读器失败时的回退方案"""
        try:
            # 读取EPUB文件内容用于显示基本信息
            file_size = os.path.getsize(epub_path)
            filename = os.path.basename(epub_path)
            
            html_content = f'''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>EPUB阅读器 - {filename}</title>
        <style>
            body {{
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            .fallback-container {{
                background: white;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                text-align: center;
                max-width: 500px;
            }}
            .epub-icon {{
                font-size: 80px;
                margin-bottom: 20px;
            }}
            .download-btn {{
                background: #4CAF50;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 25px;
                font-size: 16px;
                cursor: pointer;
                margin: 20px 0;
                transition: all 0.3s;
            }}
            .download-btn:hover {{
                background: #45a049;
                transform: translateY(-2px);
            }}
        </style>
    </head>
    <body>
        <div class="fallback-container">
            <div class="epub-icon">📚</div>
            <h2>{filename}</h2>
            <p>文件大小: {self.format_file_size(file_size)}</p>
            <p>在线阅读器暂时不可用，请下载后使用专业阅读器打开</p>
            <button class="download-btn" onclick="downloadEpub()">📥 下载EPUB文件</button>
            <p><small>推荐使用 Calibre、Adobe Digital Editions 或手机端的静读天下等阅读器</small></p>
        </div>

        <script>
            function downloadEpub() {{
                const link = document.createElement('a');
                link.href = '/api/document?path={urllib.parse.quote(epub_path)}';
                link.download = '{filename}';
                link.click();
            }}
        </script>
    </body>
    </html>
    '''
            
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(html_content.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
            
        except Exception as e:
            print(f"[SERVER ERROR] 回退方案也失败了: {e}")
            # 最后的手段 - 直接下载
            self.send_document_file(epub_path)

    def format_file_size(self, size):
        """格式化文件大小"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"

    def send_document_file(self, doc_path):
        """发送文档文件"""
        try:
            file_size = os.path.getsize(doc_path)
            filename = os.path.basename(doc_path)
            
            # 确定MIME类型
            ext = os.path.splitext(doc_path)[1].lower()
            mime_types = {
                '.pdf': 'application/pdf',
                '.txt': 'text/plain',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.ppt': 'application/vnd.ms-powerpoint',
                '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                '.xls': 'application/vnd.ms-excel',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.rtf': 'application/rtf',
                '.odt': 'application/vnd.oasis.opendocument.text',
                '.ods': 'application/vnd.oasis.opendocument.spreadsheet',
                '.odp': 'application/vnd.oasis.opendocument.presentation',
                '.pages': 'application/vnd.apple.pages',
                '.numbers': 'application/vnd.apple.numbers',
                '.key': 'application/vnd.apple.keynote',
                '.epub': 'application/epub+zip',
                '.mobi': 'application/x-mobipocket-ebook',
                '.azw': 'application/vnd.amazon.ebook',
                '.azw3': 'application/vnd.amazon.ebook',
                '.fb2': 'application/x-fictionbook',
                '.lit': 'application/x-ms-reader',
                '.prc': 'application/x-mobipocket-ebook',
                '.pdb': 'application/vnd.palm',
                '.chm': 'application/vnd.ms-htmlhelp',
                '.djvu': 'image/vnd.djvu',
                '.djv': 'image/vnd.djvu'
            }
            content_type = mime_types.get(ext, 'application/octet-stream')
            
            # 安全编码文件名
            try:
                safe_filename = filename.encode('utf-8').decode('latin-1')
            except (UnicodeEncodeError, UnicodeDecodeError):
                safe_filename = "document" + ext
            
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(file_size))
            self.send_header('Content-Disposition', f'inline; filename="{safe_filename}"')
            self.end_headers()
            
            # 发送文件内容
            with open(doc_path, 'rb') as f:
                while chunk := f.read(8192):
                    try:
                        self.wfile.write(chunk)
                    except ConnectionResetError:
                        print(f"[INFO] 文档传输中断: {doc_path}")
                        return
                        
        except Exception as e:
            print(f"[SERVER ERROR] 发送文档文件失败: {e}")
            self.send_safe_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))


    def do_POST(self):
        """处理POST请求 - 线程安全版本

        【性能优化】同 do_GET：此前用 `with self.lock:` 包住整个请求处理，
        而该锁是每个请求处理器实例各自的锁，不保护任何跨请求共享状态，
        只会把请求处理整体串行化。现移除整请求加锁。
        """
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            
            if path == '/api/scan':
                self.handle_scan_request()
            elif path == '/api/open':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(post_data)
                self.handle_open_post(data)
            elif path == '/api/admin/directories':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(post_data)
                self.handle_admin_directories_post(data)
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "API endpoint not found")
                
        except Exception as e:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))

    def get_index_html(self):
        """返回主页面HTML - 增强版，支持PDF、视频、文档播放和文件列表显示"""
        return '''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>''' + ProjectInfo.NAME + ''' - Web客户端</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: 'Microsoft YaHei', Arial, sans-serif;
                    background: linear-gradient(135deg, #F4A8B0 0%, #DFAC85 100%);
                    min-height: 100vh;
                    padding: 20px;
                }
                
                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }
                
                .header {
                    background: linear-gradient(135deg, #9DB0DA, #ACBADD);
                    color: white;
                    padding: 20px;
                    text-align: center;
                }
                
                .header h1 {
                    font-size: 2.2em;
                    margin-bottom: 5px;
                }
                
                .header .subtitle {
                    font-size: 1.1em;
                    opacity: 0.9;
                }
                
                .controls {
                    padding: 20px;
                    background: white;
                    border-bottom: 1px solid #eee;
                    display: flex;
                    flex-wrap: wrap;
                    gap: 15px;
                    align-items: center;
                }
                
                .search-box {
                    flex: 1;
                    min-width: 300px;
                    position: relative;
                }
                
                .search-box input {
                    width: 100%;
                    padding: 12px 20px;
                    border: 2px solid #C7CCE5;
                    border-radius: 25px;
                    font-size: 16px;
                    outline: none;
                    transition: all 0.3s;
                }
                
                .search-box input:focus {
                    border-color: #9DB0DA;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }
                
                .buttons {
                    display: flex;
                    gap: 10px;
                    flex-wrap: wrap;
                }
                
                .btn {
                    padding: 12px 20px;
                    border: none;
                    border-radius: 25px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: bold;
                    transition: all 0.3s;
                    text-decoration: none;
                    display: inline-block;
                    text-align: center;
                }
                
                .btn-primary {
                    background: #9DB0DA;
                    color: white;
                }
                
                .btn-success {
                    background: #B1C16B;
                    color: white;
                }
                
                .btn-warning {
                    background: #E79A76;
                    color: white;
                }
                
                .btn-info {
                    background: #6DA9E4;
                    color: white;
                }
                
                .btn-danger {
                    background: #E74C3C;
                    color: white;
                }
                
                .btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
                }
                
                .status-bar {
                    padding: 10px 20px;
                    background: #CCC4B1;
                    border-bottom: 1px solid #ddd;
                    font-size: 14px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    flex-wrap: wrap;
                }
                
                .view-controls {
                    padding: 10px 20px;
                    background: #f8f9fa;
                    border-bottom: 1px solid #eee;
                    display: flex;
                    gap: 10px;
                    align-items: center;
                    flex-wrap: wrap;
                }
                
                .view-btn {
                    padding: 8px 16px;
                    border: 1px solid #ddd;
                    background: white;
                    border-radius: 5px;
                    cursor: pointer;
                    transition: all 0.3s;
                }
                
                .view-btn.active {
                    background: #9DB0DA;
                    color: white;
                    border-color: #9DB0DA;
                }
                
                .filter-controls {
                    display: flex;
                    gap: 10px;
                    align-items: center;
                    flex-wrap: wrap;
                }
                
                .filter-select {
                    padding: 8px 12px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    background: white;
                    cursor: pointer;
                }
                
                .directories-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
                    gap: 20px;
                    padding: 20px;
                }
                
                .directories-list {
                    display: block;
                    padding: 10px;
                }
                
                .directory-card {
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                    transition: all 0.3s;
                    border: 1px solid #eee;
                }
                
                .directory-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
                }
                
                .directory-list-item {
                    display: flex;
                    align-items: center;
                    padding: 15px;
                    border-bottom: 1px solid #eee;
                    background: white;
                    transition: all 0.3s;
                }
                
                .directory-list-item:hover {
                    background: #f8f9fa;
                }
                
                .cover-image {
                    width: 100%;
                    height: 200px;
                    object-fit: cover;
                    background: #C6C2B2;
                    cursor: pointer;
                }
                
                .list-cover {
                    width: 80px;
                    height: 60px;
                    object-fit: cover;
                    margin-right: 15px;
                    border-radius: 5px;
                }
                
                .video-indicator {
                    position: absolute;
                    top: 10px;
                    right: 10px;
                    background: rgba(0, 0, 0, 0.7);
                    color: white;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                
                .pdf-indicator {
                    position: absolute;
                    top: 10px;
                    right: 10px;
                    background: rgba(255, 87, 34, 0.9);
                    color: white;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                
                .document-indicator {
                    position: absolute;
                    top: 10px;
                    right: 10px;
                    background: rgba(76, 175, 80, 0.9);
                    color: white;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                
                .card-content {
                    padding: 15px;
                }
                
                .list-content {
                    flex: 1;
                }
                
                .directory-name {
                    font-size: 1.2em;
                    font-weight: bold;
                    margin-bottom: 8px;
                    color: #333;
                }
                
                .directory-path {
                    font-size: 0.9em;
                    color: #666;
                    margin-bottom: 10px;
                    word-break: break-all;
                }
                
                .directory-info {
                    display: flex;
                    justify-content: space-between;
                    font-size: 0.8em;
                    color: #888;
                    margin-bottom: 10px;
                }
                
                .list-info {
                    display: flex;
                    gap: 15px;
                    font-size: 0.8em;
                    color: #888;
                }
                
                .card-actions {
                    display: flex;
                    gap: 8px;
                    flex-wrap: wrap;
                }
                
                .list-actions {
                    display: flex;
                    gap: 8px;
                }
                
                .btn-small {
                    padding: 6px 12px;
                    font-size: 12px;
                    border-radius: 15px;
                }
                
                .status-online {
                    color: #4CAF50;
                    font-weight: bold;
                }
                
                .status-offline {
                    color: #FF9800;
                    font-weight: bold;
                }
                
                /* 文件列表样式 */
                .file-list-container {
                    padding: 10px;
                    border-top: 1px solid #eee;
                    background: #fafafa;
                }
                
                .file-list {
                    max-height: 120px;
                    overflow-y: auto;
                    font-size: 11px;
                    background: #f8f9fa;
                    border-radius: 5px;
                    padding: 5px;
                }
                
                .file-item {
                    display: flex;
                    align-items: center;
                    padding: 3px 5px;
                    cursor: pointer;
                    border-radius: 3px;
                    transition: background-color 0.2s;
                }
                
                .file-item:hover {
                    background: #e9ecef;
                }
                
                .file-icon {
                    margin-right: 8px;
                    font-size: 14px;
                    min-width: 20px;
                }
                
                .file-name {
                    color: #0066cc;
                    text-decoration: underline;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
                
                .file-name:hover {
                    color: #004499;
                }
                
                .no-files {
                    color: #999;
                    text-align: center;
                    padding: 10px;
                    font-size: 11px;
                }
                
                .loading {
                    text-align: center;
                    padding: 40px;
                    color: #666;
                    grid-column: 1 / -1;
                }
                
                .no-results {
                    text-align: center;
                    padding: 40px;
                    color: #999;
                    grid-column: 1 / -1;
                }
                
                .modal {
                    display: none;
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.9);
                    z-index: 1000;
                    align-items: center;
                    justify-content: center;
                }
                
                .modal-content {
                    background: transparent;
                    border-radius: 10px;
                    max-width: 95%;
                    max-height: 95%;
                    overflow: auto;
                    position: relative;
                    pointer-events: none;
                }
                
                .modal-image {
                    max-width: 100%;
                    max-height: 95vh;
                    display: block;
                    margin: 0 auto;
                }
                
                .modal-video {
                    pointer-events: auto;
                    width: 90%;
                    height: auto;
                    max-height: 90vh;
                    object-fit: cover;
                    background-color: black;
                    border: none;
                    outline: none;
                }

                /* 触摸屏优化 */
                .progress-bar-wrapper {
                    touch-action: none !important;
                    -webkit-tap-highlight-color: transparent;
                    cursor: pointer;
                }
                
                .control-btn {
                    touch-action: manipulation;
                    min-width: 44px;
                    min-height: 44px;
                }
                
                .video-container {
                    position: relative;
                    width: 100%;
                    height: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: black;
                }
                
                .modal-pdf {
                    width: 100%;
                    height: 100%;
                    border: none;
                    border-radius: 10px;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                }
                
                .close-modal {
                    position: absolute;
                    top: 10px;
                    right: 10px;
                    background: rgba(0, 0, 0, 0.7);
                    color: white;
                    border: none;
                    border-radius: 50%;
                    width: 30px;
                    height: 30px;
                    cursor: pointer;
                    z-index: 1001;
                }
                
                .file-type-badge {
                    position: absolute;
                    top: 10px;
                    left: 10px;
                    background: rgba(0, 0, 0, 0.7);
                    color: white;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                
                /* PDF模态框样式 */
                .pdf-modal-container {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.95);
                    z-index: 2000;
                    display: none;
                    flex-direction: column;
                }
                
                .pdf-modal-header {
                    background: rgba(255, 255, 255, 0.1);
                    padding: 15px 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    color: white;
                }
                
                .pdf-modal-title {
                    font-size: 18px;
                    font-weight: bold;
                }
                
                .pdf-modal-close {
                    background: rgba(255, 255, 255, 0.2);
                    border: none;
                    color: white;
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    cursor: pointer;
                    font-size: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .pdf-modal-close:hover {
                    background: rgba(255, 255, 255, 0.3);
                }
                
                .pdf-modal-content {
                    flex: 1;
                    display: flex;
                    padding: 20px;
                }
                
                .pdf-viewer-container {
                    flex: 1;
                    background: white;
                    border-radius: 10px;
                    overflow: hidden;
                    display: flex;
                    flex-direction: column;
                }
                
                .pdf-viewer-iframe {
                    flex: 1;
                    border: none;
                    width: 100%;
                    height: 100%;
                }
                
                .pdf-toolbar {
                    background: #f8f9fa;
                    padding: 15px 20px;
                    display: flex;
                    align-items: center;
                    gap: 15px;
                    border-bottom: 1px solid #dee2e6;
                }
                
                .pdf-toolbar-btn {
                    padding: 8px 16px;
                    border: 1px solid #6c757d;
                    background: white;
                    border-radius: 5px;
                    cursor: pointer;
                    transition: all 0.3s;
                    color: #6c757d;
                }
                
                .pdf-toolbar-btn:hover {
                    background: #6c757d;
                    color: white;
                }
                
                .pdf-toolbar-info {
                    margin-left: auto;
                    color: #6c757d;
                    font-size: 14px;
                }
                
                /* 文档模态框样式 */
                .document-modal-container {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.95);
                    z-index: 2000;
                    display: none;
                    flex-direction: column;
                }
                
                .document-modal-header {
                    background: rgba(255, 255, 255, 0.1);
                    padding: 15px 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    color: white;
                }
                
                .document-modal-title {
                    font-size: 18px;
                    font-weight: bold;
                }
                
                .document-modal-close {
                    background: rgba(255, 255, 255, 0.2);
                    border: none;
                    color: white;
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    cursor: pointer;
                    font-size: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .document-modal-close:hover {
                    background: rgba(255, 255, 255, 0.3);
                }
                
                .document-modal-content {
                    flex: 1;
                    display: flex;
                    padding: 20px;
                }
                
                .document-viewer-container {
                    flex: 1;
                    background: white;
                    border-radius: 10px;
                    overflow: hidden;
                    display: flex;
                    flex-direction: column;
                }
                
                .document-viewer-iframe {
                    flex: 1;
                    border: none;
                    width: 100%;
                    height: 100%;
                }
                
                .document-toolbar {
                    background: #f8f9fa;
                    padding: 15px 20px;
                    display: flex;
                    align-items: center;
                    gap: 15px;
                    border-bottom: 1px solid #dee2e6;
                }
                
                .document-toolbar-btn {
                    padding: 8px 16px;
                    border: 1px solid #6c757d;
                    background: white;
                    border-radius: 5px;
                    cursor: pointer;
                    transition: all 0.3s;
                    color: #6c757d;
                }
                
                .document-toolbar-btn:hover {
                    background: #6c757d;
                    color: white;
                }
                
                .document-toolbar-info {
                    margin-left: auto;
                    color: #6c757d;
                    font-size: 14px;
                }
                
                /* 目录过滤样式 */
                .filter-badge {
                    background: #6c5ce7;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 11px;
                    margin-left: 8px;
                }

                .path-selector-tree {
                    max-height: 400px;
                    overflow-y: auto;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 10px;
                }

                .file-list-row {
                    background: #fafafa;
                    border-bottom: 1px solid #eee;
                    margin-bottom: 5px;
                }

                .directories-list .file-list-container {
                    padding: 5px 10px 5px 95px;
                    border-top: none;
                }
                
                @media (max-width: 768px) {
                    .directories-grid {
                        grid-template-columns: 1fr;
                    }
                    
                    .controls {
                        flex-direction: column;
                        align-items: stretch;
                    }
                    
                    .search-box {
                        min-width: auto;
                    }
                    
                    .buttons {
                        justify-content: center;
                    }
                    
                    .card-actions, .list-actions {
                        justify-content: center;
                    }
                    
                    .status-bar {
                        flex-direction: column;
                        gap: 10px;
                        text-align: center;
                    }
                    
                    .modal-video {
                        width: 95%;
                    }
                    
                    .pdf-modal-content {
                        padding: 10px;
                    }
                    
                    .pdf-toolbar {
                        flex-wrap: wrap;
                        justify-content: center;
                    }
                    
                    .pdf-toolbar-info {
                        margin-left: 0;
                        width: 100%;
                        text-align: center;
                        margin-top: 10px;
                    }
                    
                    .document-modal-content {
                        padding: 10px;
                    }
                    
                    .document-toolbar {
                        flex-wrap: wrap;
                        justify-content: center;
                    }
                    
                    .document-toolbar-info {
                        margin-left: 0;
                        width: 100%;
                        text-align: center;
                        margin-top: 10px;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📁 ''' + ProjectInfo.NAME + '''</h1>
                    <div class="subtitle">版本 ''' + ProjectInfo.VERSION + ''' | Web客户端</div>
                </div>
                
                <div class="controls">
                    <div class="search-box">
                        <input type="text" id="searchInput" placeholder="搜索目录名称或路径...支持拼音首字母搜索" onkeypress="handleSearchKeyPress(event)">
                    </div>
                    <div class="buttons">
                        <button class="btn btn-primary" onclick="loadDirectories()">🔄 刷新</button>
                        <button class="btn btn-success" onclick="startScan()">🔍 扫描目录</button>
                        <button class="btn btn-secondary" onclick="showAdminPanel()">⚙️ 管理</button>
                        <button class="btn btn-warning" onclick="showSystemInfo()">ℹ️ 系统信息</button>
                        <button class="btn btn-info" onclick="toggleViewMode()">📋 列表视图</button>
                        <button class="btn btn-danger" onclick="clearSearch()">🗑️ 清除</button>
                    </div>
                </div>
                
                <!-- 目录过滤区域 -->
                <div class="filter-controls" style="margin-top: 10px; padding: 10px 20px; background: #f8f9fa; border-bottom: 1px solid #eee; display: flex; flex-wrap: wrap; gap: 10px; align-items: center;">
                    <span style="font-weight: bold;">📁 目录过滤:</span>
                    <input type="text" id="pathFilterInput" placeholder="输入路径关键词，多个用|分隔" 
                        style="padding: 8px 12px; border: 1px solid #ddd; border-radius: 5px; width: 300px;">
                    <button class="btn btn-small" onclick="applyPathFilter()" style="background: #6c5ce7; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer;">应用过滤</button>
                    <button class="btn btn-small" onclick="clearPathFilter()" style="background: #95a5a6; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer;">清除过滤</button>
                    <button class="btn btn-small" onclick="showPathFilterDialog()" style="background: #00b894; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer;">选择目录...</button>
                </div>

                <div class="view-controls">
                    <div class="filter-controls">
                        <select id="typeFilter" class="filter-select" onchange="filterByType()">
                            <option value="all">所有类型</option>
                            <option value="directory">仅目录</option>
                            <option value="file">仅文件</option>
                            <option value="video">视频文件</option>
                            <option value="image">图片文件</option>
                            <option value="pdf">PDF文件</option>
                            <option value="document">文档文件</option>
                        </select>
                        <select id="sortSelect" class="filter-select" onchange="sortDirectories()">
                            <option value="name">按名称排序</option>
                            <option value="date">按日期排序</option>
                            <option value="size">按大小排序</option>
                            <option value="path">按路径排序</option>
                        </select>
                        <select id="fileDisplayMode" class="filter-select" onchange="changeFileDisplayMode()">
                            <option value="all">显示所有文件</option>
                            <option value="images">仅显示图片</option>
                            <option value="videos">仅显示视频</option>
                            <option value="documents">仅显示文档</option>
                            <option value="none">隐藏文件</option>
                        </select>
                    </div>
                </div>
                
                <div class="status-bar">
                    <div id="statusInfo">正在加载...</div>
                    <div id="itemCount">-</div>
                </div>
                
                <div id="directoriesContainer" class="directories-grid">
                    <div class="loading">正在加载目录数据...</div>
                </div>
            </div>
            
            <!-- 图片预览模态框 -->
            <div id="mediaModal" class="modal" onclick="closeMediaModal()">
                <div class="modal-content">
                    <button class="close-modal" onclick="closeMediaModal()">×</button>
                    <img id="modalImage" class="modal-image" src="" onclick="event.stopPropagation()" style="display: none;">
                </div>
            </div>
            
            <!-- 视频播放模态框 -->
            <div id="videoModal" class="modal" style="display: none; flex-direction: column; justify-content: center; align-items: center;">
                <div class="modal-content" style="background: #1a1a2e; border-radius: 15px; width: 90%; max-width: 1200px; position: relative;">
                    <div class="video-header" style="display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; background: #16213e; border-radius: 15px 15px 0 0;">
                        <div class="video-title" id="videoTitle" style="color: white; font-size: 16px; font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">
                            视频播放器
                        </div>
                        <div class="video-controls-header">
                            <button class="close-modal" style="background: rgba(255,255,255,0.2); border: none; color: white; width: 35px; height: 35px; border-radius: 50%; cursor: pointer; font-size: 20px;" onclick="closeVideoModal()">×</button>
                        </div>
                    </div>
                    <div style="position: relative; background: black;">
                        <video id="modalVideo" class="modal-video" controls style="width: 100%; max-height: 70vh; display: block;" 
                            ontimeupdate="updateVideoProgress()" 
                            onloadedmetadata="onVideoLoaded()"
                            onseeked="onVideoSeeked()">
                            您的浏览器不支持视频播放
                        </video>
                        <div id="previewOverlay" style="position: absolute; bottom: 80px; left: 0; display: none; pointer-events: none; z-index: 100;">
                            <img id="previewImage" style="width: 160px; height: 90px; border-radius: 8px; border: 2px solid #fff; box-shadow: 0 4px 15px rgba(0,0,0,0.3); background: black;">
                            <div id="previewTime" style="text-align: center; color: white; font-size: 12px; margin-top: 5px; text-shadow: 1px 1px 1px black;"></div>
                        </div>
                    </div>
                    <div class="video-control-bar" style="padding: 15px 20px; background: #16213e; border-radius: 0 0 15px 15px;">
                        <div class="progress-container" style="margin-bottom: 10px;">
                            <div class="progress-bar-wrapper" style="position: relative; height: 8px; background: #333; border-radius: 4px; cursor: pointer;" 
                                onclick="seekVideo(event)" onmousemove="showPreview(event)" onmouseleave="hidePreview()">
                                <div id="videoProgressFill" style="width: 0%; height: 100%; background: #e74c3c; border-radius: 4px;"></div>
                                <div id="videoBufferedFill" style="position: absolute; top: 0; left: 0; height: 100%; background: rgba(255,255,255,0.3); border-radius: 4px; width: 0%; pointer-events: none;"></div>
                                <div id="previewIndicator" style="position: absolute; top: -20px; transform: translateX(-50%); display: none;">
                                    <div style="background: rgba(0,0,0,0.8); color: white; padding: 2px 6px; border-radius: 4px; font-size: 12px;" id="previewIndicatorTime">00:00</div>
                                </div>
                            </div>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                            <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
                                <button class="control-btn" onclick="seekBackward(10)" title="后退10秒" style="background: rgba(255,255,255,0.1); border: none; color: white; padding: 8px 12px; border-radius: 8px; cursor: pointer;">⏪ 10s</button>
                                <button class="control-btn" onclick="seekBackward(5)" title="后退5秒" style="background: rgba(255,255,255,0.1); border: none; color: white; padding: 8px 12px; border-radius: 8px; cursor: pointer;">◀◀ 5s</button>
                                <button id="playPauseBtn" class="control-btn" onclick="togglePlayPause()" style="background: #e74c3c; border: none; color: white; width: 45px; height: 45px; border-radius: 50%; font-size: 20px; cursor: pointer;">⏸</button>
                                <button class="control-btn" onclick="seekForward(5)" title="前进5秒" style="background: rgba(255,255,255,0.1); border: none; color: white; padding: 8px 12px; border-radius: 8px; cursor: pointer;">5s ▶▶</button>
                                <button class="control-btn" onclick="seekForward(10)" title="前进10秒" style="background: rgba(255,255,255,0.1); border: none; color: white; padding: 8px 12px; border-radius: 8px; cursor: pointer;">10s ⏩</button>
                                <span id="videoTimeDisplay" style="color: white; font-size: 14px; margin-left: 5px;">00:00 / 00:00</span>
                            </div>
                            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                                <button class="control-btn" onclick="changePlaybackRate(0.75)" style="background: rgba(255,255,255,0.1); border: none; color: white; padding: 6px 10px; border-radius: 8px; cursor: pointer;">0.75x</button>
                                <button class="control-btn" onclick="changePlaybackRate(1)" style="background: #e74c3c; border: none; color: white; padding: 6px 10px; border-radius: 8px; cursor: pointer;">1x</button>
                                <button class="control-btn" onclick="changePlaybackRate(1.25)" style="background: rgba(255,255,255,0.1); border: none; color: white; padding: 6px 10px; border-radius: 8px; cursor: pointer;">1.25x</button>
                                <button class="control-btn" onclick="changePlaybackRate(1.5)" style="background: rgba(255,255,255,0.1); border: none; color: white; padding: 6px 10px; border-radius: 8px; cursor: pointer;">1.5x</button>
                                <button class="control-btn" onclick="changePlaybackRate(2)" style="background: rgba(255,255,255,0.1); border: none; color: white; padding: 6px 10px; border-radius: 8px; cursor: pointer;">2x</button>
                                <button class="control-btn" onclick="toggleFullscreen()" style="background: rgba(255,255,255,0.1); border: none; color: white; padding: 6px 10px; border-radius: 8px; cursor: pointer;">⛶ 全屏</button>
                                <button class="control-btn" onclick="downloadVideo()" style="background: rgba(255,255,255,0.1); border: none; color: white; padding: 6px 10px; border-radius: 8px; cursor: pointer;">⬇ 下载</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- PDF预览模态框 -->
            <div id="pdfModal" class="pdf-modal-container">
                <div class="pdf-modal-header">
                    <div class="pdf-modal-title" id="pdfModalTitle">PDF预览</div>
                    <button class="pdf-modal-close" onclick="closePdfModal()">×</button>
                </div>
                <div class="pdf-modal-content">
                    <div class="pdf-viewer-container">
                        <div class="pdf-toolbar">
                            <button class="pdf-toolbar-btn" onclick="downloadPdf()">📥 下载PDF</button>
                            <button class="pdf-toolbar-btn" onclick="printPdf()">🖨️ 打印</button>
                            <button class="pdf-toolbar-btn" onclick="zoomInPdf()">🔍 放大</button>
                            <button class="pdf-toolbar-btn" onclick="zoomOutPdf()">🔍 缩小</button>
                            <button class="pdf-toolbar-btn" onclick="fitToWidthPdf()">📏 适合宽度</button>
                            <button class="pdf-toolbar-btn" onclick="fitToPagePdf()">📄 适合页面</button>
                            <div class="pdf-toolbar-info" id="pdfToolbarInfo">就绪</div>
                        </div>
                        <iframe id="modalPdf" class="pdf-viewer-iframe" src=""></iframe>
                    </div>
                </div>
            </div>
            
            <!-- 文档预览模态框 -->
            <div id="documentModal" class="document-modal-container">
                <div class="document-modal-header">
                    <div class="document-modal-title" id="documentModalTitle">文档预览</div>
                    <button class="document-modal-close" onclick="closeDocumentModal()">×</button>
                </div>
                <div class="document-modal-content">
                    <div class="document-viewer-container">
                        <div class="document-toolbar">
                            <button class="document-toolbar-btn" onclick="downloadDocument()">📥 下载文档</button>
                            <button class="document-toolbar-btn" onclick="printDocument()">🖨️ 打印</button>
                            <button class="document-toolbar-btn" onclick="zoomInDocument()">🔍 放大</button>
                            <button class="document-toolbar-btn" onclick="zoomOutDocument()">🔍 缩小</button>
                            <div class="document-toolbar-info" id="documentToolbarInfo">就绪</div>
                        </div>
                        <iframe id="modalDocument" class="document-viewer-iframe" src=""></iframe>
                    </div>
                </div>
            </div>
            
            <script>
                let currentData = [];
                let currentViewMode = 'grid';
                let currentTypeFilter = 'all';
                let currentSort = 'name';
                let currentFileDisplayMode = 'all';
                let currentPathFilter = '';
                let currentPdfZoom = 1.0;
                let currentDocumentZoom = 1.0;
                
                // 页面加载完成后初始化
                document.addEventListener('DOMContentLoaded', function() {
                    loadDirectories();
                    updateSystemStatus();
                    setInterval(updateSystemStatus, 30000);
                });
                
                // 切换文件显示模式
                function changeFileDisplayMode() {
                    currentFileDisplayMode = document.getElementById('fileDisplayMode').value;
                    applyFiltersAndSort();
                }
                
                // 应用路径过滤
                function applyPathFilter() {
                    const filterValue = document.getElementById('pathFilterInput').value.trim();
                    currentPathFilter = filterValue;
                    
                    if (filterValue) {
                        updateStatus(`应用路径过滤: ${filterValue}`);
                        const filterInput = document.getElementById('pathFilterInput');
                        filterInput.style.borderColor = '#6c5ce7';
                        filterInput.style.backgroundColor = '#f3f0ff';
                        showFilterBadge(filterValue);
                    }
                    
                    loadDirectoriesWithFilter();
                }

                // 清除路径过滤
                function clearPathFilter() {
                    currentPathFilter = '';
                    document.getElementById('pathFilterInput').value = '';
                    
                    const filterInput = document.getElementById('pathFilterInput');
                    filterInput.style.borderColor = '#ddd';
                    filterInput.style.backgroundColor = 'white';
                    
                    hideFilterBadge();
                    updateStatus('已清除路径过滤');
                    loadDirectoriesWithFilter();
                }

                // 显示过滤徽章
                function showFilterBadge(filterValue) {
                    let badge = document.getElementById('filterBadge');
                    if (!badge) {
                        badge = document.createElement('span');
                        badge.id = 'filterBadge';
                        badge.className = 'filter-badge';
                        const controlsDiv = document.querySelector('.filter-controls');
                        if (controlsDiv) {
                            controlsDiv.appendChild(badge);
                        }
                    }
                    const shortFilter = filterValue.length > 30 ? filterValue.substring(0, 30) + '...' : filterValue;
                    badge.textContent = `🔍 ${shortFilter}`;
                    badge.style.display = 'inline-block';
                }

                // 隐藏过滤徽章
                function hideFilterBadge() {
                    const badge = document.getElementById('filterBadge');
                    if (badge) {
                        badge.style.display = 'none';
                    }
                }

                // 带过滤的加载目录
                function loadDirectoriesWithFilter() {
                    showLoading();
                    
                    let url = '/api/directories?';
                    const params = new URLSearchParams();
                    
                    if (currentTypeFilter !== 'all') {
                        params.append('type', currentTypeFilter);
                    }
                    if (currentSort !== 'name') {
                        params.append('sort', currentSort);
                    }
                    if (currentPathFilter) {
                        params.append('path_filter', currentPathFilter);
                    }
                    
                    url += params.toString();
                    
                    fetch(url)
                        .then(response => response.json())
                        .then(data => {
                            currentData = data.directories || [];
                            applyFiltersAndSort();
                            updateItemCount(currentData.length);
                            updateStatus(`数据加载成功`);
                        })
                        .catch(error => {
                            console.error('加载目录失败:', error);
                            updateStatus('加载失败: ' + error.message, 'error');
                            showError('无法加载目录数据');
                        });
                }

                // 显示目录选择器对话框
                async function showPathFilterDialog() {
                    try {
                        const response = await fetch('/api/directories/paths');
                        const data = await response.json();
                        
                        if (!data.tree || data.tree.length === 0) {
                            alert('没有可用的目录数据');
                            return;
                        }
                        
                        const modal = document.createElement('div');
                        modal.className = 'modal';
                        modal.style.display = 'flex';
                        modal.style.backgroundColor = 'rgba(0,0,0,0.5)';
                        modal.style.alignItems = 'center';
                        modal.style.justifyContent = 'center';
                        
                        const dialog = document.createElement('div');
                        dialog.style.backgroundColor = 'white';
                        dialog.style.borderRadius = '10px';
                        dialog.style.width = '500px';
                        dialog.style.maxWidth = '90%';
                        dialog.style.maxHeight = '80vh';
                        dialog.style.display = 'flex';
                        dialog.style.flexDirection = 'column';
                        
                        // 头部
                        const header = document.createElement('div');
                        header.style.padding = '15px 20px';
                        header.style.borderBottom = '1px solid #ddd';
                        header.style.display = 'flex';
                        header.style.justifyContent = 'space-between';
                        header.style.alignItems = 'center';
                        header.innerHTML = `<h3 style="margin:0;">选择要显示的目录</h3><button style="background:none;border:none;font-size:24px;cursor:pointer;">&times;</button>`;
                        
                        // 目录树区域
                        const content = document.createElement('div');
                        content.style.flex = '1';
                        content.style.overflowY = 'auto';
                        content.style.padding = '15px';
                        
                        const treeContainer = document.createElement('div');
                        treeContainer.className = 'path-selector-tree';
                        
                        function renderTree(nodes, level = 0) {
                            for (const node of nodes) {
                                const nodeDiv = document.createElement('div');
                                nodeDiv.style.marginLeft = `${level * 20}px`;
                                nodeDiv.style.marginBottom = '4px';
                                
                                const checkbox = document.createElement('input');
                                checkbox.type = 'checkbox';
                                checkbox.value = decodeURIComponent(node.full_path);
                                checkbox.style.marginRight = '8px';
                                
                                const label = document.createElement('label');
                                label.textContent = node.name;
                                label.style.cursor = 'pointer';
                                
                                nodeDiv.appendChild(checkbox);
                                nodeDiv.appendChild(label);
                                treeContainer.appendChild(nodeDiv);
                                
                                if (node.children && node.children.length) {
                                    renderTree(node.children, level + 1);
                                }
                            }
                        }
                        
                        renderTree(data.tree);
                        content.appendChild(treeContainer);
                        
                        // 快捷按钮
                        const quickActions = document.createElement('div');
                        quickActions.style.padding = '10px 15px';
                        quickActions.style.borderBottom = '1px solid #eee';
                        quickActions.style.display = 'flex';
                        quickActions.style.gap = '10px';
                        quickActions.style.flexWrap = 'wrap';
                        
                        const selectAllBtn = document.createElement('button');
                        selectAllBtn.textContent = '全选';
                        selectAllBtn.style.padding = '6px 12px';
                        selectAllBtn.style.background = '#6c5ce7';
                        selectAllBtn.style.color = 'white';
                        selectAllBtn.style.border = 'none';
                        selectAllBtn.style.borderRadius = '4px';
                        selectAllBtn.style.cursor = 'pointer';
                        selectAllBtn.onclick = () => {
                            const checkboxes = treeContainer.querySelectorAll('input[type="checkbox"]');
                            checkboxes.forEach(cb => cb.checked = true);
                        };
                        
                        const clearAllBtn = document.createElement('button');
                        clearAllBtn.textContent = '全不选';
                        clearAllBtn.style.padding = '6px 12px';
                        clearAllBtn.style.background = '#95a5a6';
                        clearAllBtn.style.color = 'white';
                        clearAllBtn.style.border = 'none';
                        clearAllBtn.style.borderRadius = '4px';
                        clearAllBtn.style.cursor = 'pointer';
                        clearAllBtn.onclick = () => {
                            const checkboxes = treeContainer.querySelectorAll('input[type="checkbox"]');
                            checkboxes.forEach(cb => cb.checked = false);
                        };
                        
                        const selectParentBtn = document.createElement('button');
                        selectParentBtn.textContent = '选择父级目录';
                        selectParentBtn.style.padding = '6px 12px';
                        selectParentBtn.style.background = '#00b894';
                        selectParentBtn.style.color = 'white';
                        selectParentBtn.style.border = 'none';
                        selectParentBtn.style.borderRadius = '4px';
                        selectParentBtn.style.cursor = 'pointer';
                        selectParentBtn.onclick = () => {
                            const topLevelCheckboxes = treeContainer.querySelectorAll(':scope > div > input[type="checkbox"]');
                            topLevelCheckboxes.forEach(cb => cb.checked = true);
                        };
                        
                        quickActions.appendChild(selectAllBtn);
                        quickActions.appendChild(clearAllBtn);
                        quickActions.appendChild(selectParentBtn);
                        content.insertBefore(quickActions, content.firstChild);
                        
                        // 按钮区域
                        const footer = document.createElement('div');
                        footer.style.padding = '15px 20px';
                        footer.style.borderTop = '1px solid #ddd';
                        footer.style.display = 'flex';
                        footer.style.justifyContent = 'flex-end';
                        footer.style.gap = '10px';
                        
                        const applyBtn = document.createElement('button');
                        applyBtn.textContent = '应用过滤';
                        applyBtn.style.padding = '8px 20px';
                        applyBtn.style.background = '#6c5ce7';
                        applyBtn.style.color = 'white';
                        applyBtn.style.border = 'none';
                        applyBtn.style.borderRadius = '5px';
                        applyBtn.style.cursor = 'pointer';
                        applyBtn.onclick = () => {
                            const checkboxes = treeContainer.querySelectorAll('input[type="checkbox"]:checked');
                            const paths = Array.from(checkboxes).map(cb => cb.value);
                            const filterValue = paths.join('|');
                            document.getElementById('pathFilterInput').value = filterValue;
                            applyPathFilter();
                            modal.remove();
                        };
                        
                        const cancelBtn = document.createElement('button');
                        cancelBtn.textContent = '取消';
                        cancelBtn.style.padding = '8px 20px';
                        cancelBtn.style.background = '#95a5a6';
                        cancelBtn.style.color = 'white';
                        cancelBtn.style.border = 'none';
                        cancelBtn.style.borderRadius = '5px';
                        cancelBtn.style.cursor = 'pointer';
                        cancelBtn.onclick = () => modal.remove();
                        
                        footer.appendChild(applyBtn);
                        footer.appendChild(cancelBtn);
                        
                        dialog.appendChild(header);
                        dialog.appendChild(content);
                        dialog.appendChild(footer);
                        modal.appendChild(dialog);
                        document.body.appendChild(modal);
                        
                        header.querySelector('button').onclick = () => modal.remove();
                        modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
                        
                        // 设置初始选中
                        if (currentPathFilter) {
                            const selectedPaths = currentPathFilter.split('|');
                            const checkboxes = treeContainer.querySelectorAll('input[type="checkbox"]');
                            checkboxes.forEach(cb => {
                                if (selectedPaths.some(p => cb.value.includes(p) || p.includes(cb.value))) {
                                    cb.checked = true;
                                }
                            });
                        }
                        
                    } catch (error) {
                        console.error('加载目录树失败:', error);
                        alert('无法加载目录树: ' + error.message);
                    }
                }

                // 加载目录数据
                function loadDirectories(searchTerm = '') {
                    showLoading();
                    
                    let url = searchTerm ? '/api/directories/search?q=' + encodeURIComponent(searchTerm) : '/api/directories?';
                    
                    if (!searchTerm) {
                        const params = new URLSearchParams();
                        if (currentTypeFilter !== 'all') {
                            params.append('type', currentTypeFilter);
                        }
                        if (currentSort !== 'name') {
                            params.append('sort', currentSort);
                        }
                        if (currentPathFilter) {
                            params.append('path_filter', currentPathFilter);
                        }
                        url += params.toString();
                    } else {
                        url += '&type=' + currentTypeFilter + '&sort=' + currentSort;
                        if (currentPathFilter) {
                            url += '&path_filter=' + encodeURIComponent(currentPathFilter);
                        }
                    }
                    
                    fetch(url)
                        .then(response => response.json())
                        .then(data => {
                            currentData = data.directories || [];
                            applyFiltersAndSort();
                            updateItemCount(currentData.length);
                            updateStatus('数据加载成功');
                        })
                        .catch(error => {
                            console.error('加载目录失败:', error);
                            updateStatus('加载失败: ' + error.message, 'error');
                            showError('无法加载目录数据');
                        });
                }
                
                // 应用过滤和排序
                function applyFiltersAndSort() {
                    let filteredData = [...currentData];
                    
                    if (currentTypeFilter !== 'all') {
                        filteredData = filteredData.filter(item => {
                            if (currentTypeFilter === 'directory') return item.is_directory;
                            if (currentTypeFilter === 'file') return !item.is_directory;
                            if (currentTypeFilter === 'video') return isVideoFile(item.name);
                            if (currentTypeFilter === 'image') return isImageFile(item.name);
                            if (currentTypeFilter === 'pdf') return isPdfFile(item.name);
                            if (currentTypeFilter === 'document') return isDocumentFile(item.name);
                            return true;
                        });
                    }
                    
                    filteredData.sort((a, b) => {
                        switch (currentSort) {
                            case 'name':
                                return a.name.localeCompare(b.name, 'zh-CN');
                            case 'date':
                                return new Date(b.last_modified) - new Date(a.last_modified);
                            case 'size':
                                return 0;
                            case 'path':
                                return a.path.localeCompare(b.path, 'zh-CN');
                            default:
                                return 0;
                        }
                    });
                    
                    displayDirectories(filteredData);
                }
                
                // 类型过滤
                function filterByType() {
                    currentTypeFilter = document.getElementById('typeFilter').value;
                    applyFiltersAndSort();
                }
                
                // 排序
                function sortDirectories() {
                    currentSort = document.getElementById('sortSelect').value;
                    applyFiltersAndSort();
                }
                
                // 切换视图模式
                function toggleViewMode() {
                    currentViewMode = currentViewMode === 'grid' ? 'list' : 'grid';
                    const btn = document.querySelector('.btn-info');
                    btn.textContent = currentViewMode === 'grid' ? '📋 列表视图' : '🔲 网格视图';
                    applyFiltersAndSort();
                }
                
                // 获取文件列表HTML
                async function getFileListHtml(directoryPath, displayMode) {
                    try {
                        const response = await fetch(`/api/directory/files?path=${encodeURIComponent(directoryPath)}&mode=${displayMode}`);
                        const data = await response.json();
                        
                        if (!data.files || data.files.length === 0) {
                            return '<div class="no-files">📭 无文件</div>';
                        }
                        
                        let html = '<div class="file-list">';
                        for (const file of data.files) {
                            html += `
                                <div class="file-item" onclick="event.stopPropagation(); openFile('${encodeURIComponent(file.path)}')">
                                    <span class="file-icon">${file.icon}</span>
                                    <span class="file-name" title="${escapeHtml(file.name)}">${escapeHtml(file.name)}</span>
                                </div>
                            `;
                        }
                        if (data.totalCount > data.files.length) {
                            html += `<div class="file-item" style="color: #666;">... 还有 ${data.totalCount - data.files.length} 个文件</div>`;
                        }
                        html += '</div>';
                        return html;
                    } catch (error) {
                        console.error('获取文件列表失败:', error);
                        return '<div class="no-files">❌ 加载失败</div>';
                    }
                }
                
                // 打开文件
                function openFile(encodedPath) {
                    const filePath = decodeURIComponent(encodedPath);
                    if (isVideoFile(filePath)) {
                        window.open('/api/video?path=' + encodedPath, '_blank');
                    } else if (isPdfFile(filePath)) {
                        showPdfModal(filePath);
                    } else if (isDocumentFile(filePath)) {
                        showDocumentModal(filePath);
                    } else {
                        window.open('/api/document?path=' + encodedPath, '_blank');
                    }
                }
                
                // 显示目录列表
                async function displayDirectories(directories) {
                    const container = document.getElementById('directoriesContainer');
                    container.className = currentViewMode === 'grid' ? 'directories-grid' : 'directories-list';
                    
                    if (directories.length === 0) {
                        container.innerHTML = '<div class="no-results">📭 没有找到匹配的目录</div>';
                        return;
                    }
                    
                    let html = '';
                    
                    for (const dir of directories) {
                        const encodedPath = encodeURIComponent(dir.path);
                        const isVideo = isVideoFile(dir.name);
                        const isImage = isImageFile(dir.name);
                        const isPdf = isPdfFile(dir.name);
                        const isDocument = isDocumentFile(dir.name);
                        const fileType = !dir.is_directory ? (
                            isVideo ? 'video' : 
                            isImage ? 'image' : 
                            isPdf ? 'pdf' :
                            isDocument ? 'document' : 'file'
                        ) : 'directory';
                        
                        if (currentViewMode === 'grid') {
                            html += `
                                <div class="directory-card" data-type="${fileType}" data-id="${dir.id}">
                                    <div style="position: relative;">
                                        ${!dir.is_directory ? `<div class="file-type-badge">${getFileTypeBadge(dir.name)}</div>` : ''}
                                        <img class="cover-image" 
                                            src="/api/cover?path=${encodedPath}" 
                                            alt="${escapeHtml(dir.name)}"
                                            onclick="showMedia('${encodedPath}', '${fileType}')"
                                            onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2Y4ZjlmYSIvPjx0ZXh0IHg9IjEwMCIgeT0iMTAwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM2Yzc1N2QiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIwLjM1ZW0iPuiNieeUqOaAp+aEn+WbvueJhzwvdGV4dD48L3N2Zz4='">
                                        ${isVideo ? '<div class="video-indicator">🎬 视频</div>' : ''}
                                        ${isPdf ? '<div class="pdf-indicator">📄 PDF</div>' : ''}
                                        ${isDocument ? '<div class="document-indicator">📝 文档</div>' : ''}
                                    </div>
                                    <div class="card-content">
                                        <div class="directory-name">${escapeHtml(dir.name)}</div>
                                        <div class="directory-path" title="${escapeHtml(dir.path)}">${escapeHtml(dir.path)}</div>
                                        <div class="directory-info">
                                            <span>修改: ${formatDate(dir.last_modified)}</span>
                                            <span>ID: ${dir.id}</span>
                                            <span class="${dir.exists ? 'status-online' : 'status-offline'}">
                                                ${dir.exists ? '✅ 上架' : '❌ 下架'}
                                            </span>
                                        </div>
                                        <div class="card-actions">
                                            <button class="btn btn-primary btn-small" onclick="openDirectory('${escapeHtml(dir.path)}', ${dir.id})">📂 打开</button>
                                            <button class="btn btn-success btn-small" onclick="showMedia('${encodedPath}', '${fileType}')">
                                                ${isVideo ? '🎬 播放' : isImage ? '🖼️ 查看' : isPdf ? '📄 查看PDF' : isDocument ? '📝 查看文档' : '📄 查看'}
                                            </button>
                                            <button class="btn btn-info btn-small" onclick="showDatabaseInfo(${dir.id})">ℹ️ 信息</button>
                                        </div>
                                    </div>
                                    <div class="file-list-container" id="filelist-${dir.id}">
                                        <div class="no-files">📷 加载中...</div>
                                    </div>
                                </div>
                            `;
                        } else {
                            html += `
                                <div class="directory-list-item" data-type="${fileType}" data-id="${dir.id}">
                                    <img class="list-cover" 
                                        src="/api/cover?path=${encodedPath}" 
                                        alt="${escapeHtml(dir.name)}"
                                        onclick="showMedia('${encodedPath}', '${fileType}')"
                                        onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjgwIiBoZWlnaHQ9IjYwIiBmaWxsPSIjZjhmOWZhIi8+PHRleHQgeD0iNDAiIHk9IjMwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTIiIGZpbGw9IiM2Yzc1N2QiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIwLjNlbSI+5Y2V5L2N5Zu+54mHPC90ZXh0Pjwvc3ZnPg==">
                                    <div class="list-content">
                                        <div class="directory-name">${escapeHtml(dir.name)} ${isVideo ? '🎬' : isImage ? '🖼️' : isPdf ? '📄' : isDocument ? '📝' : ''}</div>
                                        <div class="directory-path" title="${escapeHtml(dir.path)}">${escapeHtml(dir.path)}</div>
                                        <div class="list-info">
                                            <span>修改: ${formatDate(dir.last_modified)}</span>
                                            <span>ID: ${dir.id}</span>
                                            <span class="${dir.exists ? 'status-online' : 'status-offline'}">
                                                ${dir.exists ? '✅ 上架' : '❌ 下架'}
                                            </span>
                                        </div>
                                    </div>
                                    <div class="list-actions">
                                        <button class="btn btn-primary btn-small" onclick="openDirectory('${escapeHtml(dir.path)}', ${dir.id})">打开</button>
                                        <button class="btn btn-success btn-small" onclick="showMedia('${encodedPath}', '${fileType}')">
                                            ${isVideo ? '播放' : isImage ? '查看' : isPdf ? '查看PDF' : isDocument ? '查看文档' : '查看'}
                                        </button>
                                        <button class="btn btn-info btn-small" onclick="showDatabaseInfo(${dir.id})">信息</button>
                                    </div>
                                </div>
                                <div class="file-list-row" id="filelist-row-${dir.id}" style="display: block;">
                                    <div class="file-list-container" id="filelist-${dir.id}">
                                        <div class="no-files">📷 加载中...</div>
                                    </div>
                                </div>
                            `;
                        }
                    }
                    
                    container.innerHTML = html;
                    
                    for (const dir of directories) {
                        const listId = `filelist-${dir.id}`;
                        getFileListHtml(dir.path, currentFileDisplayMode).then(fileListHtml => {
                            const elem = document.getElementById(listId);
                            if (elem) elem.innerHTML = fileListHtml;
                        });
                    }
                }
                
                // HTML转义
                function escapeHtml(text) {
                    if (!text) return '';
                    return text.replace(/[&<>]/g, function(m) {
                        if (m === '&') return '&amp;';
                        if (m === '<') return '&lt;';
                        if (m === '>') return '&gt;';
                        return m;
                    });
                }
                
                // 文件类型检测
                function isPdfFile(filename) {
                    return filename.toLowerCase().endsWith('.pdf');
                }
                
                function isDocumentFile(filename) {
                    const documentExtensions = [
                        '.pdf', '.txt', '.doc', '.docx', '.ppt', '.pptx', '.xls', 
                        '.xlsx', '.rtf', '.odt', '.ods', '.odp', '.pages', '.numbers',
                        '.key', '.epub', '.mobi', '.azw', '.azw3', '.fb2', '.lit',
                        '.prc', '.pdb', '.chm', '.djvu', '.djv'
                    ];
                    return documentExtensions.some(ext => filename.toLowerCase().endsWith(ext));
                }
                
                function isVideoFile(filename) {
                    const videoExtensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'];
                    return videoExtensions.some(ext => filename.toLowerCase().endsWith(ext));
                }
                
                function isImageFile(filename) {
                    const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'];
                    return imageExtensions.some(ext => filename.toLowerCase().endsWith(ext));
                }
                
                function getFileTypeBadge(filename) {
                    if (isVideoFile(filename)) return '视频';
                    if (isImageFile(filename)) return '图片';
                    if (isPdfFile(filename)) return 'PDF';
                    if (isDocumentFile(filename)) return '文档';
                    return '文件';
                }
                
                // 格式化日期
                function formatDate(dateString) {
                    try {
                        const date = new Date(dateString);
                        return date.toLocaleDateString('zh-CN');
                    } catch(e) {
                        return dateString;
                    }
                }
                
                // 搜索处理
                function handleSearch() {
                    const searchTerm = document.getElementById('searchInput').value.trim();
                    loadDirectories(searchTerm);
                }
                
                function handleSearchKeyPress(event) {
                    if (event.key === 'Enter') {
                        handleSearch();
                    }
                }
                
                // 清除搜索
                function clearSearch() {
                    document.getElementById('searchInput').value = '';
                    loadDirectories();
                    updateStatus('搜索内容已清除');
                }
                
                // 打开目录
                async function openDirectory(path, dbId = null) {
                    try {
                        updateStatus('正在打开目录...');
                        
                        const requestData = { path: path };
                        if (dbId) {
                            requestData.db_id = dbId;
                        }
                        
                        const response = await fetch('/api/open', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify(requestData)
                        });
                        
                        const result = await response.json();
                        if (result.success) {
                            updateStatus('目录已打开');
                        } else {
                            updateStatus('打开失败: ' + result.error, 'error');
                        }
                    } catch (error) {
                        updateStatus('打开失败: ' + error.message, 'error');
                    }
                }
                
                // 显示媒体
                function showMedia(path, mediaType) {
                    const decodedPath = decodeURIComponent(path);
                    
                    if (mediaType === 'video') {
                        window.open('/api/video?path=' + path, '_blank');
                    } else if (mediaType === 'pdf') {
                        showPdfModal(decodedPath);
                    } else if (mediaType === 'document') {
                        if (decodedPath.toLowerCase().endsWith('.epub')) {
                            const epubUrl = '/api/document?path=' + path + '&preview=true';
                            window.open(epubUrl, '_blank', 'width=1200,height=800,resizable=yes,scrollbars=yes');
                        } else {
                            showDocumentModal(decodedPath);
                        }
                    } else {
                        const modal = document.getElementById('mediaModal');
                        const modalImage = document.getElementById('modalImage');
                        modalImage.src = '/api/cover?path=' + path;
                        modalImage.style.display = 'block';
                        modal.style.display = 'flex';
                    }
                }
                
                // PDF相关函数
                function showPdfModal(pdfPath) {
                    const pdfModal = document.getElementById('pdfModal');
                    const pdfIframe = document.getElementById('modalPdf');
                    const pdfTitle = document.getElementById('pdfModalTitle');
                    
                    const fileName = pdfPath.split('/').pop() || 'PDF文档';
                    pdfTitle.textContent = `PDF预览 - ${fileName}`;
                    
                    const pdfUrl = '/api/pdf?path=' + encodeURIComponent(pdfPath);
                    pdfIframe.src = pdfUrl;
                    
                    currentPdfZoom = 1.0;
                    updatePdfZoomInfo();
                    
                    pdfModal.style.display = 'flex';
                    document.addEventListener('keydown', handlePdfKeydown);
                }
                
                function handlePdfKeydown(event) {
                    const pdfModal = document.getElementById('pdfModal');
                    if (pdfModal.style.display !== 'flex') return;
                    
                    switch (event.key) {
                        case 'Escape':
                            closePdfModal();
                            break;
                        case '+':
                        case '=':
                            event.preventDefault();
                            zoomInPdf();
                            break;
                        case '-':
                            event.preventDefault();
                            zoomOutPdf();
                            break;
                        case '0':
                            event.preventDefault();
                            fitToWidthPdf();
                            break;
                    }
                }
                
                function downloadPdf() {
                    const pdfIframe = document.getElementById('modalPdf');
                    const pdfUrl = pdfIframe.src;
                    const link = document.createElement('a');
                    link.href = pdfUrl;
                    link.download = 'document.pdf';
                    link.click();
                }
                
                function printPdf() {
                    const pdfIframe = document.getElementById('modalPdf');
                    pdfIframe.contentWindow.print();
                }
                
                function zoomInPdf() {
                    currentPdfZoom = Math.min(currentPdfZoom + 0.1, 3.0);
                    applyPdfZoom();
                }
                
                function zoomOutPdf() {
                    currentPdfZoom = Math.max(currentPdfZoom - 0.1, 0.5);
                    applyPdfZoom();
                }
                
                function fitToWidthPdf() {
                    currentPdfZoom = 1.0;
                    applyPdfZoom();
                }
                
                function fitToPagePdf() {
                    currentPdfZoom = 1.0;
                    applyPdfZoom();
                }
                
                function applyPdfZoom() {
                    const pdfIframe = document.getElementById('modalPdf');
                    try {
                        pdfIframe.style.transform = `scale(${currentPdfZoom})`;
                        pdfIframe.style.transformOrigin = '0 0';
                        updatePdfZoomInfo();
                    } catch (e) {
                        console.error('应用PDF缩放失败:', e);
                    }
                }
                
                function updatePdfZoomInfo() {
                    const zoomInfo = document.getElementById('pdfToolbarInfo');
                    zoomInfo.textContent = `缩放: ${Math.round(currentPdfZoom * 100)}%`;
                }
                
                function closePdfModal() {
                    const pdfModal = document.getElementById('pdfModal');
                    const pdfIframe = document.getElementById('modalPdf');
                    
                    pdfIframe.src = '';
                    pdfIframe.style.transform = '';
                    pdfModal.style.display = 'none';
                    document.removeEventListener('keydown', handlePdfKeydown);
                }
                
                // 文档相关函数
                function showDocumentModal(docPath) {
                    const docModal = document.getElementById('documentModal');
                    const docIframe = document.getElementById('modalDocument');
                    const docTitle = document.getElementById('documentModalTitle');
                    
                    const fileName = docPath.split('/').pop() || '文档';
                    docTitle.textContent = `文档预览 - ${fileName}`;
                    
                    const docUrl = '/api/document?path=' + encodeURIComponent(docPath);
                    docIframe.src = docUrl;
                    
                    currentDocumentZoom = 1.0;
                    updateDocumentZoomInfo();
                    
                    docModal.style.display = 'flex';
                    document.addEventListener('keydown', handleDocumentKeydown);
                }
                
                function handleDocumentKeydown(event) {
                    const docModal = document.getElementById('documentModal');
                    if (docModal.style.display !== 'flex') return;
                    
                    switch (event.key) {
                        case 'Escape':
                            closeDocumentModal();
                            break;
                        case '+':
                        case '=':
                            event.preventDefault();
                            zoomInDocument();
                            break;
                        case '-':
                            event.preventDefault();
                            zoomOutDocument();
                            break;
                    }
                }
                
                function downloadDocument() {
                    const docIframe = document.getElementById('modalDocument');
                    const docUrl = docIframe.src;
                    const link = document.createElement('a');
                    link.href = docUrl;
                    link.download = 'document';
                    link.click();
                }
                
                function printDocument() {
                    const docIframe = document.getElementById('modalDocument');
                    docIframe.contentWindow.print();
                }
                
                function zoomInDocument() {
                    const docIframe = document.getElementById('modalDocument');
                    try {
                        currentDocumentZoom = Math.min(currentDocumentZoom + 0.1, 3.0);
                        docIframe.style.zoom = currentDocumentZoom;
                        updateDocumentZoomInfo();
                    } catch (e) {
                        console.error('文档放大失败:', e);
                    }
                }
                
                function zoomOutDocument() {
                    const docIframe = document.getElementById('modalDocument');
                    try {
                        currentDocumentZoom = Math.max(currentDocumentZoom - 0.1, 0.5);
                        docIframe.style.zoom = currentDocumentZoom;
                        updateDocumentZoomInfo();
                    } catch (e) {
                        console.error('文档缩小失败:', e);
                    }
                }
                
                function updateDocumentZoomInfo() {
                    const zoomInfo = document.getElementById('documentToolbarInfo');
                    zoomInfo.textContent = `缩放: ${Math.round(currentDocumentZoom * 100)}%`;
                }
                
                function closeDocumentModal() {
                    const docModal = document.getElementById('documentModal');
                    const docIframe = document.getElementById('modalDocument');
                    
                    docIframe.src = '';
                    docIframe.style.zoom = '';
                    docModal.style.display = 'none';
                    document.removeEventListener('keydown', handleDocumentKeydown);
                }
                
                function closeMediaModal() {
                    const modal = document.getElementById('mediaModal');
                    const modalImage = document.getElementById('modalImage');
                    modal.style.display = 'none';
                    modalImage.src = '';
                }
                
                // 键盘快捷键
                document.addEventListener('keydown', function(event) {
                    const pdfModal = document.getElementById('pdfModal');
                    if (pdfModal.style.display === 'flex') {
                        if (event.key === 'Escape') {
                            closePdfModal();
                        }
                    }
                    
                    const docModal = document.getElementById('documentModal');
                    if (docModal.style.display === 'flex') {
                        if (event.key === 'Escape') {
                            closeDocumentModal();
                        }
                    }
                    
                    const mediaModal = document.getElementById('mediaModal');
                    if (mediaModal.style.display === 'flex') {
                        if (event.key === 'Escape') {
                            closeMediaModal();
                        }
                    }
                    
                    if ((event.ctrlKey || event.metaKey) && event.key === 'f') {
                        event.preventDefault();
                        document.getElementById('searchInput').focus();
                    }
                    
                    if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'F') {
                        event.preventDefault();
                        showPathFilterDialog();
                    }
                    
                    if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'C') {
                        event.preventDefault();
                        clearPathFilter();
                    }
                });
                
                async function showDatabaseInfo(dbId) {
                    try {
                        const response = await fetch('/api/directory/' + dbId);
                        const data = await response.json();
                        
                        if (data.success) {
                            alert('数据库信息:\\n' +
                                'ID: ' + data.directory.id + '\\n' +
                                '名称: ' + data.directory.name + '\\n' +
                                '路径: ' + data.directory.path + '\\n' +
                                '创建时间: ' + data.directory.created_time + '\\n' +
                                '最后修改: ' + data.directory.last_modified + '\\n' +
                                '状态: ' + (data.directory.exists ? '上架' : '下架') + '\\n' +
                                '类型: ' + (data.directory.is_directory ? '目录' : '文件'));
                        } else {
                            alert('获取数据库信息失败: ' + data.error);
                        }
                    } catch (error) {
                        alert('获取数据库信息失败: ' + error.message);
                    }
                }
                
                async function startScan() {
                    try {
                        updateStatus('开始扫描目录...');
                        const response = await fetch('/api/scan', { method: 'POST' });
                        const result = await response.json();
                        
                        if (result.success) {
                            updateStatus('扫描已启动，请稍后刷新');
                            setTimeout(() => loadDirectories(), 3000);
                        } else {
                            updateStatus('扫描失败: ' + (result.error || '未知错误'), 'error');
                        }
                    } catch (error) {
                        updateStatus('扫描失败: ' + error.message, 'error');
                    }
                }
                
                function showSystemInfo() {
                    alert('系统信息:\\n' +
                        '名称: ''' + ProjectInfo.NAME + '''\\n' +
                        '版本: ''' + ProjectInfo.VERSION + '''\\n' +
                        '作者: ''' + ProjectInfo.AUTHOR + '''\\n' +
                        '描述: ''' + ProjectInfo.DESCRIPTION + '''\\n' +
                        '技术支持: ''' + ProjectInfo.URL + '''');
                }
                
                // === 管理面板（主目录管理） ===
                async function showAdminPanel() {
                    const dirs = await fetch('/api/admin/directories').then(r => r.json()).catch(() => ({directories:[]}));
                    let list = dirs.directories.map(d => d.path + ' (深度:' + d.scan_depth + ') [删除]').join('\\n');
                    let msg = '=== 主目录管理 ===\\n\\n' + (list || '(无)') + '\\n\\n输入操作:';
                    let action = prompt(msg + '\\n"add 路径|深度" 或 "del 编号"', '');
                    if (!action) return;
                    
                    if (action.startsWith('add ')) {
                        let parts = action.substring(4).split('|');
                        let body = JSON.stringify({action:'add', path:parts[0].trim(), scan_depth:parseInt(parts[1])||3});
                        let r = await fetch('/api/admin/directories', {method:'POST', body:body});
                        let result = await r.json();
                        alert(result.success ? '已添加! 请刷新并重新扫描' : '失败: ' + result.error);
                    } else if (action.startsWith('del ')) {
                        let idx = parseInt(action.substring(4)) - 1;
                        if (idx >= 0 && idx < dirs.directories.length) {
                            let body = JSON.stringify({action:'delete', id:dirs.directories[idx].id});
                            let r = await fetch('/api/admin/directories', {method:'POST', body:body});
                            alert((await r.json()).success ? '已删除' : '失败');
                        }
                    }
                }
                
                async function updateSystemStatus() {
                    try {
                        const response = await fetch('/api/status');
                        const data = await response.json();
                        
                        const statusInfo = document.getElementById('statusInfo');
                        statusInfo.innerHTML = 
                            '🟢 系统运行中 | ' +
                            '用户: ' + (data.current_user || '未登录') + ' | ' +
                            '扫描模式: ' + data.scan_mode + ' | ' +
                            '版本: ''' + ProjectInfo.VERSION + '''';
                    } catch (error) {
                        console.error('更新状态失败:', error);
                    }
                }
                
                function updateItemCount(count) {
                    document.getElementById('itemCount').textContent = '共 ' + count + ' 个项目';
                }
                
                function updateStatus(message, type = 'info') {
                    const statusInfo = document.getElementById('statusInfo');
                    let filterInfo = '';
                    if (currentPathFilter) {
                        const shortFilter = currentPathFilter.length > 20 ? currentPathFilter.substring(0, 20) + '...' : currentPathFilter;
                        filterInfo = ` | 🔍 过滤: ${shortFilter}`;
                    }
                    statusInfo.textContent = message + filterInfo;
                    statusInfo.style.color = type === 'error' ? '#ff4444' : '#666';
                }
                
                function showLoading() {
                    const container = document.getElementById('directoriesContainer');
                    container.innerHTML = '<div class="loading">正在加载...</div>';
                    updateStatus('正在加载数据...');
                }
                
                function showError(message) {
                    const container = document.getElementById('directoriesContainer');
                    container.innerHTML = '<div class="no-results">❌ ' + message + '</div>';
                }
                
                // 视频播放器相关函数（保持原有功能）
                let currentVideo = null;
                let videoUrl = '';
                let videoFileName = '';
                let lastPreviewTime = -1;
                let videoBufferedInterval = null;
                let seekFeedbackTimer = null;
                
                function updateVideoProgress() {
                    if (!currentVideo) return;
                    const percent = (currentVideo.currentTime / currentVideo.duration) * 100;
                    const fillElem = document.getElementById('videoProgressFill');
                    if (fillElem) fillElem.style.width = percent + '%';
                    
                    const current = formatTime(currentVideo.currentTime);
                    const duration = formatTime(currentVideo.duration);
                    const timeDisplay = document.getElementById('videoTimeDisplay');
                    if (timeDisplay) timeDisplay.innerHTML = current + ' / ' + duration;
                    
                    updateBufferedProgress();
                }
                
                function updateBufferedProgress() {
                    if (!currentVideo || currentVideo.buffered.length === 0) return;
                    const bufferedEnd = currentVideo.buffered.end(currentVideo.buffered.length - 1);
                    const percent = (bufferedEnd / currentVideo.duration) * 100;
                    const bufferedFill = document.getElementById('videoBufferedFill');
                    if (bufferedFill) bufferedFill.style.width = percent + '%';
                }
                
                function formatTime(seconds) {
                    if (isNaN(seconds) || !isFinite(seconds)) return '00:00';
                    const hrs = Math.floor(seconds / 3600);
                    const mins = Math.floor((seconds % 3600) / 60);
                    const secs = Math.floor(seconds % 60);
                    if (hrs > 0) {
                        return hrs.toString().padStart(2, '0') + ':' + mins.toString().padStart(2, '0') + ':' + secs.toString().padStart(2, '0');
                    }
                    return mins.toString().padStart(2, '0') + ':' + secs.toString().padStart(2, '0');
                }
                
                function onVideoLoaded() {
                    if (!currentVideo) return;
                    updateVideoProgress();
                    if (videoBufferedInterval) clearInterval(videoBufferedInterval);
                    videoBufferedInterval = setInterval(updateBufferedProgress, 500);
                }
                
                function seekVideo(event) {
                    if (!currentVideo) return;
                    const rect = event.currentTarget.getBoundingClientRect();
                    const x = event.clientX - rect.left;
                    const percent = Math.max(0, Math.min(1, x / rect.width));
                    currentVideo.currentTime = percent * currentVideo.duration;
                }
                
                async function showPreview(event) {
                    if (!currentVideo || !currentVideo.duration) return;
                    const rect = event.currentTarget.getBoundingClientRect();
                    const x = event.clientX - rect.left;
                    const percent = Math.max(0, Math.min(1, x / rect.width));
                    const previewTime = percent * currentVideo.duration;
                    
                    const indicator = document.getElementById('previewIndicator');
                    const indicatorTime = document.getElementById('previewIndicatorTime');
                    if (indicator && indicatorTime) {
                        indicator.style.left = x + 'px';
                        indicator.style.display = 'block';
                        indicatorTime.textContent = formatTime(previewTime);
                    }
                    
                    const overlay = document.getElementById('previewOverlay');
                    const previewImage = document.getElementById('previewImage');
                    const previewTimeLabel = document.getElementById('previewTime');
                    
                    if (overlay && previewImage) {
                        let leftPos = x - 80;
                        leftPos = Math.max(10, Math.min(rect.width - 170, leftPos));
                        overlay.style.left = leftPos + 'px';
                        overlay.style.display = 'block';
                        if (previewTimeLabel) previewTimeLabel.textContent = formatTime(previewTime);
                    }
                    
                    if (Math.abs(previewTime - lastPreviewTime) > 0.5) {
                        lastPreviewTime = previewTime;
                        try {
                            const thumbnail = await captureVideoFrame(previewTime);
                            if (thumbnail && previewImage) previewImage.src = thumbnail;
                        } catch(e) {}
                    }
                }
                
                async function captureVideoFrame(time) {
                    return new Promise((resolve) => {
                        if (!currentVideo || !currentVideo.src) {
                            resolve(null);
                            return;
                        }
                        const video = document.createElement('video');
                        video.crossOrigin = 'anonymous';
                        video.preload = 'metadata';
                        video.src = currentVideo.src;
                        video.addEventListener('loadedmetadata', () => {
                            video.currentTime = Math.min(time, video.duration - 0.1);
                        });
                        video.addEventListener('seeked', () => {
                            const canvas = document.createElement('canvas');
                            canvas.width = 320;
                            canvas.height = 180;
                            const ctx = canvas.getContext('2d');
                            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                            resolve(canvas.toDataURL('image/jpeg', 0.7));
                            video.src = '';
                            video.load();
                        });
                        video.addEventListener('error', () => resolve(null));
                        video.load();
                        setTimeout(() => {
                            if (video.src) {
                                video.src = '';
                                resolve(null);
                            }
                        }, 3000);
                    });
                }
                
                function hidePreview() {
                    const indicator = document.getElementById('previewIndicator');
                    const overlay = document.getElementById('previewOverlay');
                    if (indicator) indicator.style.display = 'none';
                    if (overlay) overlay.style.display = 'none';
                    lastPreviewTime = -1;
                }
                
                function seekBackward(seconds) {
                    if (!currentVideo) return;
                    currentVideo.currentTime = Math.max(0, currentVideo.currentTime - seconds);
                    showSeekFeedback('后退 ' + seconds + ' 秒');
                }
                
                function seekForward(seconds) {
                    if (!currentVideo) return;
                    currentVideo.currentTime = Math.min(currentVideo.duration, currentVideo.currentTime + seconds);
                    showSeekFeedback('前进 ' + seconds + ' 秒');
                }
                
                function showSeekFeedback(message) {
                    let feedback = document.getElementById('seekFeedback');
                    if (!feedback) {
                        feedback = document.createElement('div');
                        feedback.id = 'seekFeedback';
                        feedback.style.cssText = 'position: fixed; bottom: 30%; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.8); color: white; padding: 8px 16px; border-radius: 20px; font-size: 14px; z-index: 1001; pointer-events: none;';
                        document.body.appendChild(feedback);
                    }
                    feedback.textContent = message;
                    feedback.style.display = 'block';
                    if (seekFeedbackTimer) clearTimeout(seekFeedbackTimer);
                    seekFeedbackTimer = setTimeout(() => {
                        if (feedback) feedback.style.display = 'none';
                    }, 800);
                }
                
                function togglePlayPause() {
                    if (!currentVideo) return;
                    const btn = document.getElementById('playPauseBtn');
                    if (currentVideo.paused) {
                        currentVideo.play();
                        if (btn) btn.innerHTML = '⏸';
                    } else {
                        currentVideo.pause();
                        if (btn) btn.innerHTML = '▶';
                    }
                }
                
                function changePlaybackRate(rate) {
                    if (!currentVideo) return;
                    currentVideo.playbackRate = rate;
                    showSeekFeedback(rate + 'x 播放速度');
                    const btns = document.querySelectorAll('.control-btn');
                    btns.forEach(btn => {
                        if (btn.textContent === rate + 'x') {
                            btn.style.background = '#e74c3c';
                        } else if (btn.textContent && btn.textContent.match(/^\d+(\.\d+)?x$/)) {
                            btn.style.background = 'rgba(255,255,255,0.1)';
                        }
                    });
                }
                
                function toggleFullscreen() {
                    const modalContent = document.querySelector('#videoModal .modal-content');
                    if (!modalContent) return;
                    if (!document.fullscreenElement) {
                        modalContent.requestFullscreen().catch(function(err) {
                            console.log('全屏错误: ' + err.message);
                        });
                    } else {
                        document.exitFullscreen();
                    }
                }
                
                function downloadVideo() {
                    if (!videoUrl) return;
                    const link = document.createElement('a');
                    link.href = videoUrl;
                    link.download = videoFileName;
                    link.click();
                    showSeekFeedback('开始下载视频...');
                }
                
                function playVideo(videoPath, fileName) {
                    videoFileName = fileName || decodeURIComponent(videoPath).split('/').pop();
                    videoUrl = '/api/video?path=' + encodeURIComponent(videoPath);
                    
                    const titleElem = document.getElementById('videoTitle');
                    if (titleElem) titleElem.innerHTML = '🎬 ' + videoFileName;
                    
                    const videoModal = document.getElementById('videoModal');
                    const videoElement = document.getElementById('modalVideo');
                    
                    if (videoElement) {
                        videoElement.src = videoUrl;
                        videoElement.load();
                    }
                    currentVideo = videoElement;
                    
                    if (videoModal) videoModal.style.display = 'flex';
                    
                    const playBtn = document.getElementById('playPauseBtn');
                    if (playBtn) playBtn.innerHTML = '⏸';
                    
                    if (videoElement) {
                        videoElement.play().catch(function(error) {
                            console.log('自动播放被阻止:', error);
                            if (playBtn) playBtn.innerHTML = '▶';
                        });
                    }
                    
                    document.addEventListener('keydown', handleVideoKeydown);
                }
                
                function handleVideoKeydown(event) {
                    const videoModal = document.getElementById('videoModal');
                    if (!videoModal || videoModal.style.display !== 'flex') return;
                    switch(event.key) {
                        case 'ArrowLeft':
                            event.preventDefault();
                            seekBackward(5);
                            break;
                        case 'ArrowRight':
                            event.preventDefault();
                            seekForward(5);
                            break;
                        case 'ArrowUp':
                            event.preventDefault();
                            var newRate = Math.min(2, (currentVideo ? currentVideo.playbackRate : 1) + 0.25);
                            changePlaybackRate(newRate);
                            break;
                        case 'ArrowDown':
                            event.preventDefault();
                            var newRate = Math.max(0.5, (currentVideo ? currentVideo.playbackRate : 1) - 0.25);
                            changePlaybackRate(newRate);
                            break;
                        case ' ':
                        case 'Space':
                            event.preventDefault();
                            togglePlayPause();
                            break;
                        case 'f':
                        case 'F':
                            event.preventDefault();
                            toggleFullscreen();
                            break;
                        case 'Escape':
                            closeVideoModal();
                            break;
                    }
                }
                
                function closeVideoModal() {
                    const videoModal = document.getElementById('videoModal');
                    if (currentVideo) {
                        currentVideo.pause();
                        currentVideo.src = '';
                        currentVideo = null;
                    }
                    if (videoBufferedInterval) {
                        clearInterval(videoBufferedInterval);
                        videoBufferedInterval = null;
                    }
                    if (videoModal) videoModal.style.display = 'none';
                    document.removeEventListener('keydown', handleVideoKeydown);
                }
                
                function onVideoSeeked() {
                    var current = currentVideo ? currentVideo.currentTime : 0;
                    showSeekFeedback('跳转到 ' + formatTime(current));
                }
                
                // 触摸滑动支持
                var touchStartX = 0;
                var touchStartTime = 0;
                
                function initTouchSwipe() {
                    var videoContainer = document.querySelector('#videoModal .modal-content');
                    if (!videoContainer) return;
                    videoContainer.addEventListener('touchstart', function(e) {
                        touchStartX = e.touches[0].clientX;
                        touchStartTime = Date.now();
                    });
                    videoContainer.addEventListener('touchend', function(e) {
                        var touchEndX = e.changedTouches[0].clientX;
                        var deltaX = touchEndX - touchStartX;
                        var deltaTime = Date.now() - touchStartTime;
                        if (deltaTime < 300 && Math.abs(deltaX) > 50) {
                            if (deltaX > 0) {
                                var seconds = Math.min(30, Math.floor(Math.abs(deltaX) / 10));
                                seekBackward(seconds);
                                showSeekFeedback('← 后退 ' + seconds + ' 秒');
                            } else {
                                var seconds = Math.min(30, Math.floor(Math.abs(deltaX) / 10));
                                seekForward(seconds);
                                showSeekFeedback('→ 前进 ' + seconds + ' 秒');
                            }
                        }
                    });
                }
                
                // 触摸屏进度条预览支持
                var progressBar = null;
                var isTouchingProgress = false;
                var touchPreviewTimer = null;
                var lastTouchPreviewTime = -1;
                var lastTouchClientX = 0;
                
                function updatePreviewFromTouch(clientX) {
                    if (!currentVideo || !currentVideo.duration) return;
                    if (!progressBar) return;
                    
                    var rect = progressBar.getBoundingClientRect();
                    var x = clientX - rect.left;
                    var percent = Math.max(0, Math.min(1, x / rect.width));
                    var previewTime = percent * currentVideo.duration;
                    
                    var indicator = document.getElementById('previewIndicator');
                    var indicatorTime = document.getElementById('previewIndicatorTime');
                    if (indicator && indicatorTime) {
                        indicator.style.left = x + 'px';
                        indicator.style.display = 'block';
                        indicatorTime.textContent = formatTime(previewTime);
                    }
                    
                    var overlay = document.getElementById('previewOverlay');
                    var previewImage = document.getElementById('previewImage');
                    var previewTimeLabel = document.getElementById('previewTime');
                    
                    if (overlay && previewImage) {
                        var leftPos = x - 80;
                        leftPos = Math.max(10, Math.min(rect.width - 170, leftPos));
                        overlay.style.left = leftPos + 'px';
                        overlay.style.display = 'block';
                        if (previewTimeLabel) previewTimeLabel.textContent = formatTime(previewTime);
                    }
                    
                    if (Math.abs(previewTime - lastTouchPreviewTime) > 0.5) {
                        lastTouchPreviewTime = previewTime;
                        captureVideoFrame(previewTime).then(function(thumbnail) {
                            if (thumbnail && previewImage) previewImage.src = thumbnail;
                        });
                    }
                    
                    return previewTime;
                }
                
                function onProgressTouchStart(event) {
                    event.preventDefault();
                    event.stopPropagation();
                    isTouchingProgress = true;
                    
                    if (!progressBar || !currentVideo) return;
                    
                    var touch = event.touches[0];
                    if (!touch) return;
                    
                    updatePreviewFromTouch(touch.clientX);
                    
                    if (touchPreviewTimer) clearInterval(touchPreviewTimer);
                }
                
                function onProgressTouchMove(event) {
                    event.preventDefault();
                    event.stopPropagation();
                    if (!currentVideo || !progressBar) return;
                    
                    var touch = event.touches[0];
                    if (!touch) return;
                    
                    lastTouchClientX = touch.clientX;
                    updatePreviewFromTouch(touch.clientX);
                }
                
                function onProgressTouchEnd(event) {
                    event.preventDefault();
                    event.stopPropagation();
                    isTouchingProgress = false;
                    
                    if (touchPreviewTimer) clearInterval(touchPreviewTimer);
                    if (!currentVideo || !progressBar) return;
                    
                    var rect = progressBar.getBoundingClientRect();
                    var touch = event.changedTouches[0];
                    if (!touch) return;
                    
                    var x = touch.clientX - rect.left;
                    var percent = Math.max(0, Math.min(1, x / rect.width));
                    var seekTime = percent * currentVideo.duration;
                    
                    if (isFinite(seekTime) && seekTime >= 0 && seekTime <= currentVideo.duration) {
                        currentVideo.currentTime = seekTime;
                        showSeekFeedback('跳转到 ' + formatTime(seekTime));
                    }
                    
                    setTimeout(function() {
                        if (!isTouchingProgress) {
                            hidePreview();
                        }
                    }, 100);
                }
                
                function onProgressTouchCancel(event) {
                    isTouchingProgress = false;
                    if (touchPreviewTimer) clearInterval(touchPreviewTimer);
                    hidePreview();
                }
                
                function bindProgressTouchEvents() {
                    if (!progressBar) {
                        progressBar = document.querySelector('.progress-bar-wrapper');
                    }
                    if (!progressBar) {
                        setTimeout(bindProgressTouchEvents, 200);
                        return;
                    }
                    progressBar.addEventListener('touchstart', onProgressTouchStart, { passive: false });
                    progressBar.addEventListener('touchmove', onProgressTouchMove, { passive: false });
                    progressBar.addEventListener('touchend', onProgressTouchEnd);
                    progressBar.addEventListener('touchcancel', onProgressTouchCancel);
                }
                
                var originalInitTouchSwipe = initTouchSwipe;
                window.initTouchSwipe = function() {
                    if (originalInitTouchSwipe) originalInitTouchSwipe();
                    bindProgressTouchEvents();
                };
                
                document.addEventListener('DOMContentLoaded', function() {
                    initTouchSwipe();
                    
                    setTimeout(function() {
                        var hint = document.getElementById('touchHint');
                        if (hint) {
                            hint.style.display = 'block';
                            setTimeout(function() {
                                hint.style.opacity = '0';
                                setTimeout(function() {
                                    hint.style.display = 'none';
                                }, 1000);
                            }, 3000);
                        }
                    }, 1000);
                    
                    var touchInstructions = document.createElement('div');
                    touchInstructions.id = 'touchInstructions';
                    touchInstructions.style.cssText = 'position: fixed; bottom: 80px; left: 10px; right: 10px; background: rgba(0,0,0,0.8); color: white; padding: 10px 15px; border-radius: 25px; font-size: 13px; text-align: center; z-index: 999; pointer-events: none; opacity: 0; transition: opacity 0.5s; font-family: sans-serif;';
                    touchInstructions.innerHTML = '👆 触摸进度条可预览画面 | ◀ ▶ 左右滑动快进/快退';
                    document.body.appendChild(touchInstructions);
                    
                    setTimeout(function() {
                        touchInstructions.style.opacity = '0.9';
                        setTimeout(function() {
                            touchInstructions.style.opacity = '0';
                            setTimeout(function() {
                                if (touchInstructions && touchInstructions.remove) touchInstructions.remove();
                            }, 3000);
                        }, 4000);
                    }, 1500);
                });
                
                var touchHintStyle = document.createElement('style');
                touchHintStyle.textContent = '#touchHint { transition: opacity 0.5s; }';
                document.head.appendChild(touchHintStyle);
            </script>
        </body>
        </html>
        '''


    def get_directories_data(self):
        """获取目录数据 - 线程安全版本"""
        if not self.main_app or not self.main_app.user_manager.current_db_path:
            return {"directories": [], "count": 0}
        
        try:
            # 使用锁保护数据库访问
            with self.lock:
                conn = sqlite3.connect(self.main_app.user_manager.current_db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, name, path, directory_exists, created_time, last_modified, is_directory 
                    FROM directories 
                    ORDER BY name
                """)
                
                directories = []
                results = cursor.fetchall()
                
                for row in results:
                    try:
                        if len(row) == 7:
                            db_id, name, path, exists, created_time, last_modified, is_directory = row
                            
                            directories.append({
                                "id": db_id,
                                "name": name,
                                "path": path,
                                "exists": bool(exists),
                                "created_time": created_time,
                                "last_modified": last_modified,
                                "is_directory": bool(is_directory)
                            })
                    except Exception as e:
                        print(f"[ERROR] 处理数据库行时出错: {e}, 行数据: {row}")
                        continue
                
                conn.close()
                return {"directories": directories, "count": len(directories)}
                
        except Exception as e:
            print(f"[SERVER ERROR] 获取目录数据失败: {e}")
            return {"directories": [], "count": 0, "error": str(e)}

        
    def handle_search_request(self, query_string):
        """处理搜索请求 - 支持类型过滤和排序"""
        query_params = urllib.parse.parse_qs(query_string)
        search_term = query_params.get('q', [''])[0].lower()
        filter_type = query_params.get('type', ['all'])[0].lower()
        sort_by = query_params.get('sort', ['name'])[0].lower()
        
        # 如果没有搜索词，直接返回过滤和排序后的数据
        if not search_term:
            data = self.get_directories_data(filter_type, sort_by)
            self.send_json_response(data)
            return
        
        # 如果有搜索词，先获取所有数据然后过滤
        data = self.get_directories_data("all", sort_by)  # 先不应用类型过滤
        directories = data["directories"]
        
        # 过滤匹配的目录
        filtered_directories = []
        for dir_info in directories:
            name = dir_info["name"].lower()
            path = dir_info["path"].lower()
            
            # 应用类型过滤
            if filter_type != "all":
                is_directory = dir_info["is_directory"]
                if filter_type == "directory" and not is_directory:
                    continue
                elif filter_type == "file" and is_directory:
                    continue
                elif filter_type == "video" and not self.is_video_file(dir_info["name"]):
                    continue
                elif filter_type == "image" and not self.is_image_file(dir_info["name"]):
                    continue
                elif filter_type == "pdf" and not self.is_pdf_file(dir_info["name"]):
                    continue
                elif filter_type == "document" and not self.is_document_file(dir_info["name"]):
                    continue
            
            # 普通文本匹配
            if search_term in name or search_term in path:
                filtered_directories.append(dir_info)
                continue
            
            # 拼音首字母匹配
            if PinyinSearchHelper.contains_pinyin_initials(dir_info["name"], search_term):
                filtered_directories.append(dir_info)
        
        self.send_json_response({
            "directories": filtered_directories,
            "count": len(filtered_directories),
            "search_term": search_term,
            "filter_type": filter_type,
            "sort_by": sort_by
        })

    
    def handle_cover_request(self, query_string):
        """处理封面图片请求"""
        query_params = urllib.parse.parse_qs(query_string)
        path = query_params.get('path', [''])[0]
        
        if not path:
            self.send_error(HTTPStatus.BAD_REQUEST, "Missing path parameter")
            return
        
        try:
            directory_path = urllib.parse.unquote(path)

            # === 新增：路径规范化 ===
            if self.main_app and hasattr(self.main_app, 'normalize_path_separators'):
                directory_path = self.main_app.normalize_path_separators(directory_path)

            # 查找封面图片
            cover_path = self.main_app.find_cover_image(directory_path) if self.main_app else None
            
            if cover_path and os.path.exists(cover_path):
                # 发送图片文件
                self.send_file_response(cover_path, 'image/jpeg')
            else:
                # 返回默认图片
                self.send_default_cover()
                
        except Exception as e:
            print(f"[SERVER ERROR] 获取封面失败: {e}")
            self.send_default_cover()
    
    def handle_open_request(self, query_string):
        """处理打开目录请求 - 强制使用数据库路径"""
        query_params = urllib.parse.parse_qs(query_string)
        path = query_params.get('path', [''])[0]
        print(f"[DEBUG] Received open GET path: {path}")

        if not path:
            self.send_error(HTTPStatus.BAD_REQUEST, "Missing path parameter")
            return
        
        try:
            directory_path = urllib.parse.unquote(path)
        
            # === 新增：路径规范化处理 ===
            # 修复反斜杠转义问题
            normalized_path = directory_path.replace('\\', '/')
            print(f"[DEBUG] After normalization: {normalized_path}")
            
            # 如果规范化后的路径与原始路径不同，使用规范化路径
            if normalized_path != directory_path:
                directory_path = normalized_path
                print(f"[DEBUG] Using normalized path: {directory_path}")
            
            # === 新增：强制使用数据库路径查询 ===
            db_path = None
            if self.main_app and hasattr(self.main_app, 'user_manager') and self.main_app.user_manager.current_db_path:
                try:
                    conn = sqlite3.connect(self.main_app.user_manager.current_db_path)
                    cursor = conn.cursor()
                    
                    basename = os.path.basename(directory_path)
                    
                    # 多种策略查询数据库路径
                    cursor.execute("SELECT path FROM directories WHERE name = ? OR path LIKE ?", 
                                (basename, f"%{basename}%"))
                    results = cursor.fetchall()
                    conn.close()
                    
                    if results:
                        # 优先精确匹配
                        for result in results:
                            candidate_path = result[0]
                            if candidate_path.endswith(basename):
                                db_path = candidate_path
                                break
                        
                        if not db_path and results:
                            db_path = results[0][0]
                    
                except Exception as e:
                    print(f"[DATABASE ERROR] 查询数据库路径失败: {e}")
            
            # === 修改：必须使用数据库路径 ===
            if not db_path:
                self.send_json_response({
                    "success": False,
                    "error": f"在数据库中找不到对应的路径: {directory_path}",
                    "original_get_path": directory_path
                })
                return
            
            final_path = db_path
            print(f"[DEBUG] GET请求最终使用的数据库路径: {final_path}")
            
            # 使用线程安全的方式调用
            success = False
            error_msg = ""
            
            if self.main_app and hasattr(self.main_app, 'open_directory'):
                # 使用信号槽机制确保在主线程中执行
                # PySide6中使用QMetaObject.invokeMethod
                QMetaObject.invokeMethod(
                    self.main_app, 
                    "open_directory", 
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, final_path)
                )
                success = True
            else:
                error_msg = "没有可用的打开目录方法"
            
            self.send_json_response({
                "success": success,
                "path": final_path,
                "database_path_used": True,
                "original_get_path": directory_path,
                "error": error_msg if not success else None
            })
            
        except Exception as e:
            print(f"[SERVER ERROR] 打开目录失败: {e}")
            self.send_json_response({
                "success": False,
                "path": path,
                "database_path_used": False,
                "error": str(e)
            })



    def handle_open_post(self, data):
        """处理POST打开目录请求 - 支持数据库ID"""
        print(f"[DEBUG] Received open POST data: {data}")
        
        path = data.get('path', '')
        db_id = data.get('db_id')  # 新增：获取数据库ID
        
        print(f"[DEBUG] Extracted path: {path}, DB ID: {db_id}")

        if not path and not db_id:
            self.send_error(HTTPStatus.BAD_REQUEST, "Missing path or db_id parameter")
            return

        try:
            # 如果提供了数据库ID，优先使用数据库ID查询路径
            if db_id:
                db_path = self.get_path_by_id(db_id)
                if db_path:
                    path = db_path
                    print(f"[DEBUG] 使用数据库ID {db_id} 查询到的路径: {path}")
                else:
                    self.send_json_response({
                        "success": False,
                        "error": f"在数据库中找不到ID为 {db_id} 的目录",
                        "db_id": db_id
                    })
                    return
        except Exception as e:
            print(f"[ERROR] 通过数据库ID查询路径失败: {e}")
            # 如果通过ID查询失败，继续使用原始路径

        try:
            print(f"[DEBUG] Original path: {path}")
    
            # === 新增：路径解析修复 ===
            # 检查路径是否缺少分隔符（如 BBAPNS-076 应该是 BB/APNS-076）
            if '//' in path and not path.replace('//', '/').count('/') >= 4:
                # 尝试从数据库查找正确的路径结构
                corrected_path = self.attempt_path_correction(path)
                if corrected_path and corrected_path != path:
                    print(f"[PATH CORRECTION] 路径已修正: {path} -> {corrected_path}")
                    path = corrected_path
        
            # === 新增：使用专门的修复方法 ===
            path = self.fix_missing_separator(path)
            
            # === 原有的路径规范化处理 ===
            # 修复反斜杠转义问题
            normalized_path = path.replace('\\', '/')
            print(f"[DEBUG] After normalization: {normalized_path}")
            
            # 如果规范化后的路径与原始路径不同，使用规范化路径
            if normalized_path != path:
                path = normalized_path
                print(f"[DEBUG] Using normalized path: {path}")
            
            # === 修改：强制使用数据库路径，如果找不到就报错 ===
            db_path = None
            if self.main_app and hasattr(self.main_app, 'user_manager') and self.main_app.user_manager.current_db_path:
                print(f"[DATABASE PATH] 查询数据库路径 for: {path}")
                try:
                    conn = sqlite3.connect(self.main_app.user_manager.current_db_path)
                    cursor = conn.cursor()
                    
                    # 多种策略查询数据库中的路径
                    basename = os.path.basename(path)
                    print(f"[DATABASE PATH] 查询目录名称: {basename}")
                    
                    # 策略1: 精确匹配路径
                    cursor.execute("SELECT path FROM directories WHERE path = ?", (path,))
                    results = cursor.fetchall()
                    
                    # 策略2: 精确匹配名称
                    if not results:
                        cursor.execute("SELECT path FROM directories WHERE name = ?", (basename,))
                        results = cursor.fetchall()
                        print(f"[DATABASE PATH] 名称匹配结果数: {len(results)}")
                    
                    # 策略3: 路径包含匹配
                    if not results:
                        cursor.execute("SELECT path FROM directories WHERE path LIKE ?", (f"%{basename}%",))
                        results = cursor.fetchall()
                        print(f"[DATABASE PATH] 路径包含匹配结果数: {len(results)}")
                    
                    # 策略4: 路径结尾匹配
                    if not results:
                        cursor.execute("SELECT path FROM directories WHERE path LIKE ?", (f"%{basename}",))
                        results = cursor.fetchall()
                        print(f"[DATABASE PATH] 路径结尾匹配结果数: {len(results)}")
                    
                    conn.close()
                    
                    if results:
                        # 优先选择路径最匹配的结果
                        for result in results:
                            candidate_path = result[0]
                            if candidate_path.endswith(basename):
                                db_path = candidate_path
                                print(f"[DATABASE PATH] 找到精确匹配的数据库路径: {db_path}")
                                break
                        
                        # 如果没有精确匹配，使用第一个结果
                        if not db_path and results:
                            db_path = results[0][0]
                            print(f"[DATABASE PATH] 使用第一个数据库路径: {db_path}")



                except Exception as e:
                    print(f"[DATABASE ERROR] 查询数据库路径失败: {e}")
                    self.send_json_response({
                        "success": False,
                        "error": f"数据库查询失败: {str(e)}",
                        "original_post_path": path
                    })
                    return
            
            # === 修改：必须使用数据库路径，如果找不到就报错 ===
            if not db_path:
                print(f"[DATABASE ERROR] 在数据库中找不到对应的路径: {path}")
                self.send_json_response({
                    "success": False,
                    "error": f"在数据库中找不到对应的路径: {path}",
                    "original_post_path": path,
                    "suggestion": "请确保该目录已被扫描并保存到数据库"
                })
                return
            
            final_path = db_path
            print(f"[DEBUG] 最终使用的数据库路径: {final_path}")
            
            # 路径规范化
            print(f"[DEBUG] Path before normalization: {final_path}")
            if hasattr(self.main_app, 'normalize_path_separators'):
                final_path = self.main_app.normalize_path_separators(final_path)
                print(f"[DEBUG] Path after normalization: {final_path}")

            # 使用线程安全的方式调用主应用程序的打开目录方法
            success = False
            error_msg = ""
            
            if self.main_app:
                # 使用Qt的信号槽机制确保在主线程中执行
                if hasattr(self.main_app, 'open_directory'):
                    # 使用invokeMethod确保在主线程中执行
                    QMetaObject.invokeMethod(
                        self.main_app, 
                        "open_directory", 
                        Qt.ConnectionType.QueuedConnection,  # 使用队列连接确保线程安全
                        Q_ARG(str, final_path)
                    )
                    success = True
                else:
                    error_msg = "主应用程序没有打开目录方法"
            else:
                error_msg = "主应用程序不可用"
            
            self.send_json_response({
                "success": success,
                "path": final_path,
                "db_id": db_id,  # 新增：返回数据库ID
                "database_path_used": True,
                "original_post_path": path,
                "error": error_msg if not success else None
            })
            
        except Exception as e:
            print(f"[SERVER ERROR] 打开目录失败: {e}")
            self.send_json_response({
                "success": False,
                "error": str(e),
                "db_id": db_id,
                "original_post_path": path,
                "database_path_used": False
            })

    def get_path_by_id(self, db_id):
        """根据数据库ID获取路径"""
        if not self.main_app or not self.main_app.user_manager.current_db_path:
            return None
        
        try:
            conn = sqlite3.connect(self.main_app.user_manager.current_db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT path FROM directories WHERE id = ?", (db_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0]
            return None
            
        except Exception as e:
            print(f"[DATABASE ERROR] 根据ID查询路径失败: {e}")
            return None

    def fix_missing_separator(self, path):
        """修复路径中缺少的分隔符"""
        if not path or '//' not in path:
            return path
        
        # 将双斜杠替换为单斜杠
        normalized = path.replace('//', '/')
        
        # 分析路径结构
        parts = [part for part in normalized.split('/') if part]
        if len(parts) < 4:
            return normalized
        
        # 检查最后一部分是否包含父目录名称
        last_part = parts[-1]
        parent_part = parts[-2]
        
        # 如果最后一部分以父目录名称开头且长度更长，说明缺少分隔符
        if (last_part.startswith(parent_part) and 
            len(last_part) > len(parent_part) and
            not last_part[len(parent_part):].startswith('/')):
            
            # 在父目录名称后插入分隔符
            fixed_last = parent_part + '/' + last_part[len(parent_part):]
            parts[-2:] = [parent_part, last_part[len(parent_part):]]
            
            fixed_path = '/' + '/'.join(parts)
            print(f"[SEPARATOR FIX] 修复路径分隔符: {normalized} -> {fixed_path}")
            return fixed_path
        
        return normalized



    def attempt_path_correction(self, problematic_path):
        """尝试修正路径分隔符问题"""
        if not self.main_app or not self.main_app.user_manager.current_db_path:
            return problematic_path
        
        try:
            conn = sqlite3.connect(self.main_app.user_manager.current_db_path)
            cursor = conn.cursor()
            
            # 获取路径的基本名称部分
            basename = os.path.basename(problematic_path)
            print(f"[PATH CORRECTION] 尝试修正路径: {problematic_path}, 基本名称: {basename}")
            
            # 策略1: 在数据库中查找包含这个基本名称的路径
            cursor.execute("SELECT path FROM directories WHERE path LIKE ?", (f"%{basename}%",))
            results = cursor.fetchall()
            
            if results:
                # 找到多个可能路径时，选择最匹配的一个
                for db_path, in results:
                    # 检查数据库路径是否包含正确的目录结构
                    db_basename = os.path.basename(db_path)
                    if db_basename == basename:
                        # 完全匹配，直接返回
                        print(f"[PATH CORRECTION] 找到完全匹配: {db_path}")
                        return db_path
                    
                    # 检查是否是子目录关系
                    parent_dir = os.path.dirname(db_path)
                    parent_basename = os.path.basename(parent_dir)
                    
                    # 如果问题路径像是缺少了分隔符（如 BBAPNS-076 应该是 BB/APNS-076）
                    if parent_basename and basename.startswith(parent_basename):
                        # 提取子目录名称
                        subdir_name = basename[len(parent_basename):]
                        if subdir_name and not subdir_name.startswith('/'):
                            # 构建正确的路径
                            corrected = os.path.join(parent_dir, subdir_name)
                            print(f"[PATH CORRECTION] 推测正确路径: {corrected}")
                            
                            # 验证这个路径是否在数据库中
                            cursor.execute("SELECT path FROM directories WHERE path = ?", (corrected,))
                            if cursor.fetchone():
                                return corrected
            
            conn.close()
            
        except Exception as e:
            print(f"[PATH CORRECTION ERROR] 路径修正失败: {e}")
        
        return problematic_path



    
    def handle_scan_request(self):
        """处理扫描请求"""
        try:
            success = False
            error_msg = ""
            
            if self.main_app:
                # === 修复：使用信号槽机制在主线程中执行扫描 ===
                def run_scan_in_main_thread():
                    try:
                        # 确保在主线程中执行
                        if hasattr(self.main_app, 'scan_directories'):
                            # 使用单次定时器确保在主线程事件循环中执行
                            QTimer.singleShot(0, self.main_app.scan_directories)
                    except Exception as e:
                        print(f"[SERVER ERROR] 扫描失败: {e}")
                
                # 如果已经在主线程，直接调用
                if QThread.currentThread() == self.main_app.thread():
                    self.main_app.scan_directories()
                    success = True
                else:
                    # 否则使用信号槽机制
                    QTimer.singleShot(0, self.main_app.scan_directories)
                    success = True
            else:
                error_msg = "Main application not available"
            
            self.send_json_response({
                "success": success,
                "message": "扫描已开始" if success else error_msg,
                "error": error_msg if not success else None
            })
            
        except Exception as e:
            self.send_json_response({
                "success": False,
                "error": str(e)
            })
    
    def handle_admin_directories_get(self):
        """获取主目录列表"""
        if not self.main_app or not self.main_app.user_manager.current_db_path:
            self.send_json_response({"directories": []})
            return
        try:
            conn = sqlite3.connect(self.main_app.user_manager.current_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, path, name, scan_depth FROM main_directories ORDER BY id")
            dirs = [{"id": r[0], "path": r[1], "name": r[2], "scan_depth": r[3]} for r in cursor.fetchall()]
            conn.close()
            self.send_json_response({"directories": dirs})
        except Exception as e:
            self.send_json_response({"error": str(e)})
    
    def handle_admin_directories_post(self, data):
        """管理主目录（添加/删除）"""
        action = data.get('action', '')
        if not self.main_app or not self.main_app.user_manager.current_db_path:
            self.send_json_response({"success": False, "error": "未登录"})
            return
        try:
            conn = sqlite3.connect(self.main_app.user_manager.current_db_path)
            cursor = conn.cursor()
            if action == 'add':
                path = data.get('path', '').strip()
                name = data.get('name', '').strip() or os.path.basename(path)
                depth = int(data.get('scan_depth', 3))
                if not path:
                    self.send_json_response({"success": False, "error": "路径不能为空"})
                    return
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("INSERT INTO main_directories (path, name, scan_depth, created_time) VALUES (?,?,?,?)",
                              (path, name, depth, now))
                conn.commit()
                self.send_json_response({"success": True, "message": f"已添加: {name}"})
            elif action == 'delete':
                dir_id = data.get('id')
                cursor.execute("DELETE FROM main_directories WHERE id = ?", (dir_id,))
                conn.commit()
                self.send_json_response({"success": True, "message": "已删除"})
            else:
                self.send_json_response({"success": False, "error": "未知操作"})
            conn.close()
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)})

    
    def get_system_status(self):
        """获取系统状态"""
        status = {
            "version": ProjectInfo.VERSION,
            "name": ProjectInfo.NAME,
            "status": "running",
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        if self.main_app:
            status.update({
                "current_user": self.main_app.user_manager.current_user,
                "scan_mode": self.main_app.get_setting('scan_mode', 'directories'),
                "auto_scan": self.main_app.get_setting('auto_scan', '1') == '1'
            })
        
        return status
    
    def send_html_response(self, html_content):
        """发送HTML响应"""
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html_content.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def send_json_response(self, data):
        """发送JSON响应"""
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(json_data.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))
    
    def send_file_response(self, file_path, content_type):
        """发送文件响应"""
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', content_type)
            self.send_header('Content-Length', str(len(file_data)))
            self.end_headers()
            self.wfile.write(file_data)
            
        except Exception as e:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))
    
    def send_default_cover(self):
        """发送默认封面图片"""
        # 创建一个简单的SVG作为默认封面
        svg_content = '''
        <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
            <rect width="200" height="200" fill="#f8f9fa"/>
            <text x="100" y="100" font-family="Arial" font-size="14" fill="#6c757d" 
                text-anchor="middle" dy="0.35em">📁 无封面图片</text>
        </svg>
        '''
        
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'image/svg+xml')
        self.send_header('Content-Length', str(len(svg_content)))
        self.end_headers()
        self.wfile.write(svg_content.encode('utf-8'))
    
    def log_message(self, format, *args):
        """重写日志消息格式，过滤掉连接重置的噪音"""
        message = format % args
        # 过滤掉连接重置的日志噪音
        if "10054" in message or "远程主机强迫关闭" in message:
            print(f"[HTTP INFO] 客户端断开连接 (正常行为)")
        else:
            pass
            # print(f"[HTTP SERVER] {message}")



    def handle_pdf_request(self, query_string):
        """处理PDF文件请求 - 多线程安全版本

        【性能优化】移除整段 `with self.lock:`：该锁是每处理器实例自己的锁，
        不保护共享状态，却会把 send_pdf_file 的整个文件流式传输包在锁里
        （与视频流同类问题）。锁去掉了，业务逻辑与响应完全不变。
        """
        try:
            query_params = urllib.parse.parse_qs(query_string)
            path = query_params.get('path', [''])[0]
            
            if not path:
                self.send_error(HTTPStatus.BAD_REQUEST, "Missing path parameter")
                return
            
            pdf_path = urllib.parse.unquote(path)
            
            # 路径规范化
            if self.main_app and hasattr(self.main_app, 'normalize_path_separators'):
                pdf_path = self.main_app.normalize_path_separators(pdf_path)
            
            # 检查文件是否存在且是PDF文件
            if not os.path.exists(pdf_path):
                self.send_error(HTTPStatus.NOT_FOUND, "PDF file not found")
                return
            
            # 检查文件类型
            if not pdf_path.lower().endswith('.pdf'):
                self.send_error(HTTPStatus.BAD_REQUEST, "Not a PDF file")
                return
            
            # 发送PDF文件 - 使用线程安全的文件发送
            self.send_pdf_file(pdf_path)
                
        except Exception as e:
            # print(f"[SERVER ERROR] 处理PDF请求失败: {e}")
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))


    def send_pdf_file(self, pdf_path):
        """发送PDF文件 - 修复编码问题"""
        try:
            file_size = os.path.getsize(pdf_path)
            
            # 获取文件名，安全处理中文字符
            filename = os.path.basename(pdf_path)
            
            # 安全编码文件名，避免编码问题
            try:
                # 尝试UTF-8编码
                safe_filename = filename.encode('utf-8').decode('latin-1')
            except (UnicodeEncodeError, UnicodeDecodeError):
                # 如果UTF-8编码失败，使用ASCII安全名称
                safe_filename = "document.pdf"
            
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', 'application/pdf')
            self.send_header('Content-Length', str(file_size))
            
            # 使用安全的文件名
            self.send_header('Content-Disposition', f'inline; filename="{safe_filename}"')
            
            # 添加编码相关的头信息
            self.send_header('Content-Transfer-Encoding', 'binary')
            self.end_headers()
            
            # 发送文件内容
            with open(pdf_path, 'rb') as f:
                while chunk := f.read(8192):
                    try:
                        self.wfile.write(chunk)
                    except ConnectionResetError:
                        # 客户端断开连接，正常退出
                        print(f"[INFO] PDF传输中断: {pdf_path}")
                        return
                        
        except Exception as e:
            print(f"[SERVER ERROR] 发送PDF文件失败: {e}")
            # 使用安全的错误发送方法
            self.send_safe_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))

    def get_directories_data(self, filter_type="all", sort_by="name", path_filter=""):
        """获取目录数据 - 支持类型过滤、排序和路径过滤"""
        if not self.main_app or not self.main_app.user_manager.current_db_path:
            return {"directories": [], "count": 0}
        
        try:
            # 【性能优化】移除此处的 `with self.lock:` 整段加锁：
            # 1) self.lock 是每个请求处理器实例各自的 RLock（__init__ 中新建），
            #    并不保护任何跨请求共享状态，只是白担了同步开销；
            # 2) sqlite3.connect() 默认 isolation_level=''（deferred），SELECT 不会
            #    开启事务，因此该锁也从未让这次全表读取变成原子快照；
            # 3) 数据库连接每请求独立新建、用完即关（见下方 try/finally），无连接共享。
            # 保持"无 LIMIT、返回全集"的契约不变：前端 applyFiltersAndSort /
            # displayDirectories 依赖服务端返回全集后在客户端过滤、排序、渲染。
            conn = sqlite3.connect(self.main_app.user_manager.current_db_path)
            try:
                cursor = conn.cursor()
                
                # 基础查询
                base_query = """
                    SELECT id, name, path, directory_exists, created_time, last_modified, is_directory 
                    FROM directories 
                """
                
                # 构建WHERE子句
                where_clauses = []
                
                # 类型过滤
                if filter_type != "all":
                    if filter_type == "directory":
                        where_clauses.append("is_directory = 1")
                    elif filter_type == "file":
                        where_clauses.append("is_directory = 0")
                    elif filter_type == "video":
                        where_clauses.append("(path LIKE '%.mp4' OR path LIKE '%.avi' OR path LIKE '%.mkv' OR path LIKE '%.mov')")
                    elif filter_type == "image":
                        where_clauses.append("(path LIKE '%.jpg' OR path LIKE '%.jpeg' OR path LIKE '%.png' OR path LIKE '%.gif')")
                    elif filter_type == "pdf":
                        where_clauses.append("path LIKE '%.pdf'")
                    elif filter_type == "document":
                        where_clauses.append("(path LIKE '%.pdf' OR path LIKE '%.doc' OR path LIKE '%.docx' OR path LIKE '%.txt')")
                




                # 路径过滤（新增）- 简化版本
                if path_filter and path_filter.strip():
                    # 【性能优化】移除每请求的 FILTER DEBUG 打印（原 5299-5301），
                    # 大库刷新时既拖慢响应又刷屏。
                    filter_paths = [p.strip() for p in path_filter.split('|') if p.strip()]

                    if filter_paths:
                        path_conditions = []
                        for fp in filter_paths:
                            # 统一转换为小写进行匹配
                            normalized_fp = fp.replace('\\', '/').lower()
                            # 移除开头的斜杠（如果有）
                            while normalized_fp.startswith('/'):
                                normalized_fp = normalized_fp[1:]
                            
                            # 同时匹配大小写
                            path_conditions.append(f"LOWER(path) LIKE '{normalized_fp}%'")
                            path_conditions.append(f"LOWER(path) LIKE '%/{normalized_fp}%'")
                            path_conditions.append(f"LOWER(path) LIKE '%\\{normalized_fp}%'")
                        
                        if path_conditions:
                            where_clauses.append(f"({' OR '.join(path_conditions)})")
                
                # 构建完整的WHERE子句
                where_clause = ""
                if where_clauses:
                    where_clause = "WHERE " + " AND ".join(where_clauses)
                
                # 构建ORDER BY子句
                order_clause = "ORDER BY "
                if sort_by == "name":
                    order_clause += "name"
                elif sort_by == "date":
                    order_clause += "last_modified DESC"
                elif sort_by == "size":
                    order_clause += "name"
                elif sort_by == "path":
                    order_clause += "path"
                else:
                    order_clause += "name"
                
                # 执行查询
                query = f"{base_query} {where_clause} {order_clause}"
                cursor.execute(query)
                
                directories = []
                results = cursor.fetchall()
                
                for row in results:
                    try:
                        if len(row) == 7:
                            db_id, name, path, exists, created_time, last_modified, is_directory = row
                            
                            directories.append({
                                "id": db_id,
                                "name": name,
                                "path": path,
                                "exists": bool(exists),
                                "created_time": created_time,
                                "last_modified": last_modified,
                                "is_directory": bool(is_directory)
                            })
                    except Exception as e:
                        print(f"[ERROR] 处理数据库行时出错: {e}")
                        continue
                
            finally:
                conn.close()
            
            return {
                "directories": directories, 
                "count": len(directories),
                "filter_type": filter_type,
                "sort_by": sort_by,
                "path_filter": path_filter
            }
                
        except Exception as e:
            print(f"[SERVER ERROR] 获取目录数据失败: {e}")
            return {"directories": [], "count": 0, "error": str(e)}

    def is_video_file(self, filename):
        """检查是否为视频文件"""
        video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v']
        return any(filename.lower().endswith(ext) for ext in video_extensions)

    def is_image_file(self, filename):
        """检查是否为图片文件"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        return any(filename.lower().endswith(ext) for ext in image_extensions)

    def is_pdf_file(self, filename):
        """检查是否为PDF文件"""
        return filename.lower().endswith('.pdf')

    def is_document_file(self, filename):
        """检查是否为文档文件"""
        document_extensions = [
            '.pdf', '.txt', '.doc', '.docx', '.ppt', '.pptx', '.xls', 
            '.xlsx', '.rtf', '.odt', '.ods', '.odp', '.pages', '.numbers',
            '.key', '.epub', '.mobi', '.azw', '.azw3', '.fb2', '.lit',
            '.prc', '.pdb', '.chm', '.djvu', '.djv'
        ]
        return any(filename.lower().endswith(ext) for ext in document_extensions)



class DirectoryScannerServer:
    """目录扫描系统服务器 - 多线程版本"""
    
    def __init__(self, main_app, host='localhost', port=8080):
        self.main_app = main_app
        self.host = host
        self.port = self._check_port_available(port)  # 检查并获取可用端口
        self.server = None
        self.server_thread = None
        self.is_running = False
        self.lock = threading.Lock()
        self.thread_pool = ThreadPoolExecutor(max_workers=10)

    def _check_port_available(self, port):
        """检查端口是否可用，如果不可用则查找下一个可用端口"""
        import socket
        
        max_attempts = 100
        for p in range(port, port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('0.0.0.0', p))
                    return p
            except OSError:
                print(f"[SERVER] 端口 {p} 已被占用，尝试下一个...")
                continue
        
        print(f"[SERVER WARNING] 所有端口都被占用，将尝试使用原始端口 {port}")
        return port
    
    def start(self):
        """启动服务器 - 多线程版本"""
        with self.lock:
            if self.is_running:
                print("[SERVER] 服务器已经在运行")
                return True
                
        try:
            # 创建多线程TCP服务器
            self.server = socketserver.ThreadingTCPServer(
                (self.host, self.port), 
                self.create_request_handler()
            )
            self.server.allow_reuse_address = True
            
            # 在后台线程中启动服务器
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            self.is_running = True
            print(f"[SERVER] 目录扫描系统服务器已启动: http://{self.host}:{self.port}")
            print(f"[SERVER] 多线程模式，最大工作线程数: 10")
            print(f"[SERVER] 可以通过浏览器访问Web客户端")
            
            return True
            
        except Exception as e:
            print(f"[SERVER ERROR] 启动服务器失败: {e}")
            if "Address already in use" in str(e):
                print(f"[SERVER TIP] 端口 {self.port} 已被占用，请尝试其他端口或关闭占用程序")
            return False

    def create_request_handler(self):
        """创建请求处理器类 - 支持多线程"""
        main_app = self.main_app
        
        class ThreadedHTTPRequestHandler(DirectoryScannerHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, main_app=main_app, **kwargs)
            
            def handle_request(self):
                """处理单个请求 - 在单独的线程中执行"""
                try:
                    # 处理请求
                    self.raw_requestline = self.rfile.readline(65537)
                    if len(self.raw_requestline) > 65536:
                        self.requestline = ''
                        self.request_version = ''
                        self.command = ''
                        self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
                        return
                    
                    if not self.raw_requestline:
                        self.close_connection = True
                        return
                    
                    if not self.parse_request():
                        return
                    
                    # 根据方法分发处理
                    method_name = 'do_' + self.command
                    if not hasattr(self, method_name):
                        self.send_error(HTTPStatus.NOT_IMPLEMENTED, "Unsupported method (%r)" % self.command)
                        return
                    
                    method = getattr(self, method_name)
                    method()
                    self.wfile.flush()
                    
                except socket.timeout as e:
                    self.log_error("Request timed out: %r", e)
                    self.close_connection = True
                    return
                except Exception as e:
                    self.log_error("Request handling error: %s", str(e))
                    self.close_connection = True
        
        return ThreadedHTTPRequestHandler

    def stop(self):
        """停止服务器"""
        with self.lock:
            if self.server:
                try:
                    # 先关闭线程池
                    self.thread_pool.shutdown(wait=False)
                    
                    # 停止服务器
                    self.server.shutdown()
                    self.server.server_close()
                    self.is_running = False
                    print("[SERVER] 服务器已停止")
                except Exception as e:
                    print(f"[SERVER ERROR] 停止服务器时出错: {e}")
    
    def get_server_url(self):
        """获取服务器URL"""
        return f"http://{self.host}:{self.port}"


# 数据库备份管理类
class DatabaseBackupManager:
    def __init__(self, app_dir, max_backups=30):
        self.backup_dir = os.path.join(app_dir, "backups")
        self.max_backups = max_backups
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, db_path, backup_type="auto"):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{backup_type}_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        # 使用WAL模式备份
        try:
            src_conn = sqlite3.connect(db_path)
            dst_conn = sqlite3.connect(backup_path)
            
            with dst_conn:
                src_conn.backup(dst_conn, pages=1)
            
            src_conn.close()
            dst_conn.close()
            
            # 清理旧备份
            self.cleanup_old_backups()
            
            return True, backup_path
        except Exception as e:
            print(f"备份失败: {e}")
            return False, str(e)
    
    def cleanup_old_backups(self):
        backups = self.get_backup_list()
        if len(backups) > self.max_backups:
            backups.sort(key=lambda x: x[1])  # 按时间排序
            for i in range(len(backups) - self.max_backups):
                try:
                    os.remove(backups[i][0])
                except Exception as e:
                    print(f"删除旧备份失败: {e}")
    
    def get_backup_list(self):
        backups = []
        for filename in os.listdir(self.backup_dir):
            if filename.endswith(".db"):
                path = os.path.join(self.backup_dir, filename)
                stat = os.stat(path)
                size = stat.st_size
                parts = filename.split("_")
                if len(parts) >= 3:
                    backup_type = parts[0]
                    date_str = "_".join(parts[1:3]).replace(".db", "")
                    try:
                        date = datetime.datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                        backups.append((path, date, backup_type, size))
                    except:
                        continue
        return backups
    
    def restore_backup(self, backup_path, target_path):
        try:
            # 先备份当前数据库
            self.create_backup(target_path, "restore_pre")
            
            # 恢复备份
            src_conn = sqlite3.connect(backup_path)
            dst_conn = sqlite3.connect(target_path)
            
            with dst_conn:
                src_conn.backup(dst_conn, pages=1)
            
            src_conn.close()
            dst_conn.close()
            
            return True, None
        except Exception as e:
            return False, str(e)

# 用户管理类
class UserManager:
    def __init__(self, app_dir):
        self.app_dir = app_dir
        self.users_db_path = os.path.join(app_dir, "users.db")
        self.presets_path = os.path.join(app_dir, "presets.json")
        self.current_user = None
        self.current_db_path = None
        # 【性能优化】记录本次进程内已补齐过索引的用户库路径，避免重复检查
        self._indexes_ready = set()
        self.init_users_db()
        self._init_default_presets()
    
    def _init_default_presets(self):
        """初始化默认预设方案"""
        if not os.path.exists(self.presets_path):
            default_presets = {
                "默认方案": {
                    "scan_interval": "3600",
                    "auto_scan": "1",
                    "incremental_scan": "1",
                    "scan_mode": "directories",
                    "skip_empty_dirs": "1",
                    "include_filter": "",
                    "exclude_filter": "",
                    "cover_save_mode": "smart",
                    "cover_save_dir": "",
                    "scan_save_cover": "0",
                    "skip_existing_covers": "1",
                    "generate_pdf_covers": "1",
                    "pdf_cover_quality": "1",
                    "auto_start_server": "1",
                    "server_port": "8080",
                    "file_display_mode": "all",
                },
                "仅目录（无封面）": {
                    "scan_interval": "1800",
                    "auto_scan": "1",
                    "incremental_scan": "1",
                    "scan_mode": "directories",
                    "skip_empty_dirs": "1",
                    "include_filter": "",
                    "exclude_filter": "",
                    "cover_save_mode": "smart",
                    "cover_save_dir": "",
                    "scan_save_cover": "0",
                    "skip_existing_covers": "1",
                    "generate_pdf_covers": "0",
                    "pdf_cover_quality": "1",
                    "auto_start_server": "1",
                    "server_port": "8080",
                    "file_display_mode": "none",
                },
                "全面扫描": {
                    "scan_interval": "3600",
                    "auto_scan": "1",
                    "incremental_scan": "1",
                    "scan_mode": "both",
                    "skip_empty_dirs": "0",
                    "include_filter": "",
                    "exclude_filter": "",
                    "cover_save_mode": "smart",
                    "cover_save_dir": "",
                    "scan_save_cover": "1",
                    "skip_existing_covers": "0",
                    "generate_pdf_covers": "1",
                    "pdf_cover_quality": "2",
                    "auto_start_server": "1",
                    "server_port": "8080",
                    "file_display_mode": "all",
                },
            }
            self.save_presets(default_presets)
    
    def get_presets(self):
        """获取所有预设方案"""
        try:
            with open(self.presets_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"默认方案": {}}
    
    def save_presets(self, presets):
        """保存预设方案"""
        with open(self.presets_path, 'w', encoding='utf-8') as f:
            json.dump(presets, f, ensure_ascii=False, indent=2)
    
    def get_preset_settings(self, preset_name):
        """获取指定预设方案的设置"""
        presets = self.get_presets()
        return presets.get(preset_name, {})
    
    def apply_preset_to_db(self, db_path, preset_name):
        """将预设方案应用到指定数据库"""
        settings = self.get_preset_settings(preset_name)
        if not settings:
            return
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM settings")
            for key, value in settings.items():
                cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[PRESET ERROR] 应用预设方案失败: {e}")
    
    def init_users_db(self):
        # 确保目录存在
        if not os.path.exists(self.app_dir):
            os.makedirs(self.app_dir)
            
        if not os.path.exists(self.users_db_path):
            try:
                conn = sqlite3.connect(self.users_db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        created_at TEXT NOT NULL,
                        last_login TEXT
                    )
                """)
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"初始化用户数据库失败: {e}")

    
    def add_user(self, username, preset_name="默认方案"):
        conn = sqlite3.connect(self.users_db_path)
        cursor = conn.cursor()
        
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO users (username, created_at) VALUES (?, ?)", 
                          (username, now))
            conn.commit()
            
            # 创建用户数据库（使用指定预设方案）
            user_db_path = os.path.join(self.app_dir, f"user_{username}.db")
            self.init_user_db(user_db_path, preset_name)
            
            return True, None
        except sqlite3.IntegrityError:
            return False, "用户名已存在"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    
    def init_user_db(self, db_path, preset_name="默认方案"):
        try:
            if not os.path.exists(os.path.dirname(db_path)):
                os.makedirs(os.path.dirname(db_path))

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 创建目录表（省略，与之前相同）...
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS directories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    path TEXT UNIQUE NOT NULL,
                    created_time TEXT NOT NULL,
                    last_modified TEXT NOT NULL,
                    directory_exists INTEGER DEFAULT 1,
                    last_scanned TEXT,
                    is_main_dir INTEGER DEFAULT 0,
                    is_directory INTEGER DEFAULT 1
                )
            """)
            
            # 确保关键索引存在（加速 keyset 分页和过滤查询）
            # 【性能优化】DDL 统一由 _directories_index_statements 提供，与登录路径补索引共用同一份定义
            for _index_stmt in self._directories_index_statements():
                cursor.execute(_index_stmt)

            # 验证表结构
            cursor.execute("PRAGMA table_info(directories)")
            columns = cursor.fetchall()
            print(f"[DEBUG] 数据库表结构: {columns}")

            # 检查必需的列
            required_columns = ['id', 'name', 'path', 'created_time', 'last_modified', 'directory_exists', 'is_directory']
            existing_columns = [col[1] for col in columns]

            for req_col in required_columns:
                if req_col not in existing_columns:
                    print(f"[ERROR] 缺少必需列: {req_col}")
                    # 这里可以添加修复逻辑

            if 'is_directory' not in columns:
                try:
                    cursor.execute("ALTER TABLE directories ADD COLUMN is_directory INTEGER DEFAULT 1")
                    print(f"[DEBUG] 已添加 is_directory 列到数据库")
                except sqlite3.OperationalError as e:
                    print(f"[DEBUG] 添加 is_directory 列时出错: {e}")
            
            # 新增主目录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS main_directories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    name TEXT,
                    scan_depth INTEGER DEFAULT 3,
                    created_time TEXT NOT NULL
                )
            """)
    
            # 创建设置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT
                )
            """)
            
            # 应用预设方案设置
            settings = self.get_preset_settings(preset_name)
            for key, value in settings.items():
                try:
                    cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))
                except sqlite3.IntegrityError:
                    pass
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"初始化用户数据库失败: {e}")
    
    def delete_user(self, username):
        conn = sqlite3.connect(self.users_db_path)
        cursor = conn.cursor()
        
        try:
            # 从用户表中删除
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            conn.commit()
            
            # 删除用户数据库文件
            user_db_path = os.path.join(self.app_dir, f"user_{username}.db")
            if os.path.exists(user_db_path):
                os.remove(user_db_path)
            
            return True, None
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    
    def rename_user(self, old_username, new_username):
        conn = sqlite3.connect(self.users_db_path)
        cursor = conn.cursor()
        
        try:
            # 更新用户名
            cursor.execute("UPDATE users SET username = ? WHERE username = ?", 
                          (new_username, old_username))
            conn.commit()
            
            # 重命名用户数据库文件
            old_db_path = os.path.join(self.app_dir, f"user_{old_username}.db")
            new_db_path = os.path.join(self.app_dir, f"user_{new_username}.db")
            
            if os.path.exists(old_db_path):
                os.rename(old_db_path, new_db_path)
            
            return True, None
        except sqlite3.IntegrityError:
            return False, "新用户名已存在"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    
    def get_all_users(self):
        conn = sqlite3.connect(self.users_db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT username, created_at, last_login FROM users ORDER BY username")
        users = cursor.fetchall()
        conn.close()
        
        return users
    
    def login_user(self, username):
        conn = sqlite3.connect(self.users_db_path)
        cursor = conn.cursor()
        
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE users SET last_login = ? WHERE username = ?", (now, username))
            conn.commit()
            
            self.current_user = username
            self.current_db_path = os.path.join(self.app_dir, f"user_{username}.db")
            
            print(f"[INFO] 用户 {username} 登录成功")

            # 【性能优化】登录后补齐该用户库缺失的索引（历史库从未建过索引）
            self.ensure_user_db_indexes(self.current_db_path)

            return True, None
        except Exception as e:
            print(f"[ERROR] 用户登录失败: {e}")
            return False, str(e)
        finally:
            conn.close()

    def ensure_user_db_indexes(self, db_path):
        """【性能优化】为已存在的用户数据库补齐关键索引。

        历史库是在 init_user_db 加入 CREATE INDEX 之前创建的，从未建过索引，
        导致 load_directories 的 keyset 分页（ORDER BY name）退化为全表排序，
        实测慢 13.8 倍。这里做幂等补齐：CREATE INDEX IF NOT EXISTS 不会重复建，
        索引已存在时只读 sqlite_master，开销可忽略。

        同时顺带调优 page cache，减少大库分页时的磁盘读。
        只操作索引与连接级 PRAGMA，不改动任何表数据。
        """
        if not db_path or not os.path.exists(db_path):
            return False
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA cache_size=-40000")   # 40MB page cache
            cursor.execute("PRAGMA temp_store=MEMORY")
            # directories 表不存在时无需建索引（新库由 init_user_db 负责建表 + 索引）
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='directories'")
            if not cursor.fetchone():
                return False
            for stmt in self._directories_index_statements():
                cursor.execute(stmt)
            conn.commit()
            self._indexes_ready.add(db_path)
            print(f"[INFO] 已确保用户库索引: {os.path.basename(db_path)}")
            return True
        except Exception as e:
            print(f"[WARN] 补齐用户库索引失败 {db_path}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def _directories_index_statements():
        """directories 表的全部索引 DDL（幂等，init_user_db 与补索引共用同一份定义）"""
        return (
            "CREATE INDEX IF NOT EXISTS idx_directories_name ON directories(name)",
            "CREATE INDEX IF NOT EXISTS idx_directories_path ON directories(path)",
            "CREATE INDEX IF NOT EXISTS idx_directories_last_modified ON directories(last_modified)",
            "CREATE INDEX IF NOT EXISTS idx_directories_is_directory ON directories(is_directory)",
        )

    def clear_user_data(self, username, preset_name="默认方案"):
        """清除指定用户的所有目录数据，并应用预设方案"""
        user_db_path = os.path.join(self.app_dir, f"user_{username}.db")
        if not os.path.exists(user_db_path):
            return False, "用户数据库不存在"
        
        try:
            conn = sqlite3.connect(user_db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM directories")
            cursor.execute("DELETE FROM main_directories")
            cursor.execute("DELETE FROM settings")
            
            # 应用指定预设方案的设置
            settings = self.get_preset_settings(preset_name)
            for key, value in settings.items():
                cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))
            
            conn.commit()
            conn.close()
            
            return True, None
        except Exception as e:
            return False, str(e)


# 恢复数据库对话框
class RestoreDatabaseDialog(QDialog):
    def __init__(self, backup_manager, db_path, parent=None):
        super().__init__(parent)
        self.backup_manager = backup_manager
        self.db_path = db_path
        self.setWindowTitle("数据库恢复")
        self.setMinimumSize(800, 600)
        
        self.init_ui()
        self.load_backups()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 筛选条件
        filter_group = QGroupBox("筛选条件")
        filter_layout = QHBoxLayout()
        
        self.type_filter = QComboBox()
        self.type_filter.addItem("所有类型", "")
        self.type_filter.addItem("自动备份", "auto")
        self.type_filter.addItem("手动备份", "manual")
        self.type_filter.addItem("恢复前备份", "restore_pre")
        self.type_filter.addItem("回滚备份", "rollback")
        self.type_filter.currentIndexChanged.connect(self.load_backups)
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.dateChanged.connect(self.load_backups)
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setDate(self.date_from.date().addDays(1))
        self.date_to.dateChanged.connect(self.load_backups)
        
        filter_layout.addWidget(QLabel("备份类型:"))
        filter_layout.addWidget(self.type_filter)
        filter_layout.addWidget(QLabel("从:"))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel("到:"))
        filter_layout.addWidget(self.date_to)
        filter_layout.addStretch()
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # 备份列表
        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(5)
        self.backup_table.setHorizontalHeaderLabels(["备份时间", "备份类型", "文件大小", "操作", "详细信息"])
        self.backup_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.backup_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.backup_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.backup_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.backup_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.backup_table.verticalHeader().setVisible(False)
        self.backup_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.backup_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.backup_table)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.restore_button = QPushButton("恢复选中备份")
        self.restore_button.clicked.connect(self.restore_selected_backup)
        self.restore_button.setEnabled(False)
        
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.restore_button)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 连接信号
        self.backup_table.itemSelectionChanged.connect(self.update_restore_button_state)
    
    def load_backups(self):
        self.backup_table.setRowCount(0)
        backups = self.backup_manager.get_backup_list()
        
        filter_type = self.type_filter.currentData()
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")
        
        for backup in backups:
            path, date, btype, size = backup
            date_str = date.strftime("%Y-%m-%d %H:%M:%S")
            date_only = date.strftime("%Y-%m-%d")
            
            # 应用筛选条件
            if filter_type and btype != filter_type:
                continue
            if date_only < date_from or date_only > date_to:
                continue
            
            row = self.backup_table.rowCount()
            self.backup_table.insertRow(row)
            
            # 备份时间
            self.backup_table.setItem(row, 0, QTableWidgetItem(date_str))
            
            # 备份类型
            type_text = {
                "auto": "自动备份",
                "manual": "手动备份",
                "restore_pre": "恢复前备份",
                "rollback": "回滚备份"
            }.get(btype, btype)
            self.backup_table.setItem(row, 1, QTableWidgetItem(type_text))
            
            # 文件大小
            size_text = self.format_size(size)
            self.backup_table.setItem(row, 2, QTableWidgetItem(size_text))
            
            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(0, 0, 0, 0)
            
            restore_btn = QPushButton("恢复")
            restore_btn.clicked.connect(lambda _, p=path: self.restore_backup(p))
            restore_btn.setFixedWidth(60)
            
            btn_layout.addWidget(restore_btn)
            btn_widget.setLayout(btn_layout)
            self.backup_table.setCellWidget(row, 3, btn_widget)
            
            # 详细信息
            details = self.get_backup_details(path)
            self.backup_table.setItem(row, 4, QTableWidgetItem(details))
    
    def format_size(self, size):
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"
    
    def get_backup_details(self, backup_path):
        try:
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            
            # 获取目录数量
            cursor.execute("SELECT COUNT(*) FROM directories")
            dir_count = cursor.fetchone()[0]
            
            # 获取最早的目录创建时间
            cursor.execute("SELECT MIN(created_time) FROM directories")
            min_date = cursor.fetchone()[0]
            
            # 获取最新的目录修改时间
            cursor.execute("SELECT MAX(last_modified) FROM directories")
            max_date = cursor.fetchone()[0]
            
            conn.close()
            
            details = f"包含 {dir_count} 个目录"
            if min_date and max_date:
                details += f", 时间范围: {min_date} 至 {max_date}"
            
            return details
        except Exception as e:
            return "无法获取详细信息"
    
    def update_restore_button_state(self):
        selected = len(self.backup_table.selectedItems()) > 0
        self.restore_button.setEnabled(selected)
    
    def restore_selected_backup(self):
        selected_rows = set(item.row() for item in self.backup_table.selectedItems())
        if not selected_rows:
            return
        
        row = next(iter(selected_rows))
        path = self.backup_table.item(row, 4).data(Qt.UserRole)  # 我们在load_backups中存储了路径
        
        self.restore_backup(path)
    
    def restore_backup(self, backup_path):
        """恢复备份 - 改为使用多线程"""
        self.parent().restore_database_threaded(backup_path)

# 用户管理对话框
class UserManagerDialog(QDialog):
    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.setWindowTitle("用户管理")
        self.setMinimumSize(600, 400)
        
        self.init_ui()
        self.load_users()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 用户列表
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(4)
        self.user_table.setHorizontalHeaderLabels(["用户名", "创建时间", "最后登录", "操作"])
        self.user_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.user_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.user_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.user_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.user_table.verticalHeader().setVisible(False)
        self.user_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.user_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.user_table)
        
        # 添加用户
        add_group = QGroupBox("添加新用户")
        add_layout = QHBoxLayout()
        
        self.new_username = QLineEdit()
        self.new_username.setPlaceholderText("输入新用户名")
        
        self.preset_combo = QComboBox()
        self.preset_combo.setToolTip("选择初始设置方案")
        self._load_preset_list()
        
        add_button = QPushButton("➕添加")
        add_button.clicked.connect(self.add_user)
        add_button.setFixedWidth(80)
        
        add_layout.addWidget(QLabel("用户名:"))
        add_layout.addWidget(self.new_username)
        add_layout.addWidget(QLabel("方案:"))
        add_layout.addWidget(self.preset_combo)
        add_layout.addWidget(add_button)
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)
        
        # 方案管理按钮
        manage_presets_btn = QPushButton("📋 管理默认方案...")
        manage_presets_btn.clicked.connect(self.manage_presets)
        layout.addWidget(manage_presets_btn)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        self.login_button = QPushButton("🔑登录选中用户")
        self.login_button.clicked.connect(self.login_selected_user)
        self.login_button.setEnabled(False)
        
        self.close_button = QPushButton("❌关闭")
        self.close_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 连接信号
        self.user_table.itemSelectionChanged.connect(self.update_login_button_state)
    
    def load_users(self):
        self.user_table.setRowCount(0)
        users = self.user_manager.get_all_users()
        
        for user in users:
            username, created_at, last_login = user
            row = self.user_table.rowCount()
            self.user_table.insertRow(row)
            
            # 用户名
            self.user_table.setItem(row, 0, QTableWidgetItem(username))
            
            # 创建时间
            self.user_table.setItem(row, 1, QTableWidgetItem(created_at))
            
            # 最后登录
            self.user_table.setItem(row, 2, QTableWidgetItem(last_login if last_login else "从未登录"))
            
            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(0, 0, 0, 0)
            
            login_btn = QPushButton("🔑登录")
            login_btn.clicked.connect(lambda _, u=username: self.login_user(u))
            login_btn.setFixedWidth(60)
            
            rename_btn = QPushButton("✏️重命名")
            rename_btn.clicked.connect(lambda _, u=username: self.rename_user(u))
            rename_btn.setFixedWidth(60)
            
            delete_btn = QPushButton("🗑️删除")
            delete_btn.clicked.connect(lambda _, u=username: self.delete_user(u))
            delete_btn.setFixedWidth(60)

            clear_btn = QPushButton("🧹清除数据")
            clear_btn.clicked.connect(lambda _, u=username: self.clear_user_data(u))
            clear_btn.setFixedWidth(60)
            clear_btn.setStyleSheet("background-color: #ffeb3b;")  # 黄色背景以示警告

            btn_layout.addWidget(login_btn)
            btn_layout.addWidget(rename_btn)
            btn_layout.addWidget(delete_btn)
            btn_layout.addWidget(clear_btn)

            btn_widget.setLayout(btn_layout)
            self.user_table.setCellWidget(row, 3, btn_widget)
    
    def update_login_button_state(self):
        selected = len(self.user_table.selectedItems()) > 0
        self.login_button.setEnabled(selected)
    
    def login_selected_user(self):
        selected_rows = set(item.row() for item in self.user_table.selectedItems())
        if not selected_rows:
            return
        
        row = next(iter(selected_rows))
        username = self.user_table.item(row, 0).text()
        
        self.login_user(username)
    
    def login_user(self, username):
        # 显示登录中状态
        if hasattr(self, 'parent') and self.parent():
            self.parent().statusBar().showMessage(f"正在登录用户 {username}...")
            QApplication.processEvents()
        
        success, error = self.user_manager.login_user(username)
        if success:
            if hasattr(self, 'parent') and self.parent():
                self.parent().statusBar().showMessage(f"用户 {username} 登录成功")
            self.accept()
        else:
            if hasattr(self, 'parent') and self.parent():
                self.parent().statusBar().showMessage("登录失败")
            QMessageBox.critical(self, "登录失败", f"登录用户 {username} 时出错:\n{error}")

    
    def manage_presets(self):
        """打开预设方案管理对话框"""
        dialog = PresetManagerDialog(self.user_manager, self)
        if dialog.exec() == QDialog.Accepted:
            # 保存可能已修改的方案
            self.user_manager.save_presets(dialog.presets)
            self._load_preset_list()

    def _load_preset_list(self):
        """加载预设方案列表到下拉框"""
        presets = self.user_manager.get_presets()
        self.preset_combo.clear()
        for name in presets.keys():
            self.preset_combo.addItem(name)

    def add_user(self):
        username = self.new_username.text().strip()
        if not username:
            QMessageBox.warning(self, "无效输入", "用户名不能为空")
            return
        
        preset_name = self.preset_combo.currentText()
        success, error = self.user_manager.add_user(username, preset_name)
        if success:
            self.new_username.clear()
            self.load_users()
            QMessageBox.information(self, "添加成功", f"用户 {username} 已成功添加（方案: {preset_name}）")
        else:
            QMessageBox.critical(self, "添加失败", f"添加用户时出错:\n{error}")
    
    def rename_user(self, old_username):
        new_username, ok = QInputDialog.getText(
            self, "重命名用户", "输入新用户名:", text=old_username
        )
        
        if ok and new_username:
            if new_username == old_username:
                return
            
            success, error = self.user_manager.rename_user(old_username, new_username)
            if success:
                self.load_users()
                QMessageBox.information(self, "重命名成功", f"用户已从 {old_username} 重命名为 {new_username}")
            else:
                QMessageBox.critical(self, "重命名失败", f"重命名用户时出错:\n{error}")
    
    def delete_user(self, username):
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除用户 {username} 吗？\n此操作将删除该用户的所有数据且不可恢复！",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, error = self.user_manager.delete_user(username)
            if success:
                self.load_users()
                QMessageBox.information(self, "删除成功", f"用户 {username} 已成功删除")
            else:
                QMessageBox.critical(self, "删除失败", f"删除用户时出错:\n{error}")

    def clear_user_data(self, username):
        # 让用户选择重置后的方案
        presets = self.user_manager.get_presets()
        preset_names = list(presets.keys())
        preset_name, ok = QInputDialog.getItem(
            self, "选择重置方案", 
            f"清除 {username} 的数据后，使用哪个方案？",
            preset_names, 0, False
        )
        if not ok:
            return
        
        reply = QMessageBox.question(
            self, "确认清除数据",
            f"确定要清除用户 {username} 的所有目录数据吗？\n此操作将删除所有扫描记录但保留用户账户。\n\n重置后将应用方案: {preset_name}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, error = self.user_manager.clear_user_data(username, preset_name)
            if success:
                QMessageBox.information(self, "清除成功", f"用户 {username} 的数据已清除（方案: {preset_name}）")
                if self.user_manager.current_user == username:
                    parent = self.parent()
                    parent._clear_table()
                    parent.load_user_settings()
                    parent._load_data_with_progress()
                    parent.main_directory = ""
                    parent.dir_label.setText("主目录: 未设置")
            else:
                QMessageBox.critical(self, "清除失败", f"清除数据时出错:\n{error}")



# 预设方案管理对话框
class PresetManagerDialog(QDialog):
    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.presets = dict(user_manager.get_presets())  # 深拷贝
        self._selected_left = None
        self._selected_right = None
        self.setWindowTitle("管理默认方案")
        self.setMinimumSize(750, 500)
        self.resize(800, 550)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 顶部：方案列表
        top = QHBoxLayout()
        
        # 左侧方案列表
        left_group = QGroupBox("方案列表")
        left_layout = QVBoxLayout()
        self.preset_list = QListWidget()
        self.preset_list.currentTextChanged.connect(self._on_preset_selected)
        self._refresh_list()
        left_layout.addWidget(self.preset_list)
        
        left_btns = QHBoxLayout()
        add_btn = QPushButton("➕ 新建")
        add_btn.clicked.connect(self._add_preset)
        del_btn = QPushButton("🗑️ 删除")
        del_btn.clicked.connect(self._delete_preset)
        rename_btn = QPushButton("✏️ 重命名")
        rename_btn.clicked.connect(self._rename_preset)
        left_btns.addWidget(add_btn)
        left_btns.addWidget(rename_btn)
        left_btns.addWidget(del_btn)
        left_layout.addLayout(left_btns)
        left_group.setLayout(left_layout)
        top.addWidget(left_group, 2)
        
        # 右侧设置详情
        right_group = QGroupBox("方案设置")
        right_layout = QVBoxLayout()
        self.settings_table = QTableWidget()
        self.settings_table.setColumnCount(2)
        self.settings_table.setHorizontalHeaderLabels(["设置项", "值"])
        self.settings_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.settings_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.settings_table.verticalHeader().setVisible(False)
        self.settings_table.setEditTriggers(QTableWidget.NoEditTriggers)
        right_layout.addWidget(self.settings_table)
        right_group.setLayout(right_layout)
        top.addWidget(right_group, 3)
        
        layout.addLayout(top)
        
        # 底部：对比 + 保存 + 关闭
        bottom = QHBoxLayout()
        compare_btn = QPushButton("🔍 对比两个方案")
        compare_btn.clicked.connect(self._compare_presets)
        save_btn = QPushButton("💾 保存修改")
        save_btn.clicked.connect(self._save_all)
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 6px 16px;")
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        bottom.addWidget(compare_btn)
        bottom.addStretch()
        bottom.addWidget(save_btn)
        bottom.addWidget(close_btn)
        layout.addLayout(bottom)
        
        self.setLayout(layout)
    
    def _refresh_list(self):
        self.preset_list.clear()
        for name in sorted(self.presets.keys()):
            self.preset_list.addItem(name)
    
    def _on_preset_selected(self, name):
        if not name:
            return
        settings = self.presets.get(name, {})
        self.settings_table.setRowCount(len(settings))
        # 友好的标签映射
        labels = {
            "scan_interval": "扫描间隔(秒)", "auto_scan": "自动扫描",
            "incremental_scan": "增量扫描", "scan_mode": "扫描模式",
            "skip_empty_dirs": "跳过空目录", "include_filter": "包含过滤",
            "exclude_filter": "排除过滤", "cover_save_mode": "封面保存模式",
            "cover_save_dir": "封面保存目录", "scan_save_cover": "扫描时保存封面",
            "skip_existing_covers": "跳过已有封面", "generate_pdf_covers": "生成PDF封面",
            "pdf_cover_quality": "PDF封面质量", "auto_start_server": "自动启动服务器",
            "server_port": "服务器端口", "file_display_mode": "文件显示模式",
        }
        for i, (key, value) in enumerate(sorted(settings.items())):
            label = labels.get(key, key)
            self.settings_table.setItem(i, 0, QTableWidgetItem(label))
            self.settings_table.setItem(i, 1, QTableWidgetItem(str(value)))
    
    def _add_preset(self):
        name, ok = QInputDialog.getText(self, "新建方案", "方案名称:")
        if ok and name.strip():
            if name in self.presets:
                QMessageBox.warning(self, "已存在", "该方案名已存在")
                return
            # 复制当前选中方案或默认方案
            current = self.preset_list.currentItem()
            template_name = current.text() if current else "默认方案"
            template = self.presets.get(template_name, self.presets.get("默认方案", {}))
            self.presets[name.strip()] = dict(template)
            self._refresh_list()
    
    def _delete_preset(self):
        current = self.preset_list.currentItem()
        if not current:
            return
        name = current.text()
        if len(self.presets) <= 1:
            QMessageBox.warning(self, "无法删除", "至少保留一个方案")
            return
        reply = QMessageBox.question(self, "确认删除", f"删除方案 '{name}'？")
        if reply == QMessageBox.Yes:
            del self.presets[name]
            self._refresh_list()
    
    def _rename_preset(self):
        current = self.preset_list.currentItem()
        if not current:
            return
        old_name = current.text()
        new_name, ok = QInputDialog.getText(self, "重命名", "新名称:", text=old_name)
        if ok and new_name.strip() and new_name != old_name:
            if new_name in self.presets:
                QMessageBox.warning(self, "已存在", "该方案名已存在")
                return
            self.presets[new_name.strip()] = self.presets.pop(old_name)
            self._refresh_list()
    
    def _save_all(self):
        self.user_manager.save_presets(self.presets)
        QMessageBox.information(self, "已保存", "所有方案修改已保存")
    
    def _compare_presets(self):
        """对比多个方案，支持 Ctrl/Shift 多选，支持直接编辑值"""
        names = sorted(self.presets.keys())
        if len(names) < 2:
            QMessageBox.warning(self, "无法对比", "至少需要两个方案")
            return
        
        # 多选对话框（ExtendedSelection 支持 Ctrl+Shift）
        dlg = QDialog(self)
        dlg.setWindowTitle("选择要对比的方案（Ctrl/Shift 多选）")
        dlg.setMinimumSize(300, 250)
        dlg_layout = QVBoxLayout()
        dlg_layout.addWidget(QLabel("选择方案（可 Ctrl+Click 或 Shift+Click 多选）："))
        
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        for name in names:
            list_widget.addItem(QListWidgetItem(name))
        # 默认全选
        list_widget.selectAll()
        dlg_layout.addWidget(list_widget)
        
        ok_btn = QPushButton("开始对比")
        ok_btn.clicked.connect(dlg.accept)
        dlg_layout.addWidget(ok_btn)
        dlg.setLayout(dlg_layout)
        
        if dlg.exec() != QDialog.Accepted:
            return
        
        selected = [item.text() for item in list_widget.selectedItems()]
        if len(selected) < 2:
            QMessageBox.warning(self, "无法对比", "请至少选择2个方案")
            return
        
        all_keys = sorted(set(k for n in selected for k in self.presets.get(n, {}).keys()))
        
        labels = {
            "scan_interval": "扫描间隔(秒)", "auto_scan": "自动扫描",
            "incremental_scan": "增量扫描", "scan_mode": "扫描模式",
            "skip_empty_dirs": "跳过空目录", "include_filter": "包含过滤",
            "exclude_filter": "排除过滤", "cover_save_mode": "封面保存模式",
            "cover_save_dir": "封面保存目录", "scan_save_cover": "扫描时保存封面",
            "skip_existing_covers": "跳过已有封面", "generate_pdf_covers": "生成PDF封面",
            "pdf_cover_quality": "PDF封面质量", "auto_start_server": "自动启动服务器",
            "server_port": "服务器端口", "file_display_mode": "文件显示模式",
        }
        
        result_dlg = QDialog(self)
        result_dlg.setWindowTitle(f"方案对比 ({len(selected)} 个) — 双击单元格可编辑")
        result_dlg.setMinimumSize(200 + 160 * len(selected), 450)
        result_dlg.resize(250 + 180 * len(selected), 500)
        rl = QVBoxLayout()
        
        table = QTableWidget()
        ncols = 1 + len(selected)
        table.setColumnCount(ncols)
        headers = ["设置项"] + selected
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        
        diff_yellow = QBrush(QColor("#fff9c4"))
        
        for i, key in enumerate(all_keys):
            table.insertRow(i)
            label = labels.get(key, key)
            label_item = QTableWidgetItem(label)
            label_item.setFlags(label_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(i, 0, label_item)
            
            values = []
            for j, name in enumerate(selected):
                v = str(self.presets.get(name, {}).get(key, ""))
                values.append(v)
                item = QTableWidgetItem(v)
                item.setData(Qt.UserRole, (name, key))  # 存储方案名和键名
                table.setItem(i, j + 1, item)
            
            if len(set(values)) > 1:
                for col in range(ncols):
                    if table.item(i, col):
                        table.item(i, col).setBackground(diff_yellow)
        
        # 编辑保存逻辑
        def on_cell_changed(row, col):
            if col == 0:
                return
            item = table.item(row, col)
            if not item:
                return
            data = item.data(Qt.UserRole)
            if not data:
                return
            name, key = data
            new_val = item.text()
            self.presets[name][key] = new_val
            # 重新检查差异并高亮
            values = []
            for c in range(1, ncols):
                it = table.item(row, c)
                if it:
                    values.append(it.text())
            bg = diff_yellow if len(set(values)) > 1 else QBrush()
            for c in range(ncols):
                if table.item(row, c):
                    table.item(row, c).setBackground(bg)
        
        table.cellChanged.connect(on_cell_changed)
        
        rl.addWidget(QLabel(f"共 {len(all_keys)} 项 | 💡 双击单元格可直接编辑方案值"))
        rl.addWidget(table)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 保存修改")
        save_btn.clicked.connect(lambda: (self.user_manager.save_presets(self.presets), QMessageBox.information(result_dlg, "已保存", "方案修改已保存")))
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 6px 16px;")
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(result_dlg.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(close_btn)
        rl.addLayout(btn_layout)
        result_dlg.setLayout(rl)
        result_dlg.exec()
    
    def get_presets(self):
        return self.presets



# 设置对话框 （每个用户独立保存所有设置）
class SettingsDialog(QDialog):
    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.parent_app = parent
        self.setWindowTitle("设置（修改即保存）")
        self.setMinimumSize(520, 420)
        self.resize(550, 480)
        
        # 防抖定时器（QLineEdit 输入时延迟保存）
        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._auto_save)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        layout = QVBoxLayout()
        tabs = QTabWidget()
        
        tabs.addTab(self._create_scan_tab(), "🔍 扫描设置")
        tabs.addTab(self._create_cover_tab(), "🖼️ 封面设置")
        tabs.addTab(self._create_pdf_tab(), "📄 PDF设置")
        tabs.addTab(self._create_display_tab(), "👁️ 显示设置")
        tabs.addTab(self._create_server_tab(), "🌐 服务器")
        
        layout.addWidget(tabs)
        
        # 底部：状态提示 + 保存方案 + 关闭按钮
        button_layout = QHBoxLayout()
        self._save_status = QLabel("💡 修改即自动保存")
        self._save_status.setStyleSheet("color: #4CAF50; font-size: 11px;")
        
        save_preset_btn = QPushButton("💾 保存为默认方案")
        save_preset_btn.setToolTip("将当前设置保存为一个新的预设方案，供新建/重置用户时选择")
        save_preset_btn.clicked.connect(self._save_as_preset)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self._save_status)
        button_layout.addWidget(save_preset_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def _create_scan_tab(self):
        """创建扫描设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 扫描间隔
        interval_group = QGroupBox("⏱️ 扫描间隔")
        interval_layout = QHBoxLayout()
        self.scan_interval = QSpinBox()
        self.scan_interval.setMinimum(1)
        self.scan_interval.setMaximum(24 * 60)
        self.scan_interval.setSuffix(" 分钟")
        interval_layout.addWidget(QLabel("自动扫描间隔:"))
        interval_layout.addWidget(self.scan_interval)
        interval_layout.addStretch()
        interval_group.setLayout(interval_layout)
        layout.addWidget(interval_group)
        
        # 自动扫描
        self.auto_scan = QCheckBox("启用自动扫描")
        layout.addWidget(self.auto_scan)
        
        # 增量扫描
        inc_group = QGroupBox("⚡ 增量扫描")
        inc_layout = QVBoxLayout()
        self.incremental_scan = QCheckBox("启用增量扫描（推荐）")
        self.incremental_scan.setToolTip("只扫描变化的目录，大幅提升扫描速度")
        self.incremental_scan.setChecked(True)
        inc_info = QLabel("💡 首次全量扫描，后续仅检测变化")
        inc_info.setStyleSheet("color: #666; font-size: 11px; margin-left: 20px;")
        inc_layout.addWidget(self.incremental_scan)
        inc_layout.addWidget(inc_info)
        inc_group.setLayout(inc_layout)
        layout.addWidget(inc_group)
        
        # 扫描模式
        mode_group = QGroupBox("📋 扫描模式")
        mode_layout = QHBoxLayout()
        self.scan_mode = QComboBox()
        self.scan_mode.addItem("扫描目录和文件（推荐）", "both")
        self.scan_mode.addItem("仅扫描目录", "directories")
        self.scan_mode.addItem("仅扫描文件", "files")
        mode_layout.addWidget(QLabel("扫描模式:"))
        mode_layout.addWidget(self.scan_mode)
        mode_layout.addStretch()
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # 目录过滤
        filter_group = QGroupBox("🔽 目录过滤")
        filter_layout = QVBoxLayout()
        self.skip_empty_dirs = QCheckBox("跳过空白目录")
        self.skip_empty_dirs.setToolTip("跳过没有任何文件的空目录")
        filter_layout.addWidget(self.skip_empty_dirs)
        
        inc_layout2 = QHBoxLayout()
        self.include_filter = QLineEdit()
        self.include_filter.setPlaceholderText("例如: project,work (逗号分隔)")
        inc_layout2.addWidget(QLabel("包含:"))
        inc_layout2.addWidget(self.include_filter)
        filter_layout.addLayout(inc_layout2)
        
        exc_layout = QHBoxLayout()
        self.exclude_filter = QLineEdit()
        self.exclude_filter.setPlaceholderText("例如: temp,backup (逗号分隔)")
        exc_layout.addWidget(QLabel("排除:"))
        exc_layout.addWidget(self.exclude_filter)
        filter_layout.addLayout(exc_layout)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        
        # 修改即保存
        self.scan_interval.valueChanged.connect(self._auto_save)
        self.auto_scan.stateChanged.connect(self._auto_save)
        self.incremental_scan.stateChanged.connect(self._auto_save)
        self.scan_mode.currentIndexChanged.connect(self._auto_save)
        self.skip_empty_dirs.stateChanged.connect(self._auto_save)
        self.include_filter.textChanged.connect(self._debounce_save)
        self.exclude_filter.textChanged.connect(self._debounce_save)
        
        return tab
    
    def _create_cover_tab(self):
        """创建封面设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 封面保存模式
        mode_group = QGroupBox("📁 保存模式")
        mode_layout = QVBoxLayout()
        
        cm_layout = QHBoxLayout()
        cm_layout.addWidget(QLabel("保存模式:"))
        self.cover_save_mode = QComboBox()
        self.cover_save_mode.addItem("智能模式（推荐）", "smart")
        self.cover_save_mode.addItem("系列模式", "series")
        self.cover_save_mode.addItem("首字模式", "first_char")
        cm_layout.addWidget(self.cover_save_mode)
        cm_layout.addStretch()
        mode_layout.addLayout(cm_layout)
        
        cd_layout = QHBoxLayout()
        cd_layout.addWidget(QLabel("保存目录:"))
        self.cover_save_dir = QLineEdit()
        self.cover_save_dir.setPlaceholderText("留空使用默认: ~/目录封面")
        cover_browse_btn = QPushButton("浏览...")
        cover_browse_btn.clicked.connect(self.browse_cover_save_dir)
        cd_layout.addWidget(self.cover_save_dir)
        cd_layout.addWidget(cover_browse_btn)
        mode_layout.addLayout(cd_layout)
        
        info = QLabel("智能: 自动识别AV格式 | 系列: XXXX-#### | 首字: 按首字母")
        info.setStyleSheet("color: #666; font-size: 11px;")
        mode_layout.addWidget(info)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # 扫描时保存
        save_group = QGroupBox("💾 自动保存")
        save_layout = QVBoxLayout()
        self.scan_save_cover = QCheckBox("扫描时自动保存封面")
        self.scan_save_cover.setToolTip("每次扫描目录时自动保存封面图片")
        self.skip_existing_covers = QCheckBox("封面已存在则跳过")
        self.skip_existing_covers.setToolTip("如果备份已存在则跳过保存")
        self.skip_existing_covers.setChecked(True)
        save_layout.addWidget(self.scan_save_cover)
        save_layout.addWidget(self.skip_existing_covers)
        save_group.setLayout(save_layout)
        layout.addWidget(save_group)
        
        # 批量操作
        batch_group = QGroupBox("📦 批量操作")
        batch_layout = QHBoxLayout()
        batch_all = QPushButton("批量保存所有封面")
        batch_all.clicked.connect(self.batch_save_all_covers)
        batch_missing = QPushButton("只保存缺失封面")
        batch_missing.clicked.connect(self.batch_save_missing_covers)
        batch_layout.addWidget(batch_all)
        batch_layout.addWidget(batch_missing)
        batch_layout.addStretch()
        batch_group.setLayout(batch_layout)
        layout.addWidget(batch_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        
        # 修改即保存
        self.cover_save_mode.currentIndexChanged.connect(self._auto_save)
        self.cover_save_dir.textChanged.connect(self._debounce_save)
        self.scan_save_cover.stateChanged.connect(self._auto_save)
        self.skip_existing_covers.stateChanged.connect(self._auto_save)
        
        return tab
    
    def _create_pdf_tab(self):
        """创建PDF设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        pdf_group = QGroupBox("📄 PDF封面生成")
        pdf_layout = QVBoxLayout()
        
        self.generate_pdf_covers = QCheckBox("自动为PDF文件生成封面截图")
        self.generate_pdf_covers.setToolTip("扫描时自动为PDF文件生成封面图片")
        pdf_layout.addWidget(self.generate_pdf_covers)
        
        q_layout = QHBoxLayout()
        q_layout.addWidget(QLabel("封面质量:"))
        self.pdf_cover_quality = QComboBox()
        self.pdf_cover_quality.addItem("低质量 (快速)", "0")
        self.pdf_cover_quality.addItem("中等质量", "1")
        self.pdf_cover_quality.addItem("高质量 (较慢)", "2")
        q_layout.addWidget(self.pdf_cover_quality)
        q_layout.addStretch()
        pdf_layout.addLayout(q_layout)
        
        batch_pdf_btn = QPushButton("📦 批量生成所有PDF封面")
        batch_pdf_btn.clicked.connect(self.batch_generate_pdf_covers)
        pdf_layout.addWidget(batch_pdf_btn)
        
        pdf_group.setLayout(pdf_layout)
        layout.addWidget(pdf_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        
        # 修改即保存
        self.generate_pdf_covers.stateChanged.connect(self._auto_save)
        self.pdf_cover_quality.currentIndexChanged.connect(self._auto_save)
        
        return tab
    
    def _create_display_tab(self):
        """创建显示设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        file_group = QGroupBox("📂 文件列表显示")
        file_layout = QVBoxLayout()
        
        fm_layout = QHBoxLayout()
        fm_layout.addWidget(QLabel("文件列显示:"))
        self.file_display_mode = QComboBox()
        self.file_display_mode.addItem("显示所有文件", "all")
        self.file_display_mode.addItem("仅显示图片", "images")
        self.file_display_mode.addItem("仅显示视频", "videos")
        self.file_display_mode.addItem("仅显示文档", "documents")
        self.file_display_mode.addItem("隐藏文件", "none")
        fm_layout.addWidget(self.file_display_mode)
        fm_layout.addStretch()
        file_layout.addLayout(fm_layout)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        
        # 修改即保存
        self.file_display_mode.currentIndexChanged.connect(self._auto_save)
        
        return tab
    
    def _create_server_tab(self):
        """创建服务器设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        server_group = QGroupBox("🌐 Web服务器")
        server_layout = QVBoxLayout()
        
        self.auto_start_server = QCheckBox("启动时自动开启Web服务器")
        self.auto_start_server.setToolTip("程序启动时自动启动Web服务器")
        server_layout.addWidget(self.auto_start_server)
        
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("服务器端口:"))
        self.server_port = QSpinBox()
        self.server_port.setMinimum(1)
        self.server_port.setMaximum(65535)
        self.server_port.setValue(8080)
        self.server_port.setToolTip("Web服务器监听端口号")
        port_layout.addWidget(self.server_port)
        port_layout.addStretch()
        server_layout.addLayout(port_layout)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        
        # 修改即保存
        self.auto_start_server.stateChanged.connect(self._auto_save)
        self.server_port.valueChanged.connect(self._auto_save)
        
        return tab

    def _debounce_save(self):
        """QLineEdit 输入防抖：300ms 无输入后自动保存"""
        self._save_timer.start(300)
    
    def _auto_save(self, *_):
        """立即保存（用于 QSpinBox/QCheckBox/QComboBox）"""
        if hasattr(self, '_loading') and self._loading:
            return
        self._save_settings_silent()
    
    def _save_settings_silent(self):
        """静默保存，不弹窗"""
        if not self.user_manager.current_db_path:
            return
        try:
            self.save_settings(silent=True)
            self._save_status.setText("✅ 已自动保存")
            self._save_status.setStyleSheet("color: #4CAF50; font-size: 11px;")
            QTimer.singleShot(2000, lambda: self._save_status.setText("💡 修改即自动保存"))
        except Exception as e:
            self._save_status.setText(f"❌ 保存失败: {e}")
            self._save_status.setStyleSheet("color: #F44336; font-size: 11px;")

    def batch_save_all_covers(self):
        """批量保存所有封面"""
        self.parent().batch_save_all_covers_threaded()

    def batch_save_missing_covers(self):
        """只保存缺失封面 - 改为使用多线程"""
        self.parent().batch_save_missing_covers_threaded()

    def get_setting(self, key, default=None):
        """安全获取设置值 - SettingsDialog 专用版本"""
        if not self.user_manager.current_db_path:
            return default
        
        conn = None
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = cursor.fetchone()
            if result:
                return result[0]
            return default
        except Exception as e:
            print(f"[ERROR] 获取设置 {key} 时出错: {e}")
            return default
        finally:
            if conn:
                conn.close()
    


    def load_settings(self):
        """加载设置 - 增强版本，支持端口冲突检测"""
        self._loading = True  # 防止加载时触发自动保存
        if not self.user_manager.current_db_path:
            return
        
        conn = sqlite3.connect(self.user_manager.current_db_path)
        cursor = conn.cursor()
        
        # 获取扫描间隔
        cursor.execute("SELECT value FROM settings WHERE key = 'scan_interval'")
        result = cursor.fetchone()
        if result:
            try:
                minutes = int(result[0]) // 60
                self.scan_interval.setValue(minutes)
            except:
                pass
        
        # 获取自动扫描设置
        cursor.execute("SELECT value FROM settings WHERE key = 'auto_scan'")
        result = cursor.fetchone()
        if result:
            self.auto_scan.setChecked(result[0] == "1")
    
        # 获取增量扫描设置 ===
        cursor.execute("SELECT value FROM settings WHERE key = 'incremental_scan'")
        result = cursor.fetchone()
        if result:
            self.incremental_scan.setChecked(result[0] == "1")
        else:
            self.incremental_scan.setChecked(True)  # 默认启用
    
        # 获取包含过滤
        cursor.execute("SELECT value FROM settings WHERE key = 'include_filter'")
        result = cursor.fetchone()
        if result:
            self.include_filter.setText(result[0])
        
        # 获取排除过滤
        cursor.execute("SELECT value FROM settings WHERE key = 'exclude_filter'")
        result = cursor.fetchone()
        if result:
            self.exclude_filter.setText(result[0])
        
        # 获取扫描模式设置
        cursor.execute("SELECT value FROM settings WHERE key = 'scan_mode'")
        result = cursor.fetchone()
        if result:
            mode = result[0]
            index = self.scan_mode.findData(mode)
            if index >= 0:
                self.scan_mode.setCurrentIndex(index)
        
        # 获取跳过空白目录设置
        cursor.execute("SELECT value FROM settings WHERE key = 'skip_empty_dirs'")
        result = cursor.fetchone()
        if result:
            self.skip_empty_dirs.setChecked(result[0] == "1")
        else:
            self.skip_empty_dirs.setChecked(True)
        
        # 获取封面保存模式
        cursor.execute("SELECT value FROM settings WHERE key = 'cover_save_mode'")
        result = cursor.fetchone()
        if result:
            mode = result[0]
            index = self.cover_save_mode.findData(mode)
            if index >= 0:
                self.cover_save_mode.setCurrentIndex(index)
        else:
            self.cover_save_mode.setCurrentIndex(0)
        
        # 获取封面保存目录
        cursor.execute("SELECT value FROM settings WHERE key = 'cover_save_dir'")
        result = cursor.fetchone()
        if result:
            self.cover_save_dir.setText(result[0])
        
        # 获取扫描时保存封面设置
        cursor.execute("SELECT value FROM settings WHERE key = 'scan_save_cover'")
        result = cursor.fetchone()
        if result:
            self.scan_save_cover.setChecked(result[0] == "1")
        else:
            self.scan_save_cover.setChecked(False)
        
        # 获取封面备份存在则跳过设置
        cursor.execute("SELECT value FROM settings WHERE key = 'skip_existing_covers'")
        result = cursor.fetchone()
        if result:
            self.skip_existing_covers.setChecked(result[0] == "1")
        else:
            self.skip_existing_covers.setChecked(True)
        
        # 获取自动启动服务器设置
        cursor.execute("SELECT value FROM settings WHERE key = 'auto_start_server'")
        result = cursor.fetchone()
        if result:
            self.auto_start_server.setChecked(result[0] == "1")
        else:
            self.auto_start_server.setChecked(True)
        
        # 获取PDF封面设置
        cursor.execute("SELECT value FROM settings WHERE key = 'generate_pdf_covers'")
        result = cursor.fetchone()
        if result:
            self.generate_pdf_covers.setChecked(result[0] == "1")
        else:
            self.generate_pdf_covers.setChecked(True)
        
        cursor.execute("SELECT value FROM settings WHERE key = 'pdf_cover_quality'")
        result = cursor.fetchone()
        if result:
            quality = result[0]
            index = self.pdf_cover_quality.findData(quality)
            if index >= 0:
                self.pdf_cover_quality.setCurrentIndex(index)
        else:
            self.pdf_cover_quality.setCurrentIndex(1)
        
        # 获取服务器端口设置 - 新增实际可用端口检测
        cursor.execute("SELECT value FROM settings WHERE key = 'server_port'")
        result = cursor.fetchone()
        saved_port = 8080  # 默认端口
        if result:
            try:
                saved_port = int(result[0])
            except (ValueError, TypeError):
                saved_port = 8080
        
        # 检查保存的端口是否可用，如果不可用则查找可用端口
        actual_port = self.get_actual_available_port(saved_port)
        
        # 设置端口控件的值（使用保存的端口，而不是实际端口，让用户知道期望的端口）
        self.server_port.setValue(saved_port)
        
        # 如果端口发生了变化，显示提示信息
        if actual_port != saved_port:
            # 创建一个只读的提示标签
            port_note = QLabel(f"⚠️ 注意: 端口 {saved_port} 已被占用，下次启动时将自动使用端口 {actual_port}")
            port_note.setStyleSheet("color: #ff9800; font-size: 11px; margin-top: 5px;")
            port_note.setWordWrap(True)
            
            # 查找端口设置所在的布局并添加提示
            # 这里简化处理，在状态栏显示提示
            if hasattr(self, 'parent') and self.parent():
                self.parent().update_status_bar(f"端口 {saved_port} 已被占用，将使用端口 {actual_port}", 5000)
        
        # 获取文件显示模式设置
        cursor.execute("SELECT value FROM settings WHERE key = 'file_display_mode'")
        result = cursor.fetchone()
        if result:
            mode = result[0]
            index = self.file_display_mode.findData(mode)
            if index >= 0:
                self.file_display_mode.setCurrentIndex(index)
        else:
            self.file_display_mode.setCurrentIndex(0)
        
        conn.close()
        self._loading = False  # 加载完成，恢复自动保存

    def get_actual_available_port(self, desired_port):
        """获取实际可用的端口号"""
        import socket
        
        max_attempts = 100
        for port in range(desired_port, desired_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('0.0.0.0', port))
                    return port
            except OSError:
                # 端口被占用，继续尝试
                continue
        
        # 如果找不到可用端口，返回期望的端口
        return desired_port

    def save_settings(self, silent=False):
        """保存设置 - 增强版本，支持端口冲突处理"""
        if not self.user_manager.current_db_path:
            return
        
        conn = sqlite3.connect(self.user_manager.current_db_path)
        cursor = conn.cursor()
        
        try:
            # 保存扫描间隔 (转换为秒)
            scan_interval_seconds = self.scan_interval.value() * 60
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("scan_interval", str(scan_interval_seconds))
            )
            
            # 保存自动扫描设置
            auto_scan = "1" if self.auto_scan.isChecked() else "0"
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("auto_scan", auto_scan)
            )
        
            # 保存增量扫描设置 ===
            incremental_scan = "1" if self.incremental_scan.isChecked() else "0"
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("incremental_scan", incremental_scan)
            )
        
            # 保存包含过滤
            include_filter = self.include_filter.text().strip()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("include_filter", include_filter)
            )
            
            # 保存排除过滤
            exclude_filter = self.exclude_filter.text().strip()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("exclude_filter", exclude_filter)
            )
            
            # 保存扫描模式
            scan_mode = self.scan_mode.currentData()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("scan_mode", scan_mode)
            )
            
            # 保存跳过空白目录设置
            skip_empty_dirs = "1" if self.skip_empty_dirs.isChecked() else "0"
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("skip_empty_dirs", skip_empty_dirs)
            )
            
            # 保存封面保存模式
            cover_save_mode = self.cover_save_mode.currentData()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("cover_save_mode", cover_save_mode)
            )
            
            # 保存封面保存目录
            cover_save_dir = self.cover_save_dir.text().strip()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("cover_save_dir", cover_save_dir)
            )
            
            # 保存扫描时保存封面设置
            scan_save_cover = "1" if self.scan_save_cover.isChecked() else "0"
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("scan_save_cover", scan_save_cover)
            )
            
            # 保存封面备份存在则跳过设置
            skip_existing_covers = "1" if self.skip_existing_covers.isChecked() else "0"
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("skip_existing_covers", skip_existing_covers)
            )
            
            # 保存自动启动服务器设置
            auto_start_server = "1" if self.auto_start_server.isChecked() else "0"
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("auto_start_server", auto_start_server)
            )
            
            # 保存PDF封面设置
            generate_pdf_covers = "1" if self.generate_pdf_covers.isChecked() else "0"
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("generate_pdf_covers", generate_pdf_covers)
            )
            
            pdf_cover_quality = self.pdf_cover_quality.currentData()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("pdf_cover_quality", pdf_cover_quality)
            )
            
            # 保存服务器端口设置 - 增强端口冲突处理
            desired_port = self.server_port.value()
            old_port = self.get_current_server_port()
            
            # 检查端口是否可用
            port_available, available_port = self.check_port_availability(desired_port)
            
            if not port_available:
                # 端口被占用，显示警告并询问
                reply = QMessageBox.question(
                    self, "端口已被占用",
                    f"端口 {desired_port} 已被其他程序占用。\n\n"
                    f"建议使用端口 {available_port}，或者手动选择其他端口。\n\n"
                    f"是否保存为端口 {available_port}？\n"
                    f"（选择“否”将保持原端口设置）",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    # 使用可用端口
                    final_port = available_port
                    self.server_port.setValue(final_port)  # 更新界面显示
                    QMessageBox.information(self, "端口已调整", 
                                        f"端口已自动调整为 {final_port}，该端口当前可用。")
                else:
                    # 保持原端口（保存到数据库但不期望立即生效）
                    final_port = desired_port
                    QMessageBox.warning(self, "端口冲突", 
                                    f"端口 {desired_port} 已被占用，保存后将无法启动服务器。\n"
                                    f"请手动停止占用该端口的程序，或稍后更改端口设置。")
            else:
                final_port = desired_port
            
            # 保存端口设置
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("server_port", str(final_port))
            )
            
            # 保存文件显示模式设置
            file_display_mode = self.file_display_mode.currentData()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("file_display_mode", file_display_mode)
            )
            
            conn.commit()
            
            # 验证保存结果
            self.verify_settings_saved()
            
            # 处理服务器重启（只有当端口真正变化时）
            if old_port != final_port and hasattr(self, 'parent') and self.parent():
                # 检查新端口是否可用
                if self.check_port_availability(final_port)[0]:
                    self.parent().restart_server_if_needed(old_port, final_port)
                else:
                    QMessageBox.warning(self, "端口不可用", 
                                    f"端口 {final_port} 当前不可用，设置已保存但服务器无法启动。\n"
                                    f"请手动停止占用该端口的程序后重启服务器。")
            
            if not silent:
                QMessageBox.information(self, "保存成功", "设置已成功保存")
                self.accept()
            
        except Exception as e:
            print(f"[DEBUG] 保存设置时出错:{e}")
            QMessageBox.critical(self, "保存失败", f"保存设置时出错:\n{e}")
        finally:
            conn.close()

    def get_current_server_port(self):
        """获取当前服务器端口"""
        if not self.user_manager.current_db_path:
            return 8080
        
        conn = None
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'server_port'")
            result = cursor.fetchone()
            if result:
                return int(result[0])
            return 8080
        except Exception:
            return 8080
        finally:
            if conn:
                conn.close()

    def check_port_availability(self, port):
        """检查端口是否可用，如果不可用返回下一个可用端口"""
        import socket
        
        max_attempts = 100
        for p in range(port, port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('0.0.0.0', p))
                    return True, p
            except OSError:
                continue
        
        return False, port

    def verify_settings_saved(self):
        """验证设置是否真正保存成功"""
        verification_results = {
            'success': [],
            'warning': [],
            'error': []
        }
        
        conn = None
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            
            # 验证的关键设置列表
            critical_settings = [
                'scan_interval', 
                'auto_scan', 
                'scan_mode',
                'include_filter',
                'exclude_filter',
                'cover_save_mode',  
                'cover_save_dir',
                'server_port'  # 新增验证端口设置
            ]
            
            for key in critical_settings:
                try:
                    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
                    result = cursor.fetchone()
                    
                    if result:
                        verification_results['success'].append(f"设置 {key} 已保存: {result[0]}")
                    else:
                        verification_results['error'].append(f"设置 {key} 未找到")
                except Exception as e:
                    verification_results['error'].append(f"查询设置 {key} 时出错: {e}")
                    
            # 特别验证端口设置
            if 'server_port' in [s.split(' ')[1] for s in verification_results['success']]:
                cursor.execute("SELECT value FROM settings WHERE key = 'server_port'")
                port_result = cursor.fetchone()
                if port_result:
                    saved_port = int(port_result[0])
                    is_available, available_port = self.check_port_availability(saved_port)
                    if not is_available:
                        verification_results['warning'].append(
                            f"端口 {saved_port} 已被占用，服务器可能无法启动。建议使用端口 {available_port}"
                        )
                        
        except Exception as e:
            print(f"[CRITICAL] 验证设置时发生严重错误: {e}")
        finally:
            if conn:
                conn.close()
        
        # 输出验证结果（仅警告和错误）
        if verification_results['warning']:
            print(f"[WARNING] {len(verification_results['warning'])} 个警告")
            for warning in verification_results['warning']:
                print(f"  - {warning}")
        
        if verification_results['error']:
            print(f"[ERROR] {len(verification_results['error'])} 个验证错误")
            for error in verification_results['error']:
                print(f"  - {error}")
        
        return verification_results


    def _save_as_preset(self):
        """将当前设置保存为预设方案"""
        name, ok = QInputDialog.getText(self, "保存方案", "方案名称:")
        if ok and name.strip():
            # 先保存当前设置
            self.save_settings(silent=True)
            # 读取所有当前设置
            presets = self.user_manager.get_presets()
            settings = {}
            keys = ["scan_interval", "auto_scan", "incremental_scan", "scan_mode",
                    "skip_empty_dirs", "include_filter", "exclude_filter",
                    "cover_save_mode", "cover_save_dir", "scan_save_cover",
                    "skip_existing_covers", "generate_pdf_covers", "pdf_cover_quality",
                    "auto_start_server", "server_port", "file_display_mode"]
            for key in keys:
                val = self.get_setting(key, "")
                settings[key] = val
            presets[name.strip()] = settings
            self.user_manager.save_presets(presets)
            QMessageBox.information(self, "成功", f"方案 '{name}' 已保存")
    
    def browse_cover_save_dir(self):
        """浏览选择封面保存目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择封面保存目录", 
            self.cover_save_dir.text() or os.path.expanduser("~"),
            options=QFileDialog.DontUseNativeDialog
        )
        if directory:
            self.cover_save_dir.setText(directory)

    def get_cover_save_directory(self):
        """获取封面保存目录"""
        cover_save_dir = self.cover_save_dir.text().strip()
        
        # 如果用户未设置，使用默认目录
        if not cover_save_dir:
            # 使用用户主目录下的"目录封面"文件夹，避免权限问题
            default_dir = os.path.join(os.path.expanduser("~"), "目录封面")
            return default_dir
        
        return cover_save_dir

    def batch_generate_pdf_covers(self):
        """批量生成所有PDF封面 - 改为使用多线程"""
        self.parent().batch_generate_pdf_covers_threaded()

# 封面处理工作线程类
class CoverProcessingWorker(QObject):
    """封面处理工作线程"""
    
    # 信号定义 - 使用Signal替代pyqtSignal
    progress_updated = Signal(int, str)  # 进度值, 状态消息
    cover_saved = Signal(str, str)  # 目录路径, 封面路径
    finished = Signal()
    error_occurred = Signal(str, str)  # 错误消息, 目录路径
    
    def __init__(self, main_app, directories, operation_type="save_all"):
        super().__init__()
        self.main_app = main_app
        self.directories = directories
        self.operation_type = operation_type  # "save_all", "save_missing", "generate_pdf"
        self.is_running = True
        
    def stop(self):
        """停止处理"""
        self.is_running = False
    
    def process_covers(self):
        """处理封面 - 主处理方法"""
        try:
            total_dirs = len(self.directories)
            if total_dirs == 0:
                self.finished.emit()
                return
            
            # 获取封面保存设置
            cover_save_mode, cover_save_dir = self.main_app.get_cover_save_settings()
            skip_existing = self.main_app.get_setting('skip_existing_covers', '1') == '1'
            
            saved_count = 0
            skipped_count = 0
            error_count = 0
            
            for i, dir_info in enumerate(self.directories):
                if not self.is_running:
                    break
                    
                # 更新进度
                progress = int((i + 1) / total_dirs * 100)
                status_msg = f"处理封面中... ({i+1}/{total_dirs})"
                self.progress_updated.emit(progress, status_msg)
                
                try:
                    if dir_info.get("is_directory", 1) == 1:  # 只处理目录
                        dir_path = dir_info["path"]
                        
                        if self.operation_type == "save_missing":
                            # 检查是否已存在封面
                            expected_path = self.main_app.get_expected_cover_path(
                                dir_path, cover_save_dir, cover_save_mode
                            )
                            if expected_path and os.path.exists(expected_path):
                                skipped_count += 1
                                continue
                        
                        # 查找封面图片
                        cover_path = self.main_app.find_cover_image(dir_path)
                        if cover_path and os.path.exists(cover_path):
                            # 保存封面
                            if self.main_app.save_cover_image(dir_path, cover_path):
                                saved_count += 1
                                self.cover_saved.emit(dir_path, cover_path)
                            else:
                                error_count += 1
                        else:
                            # 对于PDF文件，尝试生成封面
                            if self.operation_type in ["save_all", "save_missing"]:
                                pdf_cover_generated = self.try_generate_pdf_cover(dir_path)
                                if pdf_cover_generated:
                                    saved_count += 1
                                else:
                                    error_count += 1
                    else:
                        # 处理文件封面
                        file_path = dir_info["path"]
                        if self.should_generate_file_cover(file_path):
                            if self.generate_file_cover(file_path):
                                saved_count += 1
                            else:
                                error_count += 1
                                
                except Exception as e:
                    error_count += 1
                    self.error_occurred.emit(str(e), dir_info.get("path", "unknown"))
                    print(f"[COVER ERROR] 处理封面失败 {dir_info.get('path', 'unknown')}: {e}")
            
            # 完成处理
            final_msg = f"封面处理完成: 保存 {saved_count}, 跳过 {skipped_count}, 错误 {error_count}"
            self.progress_updated.emit(100, final_msg)
            self.finished.emit()
            
        except Exception as e:
            self.error_occurred.emit(f"封面处理过程出错: {e}", "global")
            self.finished.emit()
    
    def try_generate_pdf_cover(self, dir_path):
        """尝试为PDF文件生成封面"""
        # 检查目录中是否有PDF文件
        for file in os.listdir(dir_path):
            if file.lower().endswith('.pdf'):
                pdf_path = os.path.join(dir_path, file)
                return self.main_app.generate_pdf_cover(pdf_path)
        return False
    
    def should_generate_file_cover(self, file_path):
        """判断是否应该为文件生成封面"""
        if file_path.lower().endswith('.pdf'):
            return True
        # 可以扩展其他文件类型
        return False
    
    def generate_file_cover(self, file_path):
        """为文件生成封面"""
        if file_path.lower().endswith('.pdf'):
            return self.main_app.generate_pdf_cover(file_path)
        return False

class PDFCoverGenerationWorker(QObject):
    """PDF封面生成工作线程"""
    
    progress_updated = Signal(int, str)
    cover_generated = Signal(str, str)
    finished = Signal(int, int)  # 成功数, 失败数
    error_occurred = Signal(str)
    
    def __init__(self, main_app, pdf_files):
        super().__init__()
        self.main_app = main_app
        self.pdf_files = pdf_files
        self.is_running = True
        self.lock = Lock()
        
    def stop(self):
        """停止生成"""
        with self.lock:
            self.is_running = False
    
    def generate_pdf_covers(self):
        """批量生成PDF封面"""
        try:
            total = len(self.pdf_files)
            if total == 0:
                self.finished.emit(0, 0)
                return
            
            success_count = 0
            error_count = 0
            
            for i, pdf_path in enumerate(self.pdf_files):
                # 检查是否停止
                with self.lock:
                    if not self.is_running:
                        break
                
                # 更新进度
                progress = int((i + 1) / total * 100)
                status_msg = f"生成PDF封面中... ({i+1}/{total})"
                self.progress_updated.emit(progress, status_msg)
                
                try:
                    if self.main_app.generate_pdf_cover(pdf_path):
                        success_count += 1
                        self.cover_generated.emit(pdf_path, "generated")
                    else:
                        error_count += 1
                        
                except Exception as e:
                    error_count += 1
                    self.error_occurred.emit(f"生成PDF封面失败 {pdf_path}: {str(e)}")
            
            # 发送完成信号
            self.finished.emit(success_count, error_count)
            
        except Exception as e:
            self.error_occurred.emit(f"批量PDF封面生成失败: {str(e)}")
            self.finished.emit(0, 0)

class ThreadPoolManager:
    """线程池管理器"""
    
    def __init__(self, max_workers=None):
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.futures = []
        
    def submit_task(self, fn, *args, **kwargs):
        """提交任务到线程池"""
        future = self.executor.submit(fn, *args, **kwargs)
        self.futures.append(future)
        return future
    
    def shutdown(self, wait=True):
        """关闭线程池"""
        self.executor.shutdown(wait=wait)
        self.futures.clear()
    
    def cancel_all(self):
        """取消所有任务"""
        for future in self.futures:
            future.cancel()
        self.futures.clear()

class DirectoryScanWorker(QObject):
    """目录扫描工作线程 - 支持增量扫描"""
    
    # 信号定义
    progress_updated = Signal(int, str)
    directory_scanned = Signal(dict)       # 保留单个信号（兼容），但优先使用批量信号
    directory_batch_scanned = Signal(list)  # 批量发送扫描结果，减少信号洪泛
    scan_finished = Signal(list)
    error_occurred = Signal(str)
    
    # 批量发送阈值
    BATCH_SIZE = 100
    BATCH_FLUSH_INTERVAL = 0.1  # 秒

    # 【性能优化】扫描状态落盘策略（消除原 save_scan_state 的 O(N^2) 整读+整写）
    STATE_FLUSH_INTERVAL = 2.0    # 秒，增量状态最长滞留内存时间
    STATE_FLUSH_UPDATES = 500     # 未落盘的脏目录数达到该值即落盘

    def __init__(self, scan_path, scan_depth, scan_mode="directories", main_app=None):
        super().__init__()
        self.scan_path = scan_path
        self.scan_depth = scan_depth
        self.scan_mode = scan_mode
        self.main_app = main_app
        self.is_running = True
        self.state_file = None  # 状态文件路径
        
        # 批量发送缓冲区
        self._batch_buffer = []
        self._last_flush_time = time.time()
        
        # 【性能优化】扫描状态内存缓存：整个 state 文件只读一次、只写整块
        self._state_cache = None      # 惰性加载：None=尚未读取，dict=已加载的完整状态
        self._state_dirty = False     # 内存中是否有未落盘的改动
        self._state_dirty_count = 0   # 未落盘的脏目录数（触发阈值落盘）
        self._state_dropped = False   # 是否已显式丢弃状态文件（防止 force 落盘复活旧基线）
        self._last_state_flush = time.time()
        
        # 设置状态文件路径
        if main_app and main_app.user_manager.current_db_path:
            state_dir = os.path.join(main_app.app_dir, "scan_states")
            os.makedirs(state_dir, exist_ok=True)
            safe_path = scan_path.replace(':', '_').replace('\\', '_').replace('/', '_')
            self.state_file = os.path.join(state_dir, f"{safe_path}.state")
        
    def stop(self):
        """停止扫描"""
        self.is_running = False
    
    def _add_to_batch(self, item):
        """将扫描结果加入批量缓冲区，达到阈值时自动发送"""
        self._batch_buffer.append(item)
        now = time.time()
        # 达到批量大小或超过刷新间隔时发送
        if len(self._batch_buffer) >= self.BATCH_SIZE or (now - self._last_flush_time) >= self.BATCH_FLUSH_INTERVAL:
            self._flush_batch()
    
    def _flush_batch(self):
        """强制刷新批量缓冲区"""
        if self._batch_buffer:
            batch = self._batch_buffer
            self._batch_buffer = []
            self._last_flush_time = time.time()
            self.directory_batch_scanned.emit(batch)
    
    def scan_directory(self):
        """执行目录扫描（根据模式选择方法）"""
        try:
            use_incremental = True
            if self.main_app:
                use_incremental = self.main_app.get_setting('incremental_scan', '1') == '1'
            
            if use_incremental:
                directories = self.scan_directory_incremental(self.scan_path, self.scan_depth)
            else:
                # 全量扫描：清除旧状态文件，确保下次增量扫描从干净基线开始
                # 【修复】原实现只删文件、不清内存缓存，随后 finally 的
                # _flush_state(force=True) 会把刚删掉的状态（旧基线）重新写回，
                # 导致全量扫描后状态文件"复活"，下次增量扫描拿旧基线跳过应重扫内容。
                # 统一走 _drop_state_file()：删文件 + 清缓存 + 复位脏标记。
                self._drop_state_file()
                if self.scan_mode == "directories":
                    directories = self.scan_directories_only(self.scan_path, self.scan_depth)
                elif self.scan_mode == "files":
                    directories = self.scan_files_only(self.scan_path, self.scan_depth)
                else:
                    dirs = self.scan_directories_only(self.scan_path, self.scan_depth)
                    files = self.scan_files_only(self.scan_path, self.scan_depth)
                    directories = dirs + files
            
            # 刷新剩余批量数据
            self._flush_batch()
            
            self.scan_finished.emit(directories)
            
        except Exception as e:
            self.error_occurred.emit(f"扫描失败: {str(e)}")
        finally:
            # 【性能优化 + 可靠性兜底】扫描收尾时无条件把内存中的增量状态落盘。
            # 正常结束、抛异常、以及被 stop() 中断都会走到这里，确保状态不静默丢失。
            self._flush_state(force=True)
    
    def scan_directory_incremental(self, path=None, depth=None):
        """增量扫描目录 - 只处理变化的文件和目录"""
        # 如果没有传入参数，使用实例变量
        if path is None:
            path = self.scan_path
        if depth is None:
            depth = self.scan_depth
        
        directories = []
        
        if depth < 0 or not self.is_running:
            return directories
        
        try:
            # 获取跳过空白目录设置
            skip_empty_dirs = True
            if self.main_app:
                skip_empty_dirs = self.main_app.get_setting('skip_empty_dirs', '1') == '1'
            
            # 获取上次扫描信息
            last_scan_info = self.load_scan_state(path)
            
            # 获取扫描模式（增量扫描也需遵守）
            scan_mode = self.scan_mode
            if self.main_app:
                scan_mode = self.main_app.get_setting('scan_mode', 'directories')
            only_dirs = (scan_mode == "directories")
            only_files = (scan_mode == "files")
            
            # 扫描当前目录
            current_items = {}
            self.progress_updated.emit(0, f"增量扫描: {path}")
            
            for entry in os.scandir(path):
                if not self.is_running:
                    break
                
                try:
                    is_dir = entry.is_dir(follow_symlinks=False)
                    # 按扫描模式过滤
                    if only_files and is_dir:
                        continue
                    if only_dirs and not is_dir:
                        continue
                    stat = entry.stat()
                    current_items[entry.name] = {
                        'path': entry.path,
                        'mtime': stat.st_mtime,
                        'size': stat.st_size,
                        'is_dir': is_dir
                    }
                except (PermissionError, OSError) as e:
                    print(f"无法访问 {entry.path}: {e}")
                    continue
            
            # 对比变化
            if last_scan_info:
                # 检查新增和修改的项
                for name, info in current_items.items():
                    if not self.is_running:
                        break
                    
                    if name not in last_scan_info:
                        # 新增项（按扫描模式过滤）
                        if only_files and info['is_dir']:
                            continue
                        if only_dirs and not info['is_dir']:
                            continue
                        if info['is_dir']:
                            # 检查是否跳过空白目录
                            if skip_empty_dirs and info['is_dir']:
                                try:
                                    dir_contents = os.listdir(info['path'])
                                    visible_contents = [item for item in dir_contents 
                                                    if not item.startswith('.') and not item.startswith('~')]
                                    if not visible_contents:
                                        continue
                                except:
                                    pass
                            
                            dir_info = self.get_item_info(info['path'], True)
                            if dir_info:
                                directories.append(dir_info)
                                self._add_to_batch(dir_info)
                        else:
                            file_info = self.get_item_info(info['path'], False)
                            if file_info:
                                directories.append(file_info)
                                self._add_to_batch(file_info)
                    else:
                        last_info = last_scan_info[name]
                        # 检查修改（修改时间变化或大小变化）
                        if (abs(info['mtime'] - last_info.get('mtime', 0)) > 0.1 or
                            info['size'] != last_info.get('size', 0)):
                            # 修改项（按扫描模式过滤）
                            if only_files and info['is_dir']:
                                continue
                            if only_dirs and not info['is_dir']:
                                continue
                            if info['is_dir']:
                                dir_info = self.get_item_info(info['path'], True)
                                if dir_info:
                                    directories.append(dir_info)
                                    self._add_to_batch(dir_info)
                            else:
                                file_info = self.get_item_info(info['path'], False)
                                if file_info:
                                    directories.append(file_info)
                                    self._add_to_batch(file_info)
                
                # 检查删除的项（可选：标记为不存在）
                for name, last_info in last_scan_info.items():
                    if not self.is_running:
                        break
                    
                    if name not in current_items:
                        # 按扫描模式过滤删除项
                        is_dir = last_info.get('is_dir', True)
                        if only_files and is_dir:
                            continue
                        if only_dirs and not is_dir:
                            continue
                        directories.append({
                            "name": name,
                            "path": last_info['path'],
                            "created_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "last_modified": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "directory_exists": 0,
                            "is_main_dir": 0,
                            "is_directory": 1 if last_info.get('is_dir', True) else 0
                        })
            else:
                # 首次扫描，添加所有项（按扫描模式过滤）
                for name, info in current_items.items():
                    if not self.is_running:
                        break
                    
                    if only_files and info['is_dir']:
                        continue
                    if only_dirs and not info['is_dir']:
                        continue
                    
                    if info['is_dir']:
                        # 检查是否跳过空白目录
                        if skip_empty_dirs and info['is_dir']:
                            try:
                                dir_contents = os.listdir(info['path'])
                                visible_contents = [item for item in dir_contents 
                                                if not item.startswith('.') and not item.startswith('~')]
                                if not visible_contents:
                                    continue
                            except:
                                pass
                        
                        dir_info = self.get_item_info(info['path'], True)
                        if dir_info:
                            directories.append(dir_info)
                            self._add_to_batch(dir_info)
                    else:
                        file_info = self.get_item_info(info['path'], False)
                        if file_info:
                            directories.append(file_info)
                            self._add_to_batch(file_info)
            
            # 递归扫描子目录（增量模式）
            if depth > 0:
                for entry in os.scandir(path):
                    if not self.is_running:
                        break
                    
                    if entry.is_dir(follow_symlinks=False):
                        try:
                            # 检查是否需要递归扫描该子目录
                            if last_scan_info:
                                sub_last_info = last_scan_info.get(entry.name)
                                if sub_last_info and not self.has_directory_changed(entry.path, sub_last_info):
                                    continue
                            
                            sub_dirs = self.scan_directory_incremental(entry.path, depth - 1)
                            directories.extend(sub_dirs)
                        except (PermissionError, OSError):
                            continue
            
            # 刷新批量缓冲区
            self._flush_batch()
            # 保存扫描状态
            self.save_scan_state(path, current_items)
            
            return directories
            
        except Exception as e:
            self.error_occurred.emit(f"增量扫描失败 {path}: {str(e)}")
            return directories
    
    def has_directory_changed(self, dir_path, last_info):
        """检查目录是否有变化"""
        try:
            stat = os.stat(dir_path)
            current_mtime = stat.st_mtime
            last_mtime = last_info.get('mtime', 0)
            return abs(current_mtime - last_mtime) > 0.1
        except:
            return True
    
    def _drop_state_file(self):
        """【修复】删除状态文件并同步失效内存缓存（删文件 + 清缓存 + 复位脏标记）。

        统一处理"丢弃既有基线"的两种场景，保证两处语义自洽：
        1. 全量扫描（incremental_scan=0）：丢弃旧基线，下次增量从干净状态开始；
        2. _load_state_file 读到版本不符/损坏文件：同样丢弃。
        
        关键点：_state_cache 置为**空状态字典**（而非 None）。
        - 置 None 会让后续 _load_state_file 重新去 stat/读已不存在的文件；
        - 置空字典则让 `if self._state_cache is not None` 直接短路，语义与
          "无历史基线"完全一致。
        同时复位 _state_dirty / _state_dirty_count，并置 _state_dropped=True，
        使收尾的 _flush_state(force=True) 不会凭 force 绕过脏检查、
        把刚被丢弃的旧基线重新写回（这正是原先"状态文件复活"的根因）。
        """
        if self.state_file:
            try:
                if os.path.exists(self.state_file):
                    os.remove(self.state_file)
            except Exception:
                pass
        self._state_cache = {'__version__': 2}
        self._state_dirty = False
        self._state_dirty_count = 0
        self._state_dropped = True
        self._last_state_flush = time.time()

    def _load_state_file(self):
        """【性能优化】把整个 state 文件读入内存（每次扫描进程只读一次）。

        文件格式保持不变：{'__version__': 2, '<path>': {name: {...}}, ...}。
        老文件（含无版本标记的）仍然按原逻辑处理：版本不对就删除并返回空状态。
        """
        if self._state_cache is not None:
            return self._state_cache
        
        full_state = {'__version__': 2}
        if self.state_file and os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'rb') as f:
                    loaded = pickle.load(f)
                if isinstance(loaded, dict) and loaded.get('__version__') == 2:
                    full_state = loaded
                else:
                    # 与原先 load_scan_state 的版本检查行为保持一致：
                    # 丢弃文件；用 _drop_state_file 统一处理，保证缓存自洽
                    # （不会出现"删了文件但缓存仍持旧内容"）。
                    self._drop_state_file()
                    return self._state_cache
            except Exception:
                full_state = {'__version__': 2}
        self._state_cache = full_state
        return self._state_cache
    
    def load_scan_state(self, path):
        """加载指定路径的扫描状态（按 path 索引，递归不覆盖）
        
        【性能优化】原实现每次调用都整读整个 pickle 文件；现在改为首次读取后
        常驻内存（self._state_cache），后续调用是纯字典查询，零 I/O。
        注意：返回的是缓存内的同一个字典对象（与原先每次反序列化出新对象不同），
        调用方只做读取比较，不修改它，因此语义一致。
        """
        if not self.state_file:
            return None
        full_state = self._load_state_file()
        return full_state.get(path, None)
    
    def save_scan_state(self, path, current_items):
        """保存指定路径的扫描状态（按 path 索引，递归不覆盖）
        
        【性能优化】原实现每保存一个目录就"整读整个文件 + 整写整个文件"，
        复杂度 O(N^2)（实测 2.9ms/目录，10000 目录约 28.8s 且持续恶化）。
        现在只把状态写入内存字典，按数量阈值/时间间隔批量落盘，
        并在扫描结束时由 _flush_state(force=True) 兜底，落盘为整块一次性写。
        """
        if not self.state_file:
            return
        
        if self._state_cache is None:
            self._load_state_file()
        self._state_cache[path] = current_items
        
        if not self._state_dirty:
            self._state_dirty = True
        self._state_dirty_count += 1
        # 丢弃基线后又写入了新状态：清除丢弃标记，允许正常落盘
        self._state_dropped = False
        
        now = time.time()
        if (self._state_dirty_count >= self.STATE_FLUSH_UPDATES or
                (now - self._last_state_flush) >= self.STATE_FLUSH_INTERVAL):
            self._flush_state()
    
    def _flush_state(self, force=False):
        """【性能优化】把内存中的扫描状态批量落盘（整块一次写）。

        这是"异常/中断不静默丢状态"的兜底：除了阈值/定时触发，
        扫描收尾（scan_directory 的 finally）会用 force=True 无条件落盘。

        【修复】若本次已显式丢弃过状态文件（_state_dropped），且丢弃后没有再
        写入任何新状态（_state_dirty 仍为 False），则不落盘：
        避免 force=True 绕过脏检查、把刚删掉的旧基线写回去（状态文件复活）。

        【修复 F4】_drop_state_file() 会把 _state_cache 置为**空状态字典**而非
        None，因此下面 `self._state_cache is None` 的短路在"刚丢弃"情形下失效
        （空 dict 不是 None），只剩 _state_dropped 单条守卫。这里补上第二重判据：
        缓存为空状态且非脏 -> 没有任何真实状态可写，直接返回。双重判据互相独立，
        即使将来有人改动 _state_dropped 的置位时机，也不会误写出空/旧基线。
        """
        if not self.state_file or self._state_cache is None:
            return False
        if self._state_dropped and not self._state_dirty:
            return False
        # 【修复 F4】第二重判据：空状态缓存 + 无脏改动 => 无可落盘内容
        if not self._state_dirty and len(self._state_cache) <= 1:
            return False
        if not self._state_dirty and not force:
            return False
        try:
            with open(self.state_file, 'wb') as f:
                pickle.dump(self._state_cache, f)
            self._state_dirty = False
            self._state_dirty_count = 0
            self._state_dropped = False
            self._last_state_flush = time.time()
            return True
        except Exception:
            return False
    
    def scan_directories_only(self, path, depth):
        """仅扫描目录 - 添加空白目录检查"""
        directories = []
        
        if depth < 0 or not self.is_running:
            return directories
        
        try:
            skip_empty_dirs = True
            if self.main_app:
                skip_empty_dirs = self.main_app.get_setting('skip_empty_dirs', '1') == '1'
            
            self.progress_updated.emit(0, f"正在扫描目录: {path}")
            
            for entry in os.scandir(path):
                if not self.is_running:
                    break
                    
                if entry.is_dir(follow_symlinks=False):
                    try:
                        if skip_empty_dirs:
                            dir_contents = os.listdir(entry.path)
                            # 将子目录也算作可见内容
                            has_content = any(
                                not item.startswith('.') and not item.startswith('~')
                                for item in dir_contents
                            )
                            if not has_content:
                                continue
                        
                        dir_info = self.get_directory_info(entry.path)
                        if dir_info:
                            directories.append(dir_info)
                            self._add_to_batch(dir_info)
                    except (PermissionError, OSError) as e:
                        print(f"无法访问目录 {entry.path}: {e}")
                        continue
            
            if depth > 0:
                for entry in os.scandir(path):
                    if not self.is_running:
                        break
                        
                    if entry.is_dir(follow_symlinks=False):
                        try:
                            sub_dirs = self.scan_directories_only(entry.path, depth - 1)
                            directories.extend(sub_dirs)
                        except (PermissionError, OSError):
                            continue
            
            self._flush_batch()
            return directories
            
        except Exception as e:
            print(f"扫描目录失败 {path}: {e}")
            self.error_occurred.emit(f"扫描目录失败 {path}: {str(e)}")
            return directories
    
    def scan_files_only(self, path, depth):
        """仅扫描文件"""
        files = []
        
        if depth < 0 or not self.is_running:
            return files
        
        try:
            self.progress_updated.emit(0, f"正在扫描文件: {path}")
            
            for entry in os.scandir(path):
                if not self.is_running:
                    break
                    
                if entry.is_file():
                    try:
                        file_info = self.get_file_info(entry.path)
                        if file_info:
                            files.append(file_info)
                            self._add_to_batch(file_info)
                    except (PermissionError, OSError) as e:
                        print(f"无法访问文件 {entry.path}: {e}")
                        continue
            
            if depth > 0:
                for entry in os.scandir(path):
                    if not self.is_running:
                        break
                        
                    if entry.is_dir(follow_symlinks=False):
                        try:
                            sub_files = self.scan_files_only(entry.path, depth - 1)
                            files.extend(sub_files)
                        except (PermissionError, OSError):
                            continue
            
            self._flush_batch()
            return files
            
        except Exception as e:
            self.error_occurred.emit(f"扫描文件失败 {path}: {str(e)}")
            return files
    
    def get_item_info(self, item_path, is_directory):
        """获取项目信息（统一方法）"""
        try:
            stat = os.stat(item_path)
            name = os.path.basename(item_path)
            
            return {
                "name": name,
                "path": item_path,
                "created_time": datetime.datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                "last_modified": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "directory_exists": 1,
                "is_main_dir": 0,
                "is_directory": 1 if is_directory else 0
            }
        except Exception as e:
            print(f"获取项目信息失败 {item_path}: {e}")
            return None
    
    def get_directory_info(self, dir_path):
        """获取目录信息（兼容旧代码）"""
        return self.get_item_info(dir_path, True)
    
    def get_file_info(self, file_path):
        """获取文件信息（兼容旧代码）"""
        return self.get_item_info(file_path, False)


class ScanDispatcherWorker(QObject):
    """扫描调度器 - 在单个QThread中使用ThreadPoolExecutor并行扫描多个主目录
    优势：限制并发数(默认4-8)，避免创建过多QThread导致上下文切换开销"""
    
    progress_updated = Signal(int, str)
    error_occurred = Signal(str)
    all_scans_finished = Signal(list)  # 所有扫描完成，发送所有结果
    
    # 最大并发扫描线程数
    MAX_CONCURRENT = min(8, max(4, (os.cpu_count() or 4)))
    
    def __init__(self, main_dirs, scan_mode, use_incremental, main_app):
        super().__init__()
        self.main_dirs = main_dirs
        self.scan_mode = scan_mode
        self.use_incremental = use_incremental
        self.main_app = main_app
        self.is_running = True
        
    def stop(self):
        """停止所有扫描"""
        self.is_running = False
    
    def run(self):
        """主执行方法：在线程池中并行扫描所有主目录"""
        total_dirs = len(self.main_dirs)
        all_directories = []
        scan_lock = Lock()
        completed = [0]  # 用列表包装以便在闭包中修改
        
        def scan_one_directory(dir_info):
            """在线程池中扫描单个主目录"""
            dir_id, path, depth = dir_info
            
            if not self.is_running:
                return []
            
            worker = None
            try:
                print(f"[SCAN] 开始扫描主目录: {path} (深度: {depth})")
                worker = DirectoryScanWorker(path, depth, self.scan_mode, self.main_app)
                
                if self.use_incremental:
                    result = worker.scan_directory_incremental(path, depth)
                else:
                    result = worker.scan_directory()
                
                # 清理worker的批量缓冲区
                worker._flush_batch()
                
                with scan_lock:
                    completed[0] += 1
                    progress = int(completed[0] / total_dirs * 50)
                    self.progress_updated.emit(progress, f"扫描进度: {completed[0]}/{total_dirs}")
                
                return result
                
            except Exception as e:
                error_msg = f"扫描失败 {path}: {str(e)}"
                print(f"[SCAN ERROR] {error_msg}")
                self.error_occurred.emit(error_msg)
                with scan_lock:
                    completed[0] += 1
                return []
            finally:
                # 【修复 F2】增量分支直接调用 scan_directory_incremental，绕过了
                # scan_directory() 里 finally 的 _flush_state(force=True)，只剩
                # 500 条 / 2s 阈值落盘；多主目录扫描走的正是这条路径，进程被强杀
                # 会丢掉未达阈值的尾部改动。这里补上收尾兜底，放在 finally 中
                # 以保证正常结束、抛异常、stop() 三种情形都落盘。
                if worker is not None:
                    try:
                        worker._flush_state(force=True)
                    except Exception as flush_err:
                        print(f"[SCAN WARN] 收尾落盘扫描状态失败 {path}: {flush_err}")
        
        try:
            # 使用ThreadPoolExecutor进行并行扫描
            # 限制并发数，避免磁盘I/O争抢和过多上下文切换
            max_workers = min(self.MAX_CONCURRENT, total_dirs)
            print(f"[SCAN] 使用线程池扫描，最大并发: {max_workers}")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有扫描任务
                future_to_dir = {
                    executor.submit(scan_one_directory, dir_info): dir_info 
                    for dir_info in self.main_dirs
                }
                
                # 收集结果
                for future in as_completed(future_to_dir):
                    if not self.is_running:
                        # 取消剩余任务
                        for f in future_to_dir:
                            f.cancel()
                        break
                    try:
                        result = future.result()
                        if result:
                            all_directories.extend(result)
                    except Exception as e:
                        dir_info = future_to_dir[future]
                        print(f"[SCAN ERROR] 获取扫描结果失败 {dir_info[1]}: {e}")
            
            # 去重
            if all_directories:
                seen = set()
                unique_dirs = []
                for d in all_directories:
                    key = d.get('path', '')
                    if key and key not in seen:
                        seen.add(key)
                        unique_dirs.append(d)
                all_directories = unique_dirs
            
        except Exception as e:
            self.error_occurred.emit(f"扫描调度失败: {str(e)}")
        
        self.all_scans_finished.emit(all_directories)


class DatabaseSaveWorker(QObject):
    """数据库保存工作线程"""
    
    progress_updated = Signal(int, str)
    save_finished = Signal(int, int)  # 成功数量, 失败数量
    error_occurred = Signal(str)
    
    def __init__(self, db_path, directories, root_paths=None):
        super().__init__()
        self.db_path = db_path
        self.directories = directories
        self.root_paths = root_paths or []  # 扫描的根路径，用于清理旧数据
        self.is_running = True
        
    def stop(self):
        """停止保存"""
        self.is_running = False
    
    def save_to_database(self):
        """保存目录信息到数据库 - 流式分批 executemany 优化版"""
        success_count = 0
        error_count = 0
        duplicate_count = 0
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=OFF")
            cursor.execute("PRAGMA cache_size=-8000")
            
            total_dirs = len(self.directories)
            duplicate_paths = set()
            
            # 清理根路径下的旧数据（模式切换后旧条目被清除）
            for root in self.root_paths:
                cursor.execute("DELETE FROM directories WHERE path LIKE ?", (f"{root}%",))
            
            # ===== 流式分批处理 =====
            batch_size = 300
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            for batch_start in range(0, total_dirs, batch_size):
                if not self.is_running:
                    break
                
                batch_end = min(batch_start + batch_size, total_dirs)
                batch_data = []
                
                for i in range(batch_start, batch_end):
                    dir_info = self.directories[i]
                    
                    try:
                        name = dir_info.get("name", "").strip()
                        dir_path = dir_info.get("path", "").strip()
                        
                        if not name or not dir_path:
                            error_count += 1
                            continue
                        
                        if dir_path in duplicate_paths:
                            duplicate_count += 1
                            continue
                        
                        created_time = dir_info.get("created_time")
                        last_modified = dir_info.get("last_modified")
                        
                        if not created_time or not last_modified:
                            error_count += 1
                            continue
                        
                        # 不调用 os.path.exists，信任扫描时已验证
                        batch_data.append((
                            name, dir_path, created_time, last_modified,
                            now_str,
                            dir_info.get("is_main_dir", 0),
                            dir_info.get("is_directory", 1)
                        ))
                        duplicate_paths.add(dir_path)
                        
                    except Exception as e:
                        error_count += 1
                
                # 批量INSERT（INSERT OR REPLACE：新增+更新，支持增量扫描的修改检测）
                if batch_data:
                    try:
                        cursor.executemany("""
                            INSERT OR REPLACE INTO directories 
                            (name, path, created_time, last_modified, directory_exists, last_scanned, is_main_dir, is_directory)
                            VALUES (?, ?, ?, ?, 1, ?, ?, ?)
                        """, batch_data)
                        success_count += len(batch_data)
                    except Exception as e:
                        error_count += len(batch_data)
                        print(f"[ERROR] 批量保存失败: {e}")
                
                conn.commit()
                
                # 进度反馈
                progress = int((batch_end / total_dirs) * 100)
                self.progress_updated.emit(progress, f"保存数据库中... ({batch_end}/{total_dirs})")
            
            conn.close()
            
            print(f"[INFO] 数据库保存完成: 成功 {success_count}, 重复 {duplicate_count}, 错误 {error_count}")
            self.save_finished.emit(success_count, error_count)
            
        except Exception as e:
            self.error_occurred.emit(f"数据库保存失败: {str(e)}")


class MultiDirectoryScanManager(QObject):
    """多目录扫描管理器"""
    
    progress_updated = Signal(int, str)
    scan_completed = Signal()
    error_occurred = Signal(str)
    
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.incremental_mode = True  # 默认启用增量扫描
        self.scan_workers = []
        self.save_workers = []
        self.is_running = False
        
    def scan_all_directories(self):
        """扫描所有主目录"""
        if not self.main_app.user_manager.current_db_path:
            self.error_occurred.emit("未登录用户")
            return
        
        # 停止之前的扫描
        self.stop_all()
        
        self.is_running = True
        
        try:
            # 获取主目录列表
            conn = sqlite3.connect(self.main_app.user_manager.current_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, path, scan_depth FROM main_directories")
            main_dirs = cursor.fetchall()
            conn.close()
            
            if not main_dirs:
                self.error_occurred.emit("没有主目录")
                return
            
            # 获取扫描模式
            scan_mode = self.main_app.get_setting('scan_mode', 'directories')
            
            # 使用线程池执行扫描
            self.scan_with_threadpool(main_dirs, scan_mode)
            
        except Exception as e:
            self.error_occurred.emit(f"扫描初始化失败: {str(e)}")
    
    def scan_with_threadpool(self, main_dirs, scan_mode):
        """使用受控线程池扫描目录（支持增量扫描）- 优化版
        使用单一QThread + ThreadPoolExecutor，限制并发数，避免线程过多导致卡顿"""
        total_dirs = len(main_dirs)
        
        # 获取增量扫描设置
        use_incremental = self.main_app.get_setting('incremental_scan', '1') == '1'
        
        # 打印扫描模式信息
        if use_incremental:
            pass
        else:
            print(f"[SCAN] 使用全量扫描模式，将扫描 {total_dirs} 个主目录")
        
        # 保存用于后续清理
        self._scanned_main_dirs = main_dirs
        
        self._scan_dispatcher = ScanDispatcherWorker(
            main_dirs, scan_mode, use_incremental, self.main_app
        )
        self._scan_thread = QThread()
        self._scan_dispatcher.moveToThread(self._scan_thread)
        
        # 连接信号
        self._scan_dispatcher.progress_updated.connect(self.progress_updated)
        self._scan_dispatcher.error_occurred.connect(self.error_occurred)
        self._scan_dispatcher.all_scans_finished.connect(self._on_all_scans_finished)
        
        # 启动
        self._scan_thread.started.connect(self._scan_dispatcher.run)
        self._scan_dispatcher.all_scans_finished.connect(self._scan_thread.quit)
        self._scan_dispatcher.all_scans_finished.connect(self._scan_dispatcher.deleteLater)
        self._scan_thread.finished.connect(self._scan_thread.deleteLater)
        
        self.scan_workers.append((self._scan_dispatcher, self._scan_thread))
        self._scan_thread.start()
    
    def _on_all_scans_finished(self, all_directories):
        """所有扫描完成后的回调"""
        print(f"[SCAN] 所有目录扫描完成，共发现 {len(all_directories)} 个变化项")
        if self.is_running:
            self.save_all_to_database(all_directories)
        else:
            self.scan_completed.emit()
    
    def save_all_to_database(self, all_directories):
        """保存所有目录到数据库（含根路径清理）"""
        if not self.is_running or not all_directories:
            self.scan_completed.emit()
            return
        
        print(f"[SAVE] 开始保存 {len(all_directories)} 个目录到数据库...")
        
        # 从扫描的主目录提取根路径用于清理
        root_paths = [p for _, p, _ in getattr(self, '_scanned_main_dirs', [])]
        if not root_paths:
            root_paths = []
        
        worker = DatabaseSaveWorker(
            self.main_app.user_manager.current_db_path, 
            all_directories,
            root_paths=root_paths
        )
        thread = QThread()
        
        worker.moveToThread(thread)
        worker.progress_updated.connect(lambda p, msg: self.progress_updated.emit(50 + p // 2, msg))  # 保存占50%
        worker.save_finished.connect(self.on_save_finished)
        worker.error_occurred.connect(self.error_occurred)
        
        thread.started.connect(worker.save_to_database)
        worker.save_finished.connect(thread.quit)
        worker.save_finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        
        self.save_workers.append((worker, thread))
        thread.start()

    def on_save_finished(self, success_count, error_count):
        """保存完成处理"""
        print(f"[SAVE] 保存完成: 成功={success_count}, 失败={error_count}")
        
        # 创建备份
        self.main_app.backup_manager.create_backup(self.main_app.user_manager.current_db_path)
        
        # 保存封面（异步）
        if self.main_app.get_setting('scan_save_cover', '0') == '1':
            # 获取当前目录数据
            if hasattr(self.main_app, 'get_current_directories'):
                directories = self.main_app.get_current_directories()
                if directories:
                    cover_save_mode, cover_save_dir = self.main_app.get_cover_save_settings()
                    skip_existing = self.main_app.get_setting('skip_existing_covers', '1') == '1'
                    
                    self.main_app.save_covers_async(
                        [d for d in directories if d.get("is_directory", 1) == 1],
                        cover_save_dir,
                        cover_save_mode,
                        skip_existing
                    )
        
        self.progress_updated.emit(100, f"扫描完成: {success_count}成功, {error_count}失败")
        self.scan_completed.emit()
        self.is_running = False


    
    def stop_all(self):
        """停止所有扫描并等待线程退出（防御性：捕获已删除的C++对象）"""
        self.is_running = False
        try:
            if hasattr(self, '_scan_dispatcher') and self._scan_dispatcher:
                self._scan_dispatcher.stop()
        except RuntimeError:
            pass
        try:
            if hasattr(self, '_scan_thread') and self._scan_thread and self._scan_thread.isRunning():
                self._scan_thread.quit()
                self._scan_thread.wait(3000)
        except RuntimeError:
            pass
        for worker, thread in list(self.scan_workers):
            try:
                if hasattr(worker, 'stop'): worker.stop()
            except RuntimeError: pass
            try:
                if thread and thread.isRunning():
                    thread.quit()
                    thread.wait(1000)
            except RuntimeError: pass
        for worker, thread in list(self.save_workers):
            try:
                if hasattr(worker, 'stop'): worker.stop()
            except RuntimeError: pass
            try:
                if thread and thread.isRunning():
                    thread.quit()
                    thread.wait(1000)
            except RuntimeError: pass
        self.scan_workers.clear()
        self.save_workers.clear()

class BatchCoverSaveWorker(QObject):
    """批量封面保存工作线程"""
    
    progress_updated = Signal(int, str)
    cover_saved = Signal(str, str)
    finished = Signal(int, int, int)  # 成功数, 跳过数, 失败数
    error_occurred = Signal(str)
    
    def __init__(self, main_app, directories, operation_type="save_all"):
        super().__init__()
        self.main_app = main_app
        self.directories = directories
        self.operation_type = operation_type
        self.is_running = True
        self.lock = Lock()
        
    def stop(self):
        """停止处理"""
        with self.lock:
            self.is_running = False
    
    def process_batch_covers(self):
        """批量处理封面 - 多线程分块并行优化版"""
        try:
            total = len(self.directories)
            if total == 0:
                self.finished.emit(0, 0, 0)
                return
            
            # 获取封面保存设置
            cover_save_mode, cover_save_dir = self.main_app.get_cover_save_settings()
            skip_existing = self.main_app.get_setting('skip_existing_covers', '1') == '1'
            
            # 将目录列表分成多个块，使用线程池并行处理
            cpu_count = os.cpu_count() or 4
            max_workers = min(cpu_count, 8)
            chunk_size = max(1, total // max_workers)
            chunks = [self.directories[i:i + chunk_size] for i in range(0, total, chunk_size)]
            
            success_count = 0
            skip_count = 0
            error_count = 0
            processed = [0]  # 用列表包装以在闭包中修改
            stats_lock = Lock()
            
            def process_chunk(chunk_dirs):
                """在Worker线程中处理一个块的封面"""
                chunk_success = 0
                chunk_error = 0
                
                for dir_info in chunk_dirs:
                    with self.lock:
                        if not self.is_running:
                            break
                    
                    try:
                        if self.process_single_cover(dir_info, cover_save_mode, cover_save_dir, skip_existing):
                            chunk_success += 1
                        else:
                            chunk_error += 1
                    except Exception as e:
                        chunk_error += 1
                        self.error_occurred.emit(f"处理封面失败 {dir_info.get('path', 'unknown')}: {str(e)}")
                    
                    # 更新进度
                    with stats_lock:
                        processed[0] += 1
                        progress = int(processed[0] / total * 100)
                        status_msg = f"处理封面中... ({processed[0]}/{total})"
                        self.progress_updated.emit(progress, status_msg)
                
                return chunk_success, chunk_error
            
            # 使用线程池并行处理所有块
            with ThreadPoolExecutor(max_workers=min(len(chunks), max_workers)) as executor:
                futures = [executor.submit(process_chunk, chunk) for chunk in chunks]
                for future in as_completed(futures):
                    try:
                        s, e = future.result()
                        success_count += s
                        error_count += e
                    except Exception as ex:
                        print(f"[COVER ERROR] 并行处理块失败: {ex}")
            
            # 发送完成信号
            self.finished.emit(success_count, skip_count, error_count)
            
        except Exception as e:
            self.error_occurred.emit(f"批量封面处理失败: {str(e)}")
            self.finished.emit(0, 0, 0)
    
    def process_single_cover(self, dir_info, cover_save_mode, cover_save_dir, skip_existing):
        """处理单个封面"""
        if dir_info.get("is_directory", 1) == 1:  # 目录
            return self.process_directory_cover(dir_info, cover_save_mode, cover_save_dir, skip_existing)
        else:  # 文件
            return self.process_file_cover(dir_info, cover_save_mode, cover_save_dir)
    
    def process_directory_cover(self, dir_info, cover_save_mode, cover_save_dir, skip_existing):
        """处理目录封面"""
        dir_path = dir_info["path"]
        
        # 检查是否跳过已存在的封面
        if skip_existing and self.operation_type == "save_missing":
            expected_path = self.main_app.get_expected_cover_path(dir_path, cover_save_dir, cover_save_mode)
            if expected_path and os.path.exists(expected_path):
                return False  # 标记为跳过
        
        # 查找封面图片
        cover_path = self.main_app.find_cover_image(dir_path)
        if cover_path and os.path.exists(cover_path):
            # 保存封面
            if self.main_app.save_cover_image(dir_path, cover_path):
                self.cover_saved.emit(dir_path, cover_path)
                return True
        else:
            # 尝试为PDF文件生成封面
            return self.try_generate_pdf_cover(dir_path)
        
        return False
    
    def process_file_cover(self, dir_info, cover_save_mode, cover_save_dir):
        """处理文件封面"""
        file_path = dir_info["path"]
        
        if file_path.lower().endswith('.pdf'):
            return self.main_app.generate_pdf_cover(file_path)
        
        return False
    
    def try_generate_pdf_cover(self, dir_path):
        """尝试为PDF文件生成封面"""
        try:
            for file in os.listdir(dir_path):
                if file.lower().endswith('.pdf'):
                    pdf_path = os.path.join(dir_path, file)
                    if self.main_app.generate_pdf_cover(pdf_path):
                        return True
        except Exception:
            pass
        return False

class DatabaseBackupWorker(QObject):
    """数据库备份工作线程"""
    
    progress_updated = Signal(int, str)
    backup_finished = Signal(str, bool, str)  # 备份路径, 是否成功, 错误信息
    finished = Signal()
    
    def __init__(self, backup_manager, db_path, backup_type="manual"):
        super().__init__()
        self.backup_manager = backup_manager
        self.db_path = db_path
        self.backup_type = backup_type
        self.is_running = True
        
    def stop(self):
        """停止备份"""
        self.is_running = False
    
    def create_backup(self):
        """创建数据库备份"""
        try:
            self.progress_updated.emit(0, "正在准备备份...")
            
            if not self.is_running:
                return
            
            self.progress_updated.emit(30, "正在创建备份文件...")
            
            # 执行备份
            success, result = self.backup_manager.create_backup(self.db_path, self.backup_type)
            
            if not self.is_running:
                return
            
            if success:
                self.progress_updated.emit(100, "备份完成")
                self.backup_finished.emit(result, True, "")
            else:
                self.progress_updated.emit(0, "备份失败")
                self.backup_finished.emit("", False, result)
                
        except Exception as e:
            error_msg = f"备份过程中出错: {str(e)}"
            self.backup_finished.emit("", False, error_msg)
        finally:
            self.finished.emit()

class DatabaseRestoreWorker(QObject):
    """数据库恢复工作线程"""
    
    progress_updated = Signal(int, str)
    restore_finished = Signal(bool, str)  # 是否成功, 错误信息
    finished = Signal()
    
    def __init__(self, backup_manager, backup_path, target_path):
        super().__init__()
        self.backup_manager = backup_manager
        self.backup_path = backup_path
        self.target_path = target_path
        self.is_running = True
        
    def stop(self):
        """停止恢复"""
        self.is_running = False
    
    def restore_backup(self):
        """恢复数据库备份"""
        try:
            self.progress_updated.emit(0, "正在准备恢复...")
            
            if not self.is_running:
                return
            
            self.progress_updated.emit(30, "正在恢复数据库...")
            
            # 执行恢复
            success, error = self.backup_manager.restore_backup(self.backup_path, self.target_path)
            
            if not self.is_running:
                return
            
            if success:
                self.progress_updated.emit(100, "恢复完成")
                self.restore_finished.emit(True, "")
            else:
                self.progress_updated.emit(0, "恢复失败")
                self.restore_finished.emit(False, error)
                
        except Exception as e:
            error_msg = f"恢复过程中出错: {str(e)}"
            self.restore_finished.emit(False, error_msg)
        finally:
            self.finished.emit()

class StaticFileDownloadWorker(QObject):
    """静态文件下载工作线程"""
    
    progress_updated = Signal(int, str)
    download_finished = Signal(str, bool, str)  # 文件名, 是否成功, 错误信息
    all_finished = Signal()
    
    def __init__(self, download_files, static_dir):
        super().__init__()
        self.download_files = download_files
        self.static_dir = static_dir
        self.is_running = True
        self.lock = Lock()
        
    def stop(self):
        """停止下载"""
        with self.lock:
            self.is_running = False
    
    def download_files_parallel(self):
        """并行下载文件"""
        try:
            total_files = len(self.download_files)
            completed_count = 0
            
            # 使用线程池并行下载
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                # 提交所有下载任务
                future_to_file = {
                    executor.submit(self.download_single_file, file_info): file_info 
                    for file_info in self.download_files
                }
                
                # 处理完成的任务
                for future in concurrent.futures.as_completed(future_to_file):
                    if not self.is_running:
                        # 取消未完成的任务
                        for f in future_to_file:
                            f.cancel()
                        break
                    
                    file_info = future_to_file[future]
                    filename = file_info['filename']
                    
                    try:
                        success, message = future.result()
                        self.download_finished.emit(filename, success, message)
                    except Exception as e:
                        self.download_finished.emit(filename, False, str(e))
                    
                    completed_count += 1
                    progress = int(completed_count / total_files * 100)
                    self.progress_updated.emit(progress, f"下载进度: {completed_count}/{total_files}")
            
            self.all_finished.emit()
            
        except Exception as e:
            self.all_finished.emit()
    
    def download_single_file(self, file_info):
        """下载单个文件"""
        try:
            url = file_info['url']
            file_path = os.path.join(self.static_dir, file_info['filename'])
            description = file_info['description']
            
            # 检查是否停止
            with self.lock:
                if not self.is_running:
                    return False, "下载已取消"
            
            # 创建SSL上下文
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # 下载文件
            import urllib.request
            with urllib.request.urlopen(url, context=ssl_context) as response:
                file_data = response.read()
            
            # 再次检查是否停止
            with self.lock:
                if not self.is_running:
                    return False, "下载已取消"
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            return True, f"下载成功 ({len(file_data)} 字节)"
            
        except Exception as e:
            return False, f"下载失败: {str(e)}"

class MD5CalculationWorker(QObject):
    """MD5计算工作线程"""
    
    progress_updated = Signal(int, str)
    calculation_finished = Signal(dict)  # 文件路径 -> MD5映射
    finished = Signal()
    
    def __init__(self, file_paths):
        super().__init__()
        self.file_paths = file_paths
        self.is_running = True
        self.lock = Lock()
        
    def stop(self):
        """停止计算"""
        with self.lock:
            self.is_running = False
    
    def calculate_md5_batch(self):
        """批量计算MD5 - 修复版本"""
        try:
            total_files = len(self.file_paths)
            md5_map = {}
            
            for i, file_path in enumerate(self.file_paths):
                # 频繁检查停止信号
                with self.lock:
                    if not self.is_running:
                        print("[MD5 DEBUG] MD5计算被用户停止")
                        break
                
                # 每处理5个文件就检查一次（更频繁）
                if i % 5 == 0:
                    with self.lock:
                        if not self.is_running:
                            break
                
                # 更新进度
                progress = int((i + 1) / total_files * 100)
                status_msg = f"计算MD5指纹... ({i+1}/{total_files})"
                self.progress_updated.emit(progress, status_msg)
                
                try:
                    md5_value = self.calculate_single_md5(file_path)
                    if md5_value:
                        md5_map[file_path] = md5_value
                except Exception as e:
                    print(f"[MD5 ERROR] 计算MD5失败 {file_path}: {e}")
            
            # 发送完成信号
            self.calculation_finished.emit(md5_map)
            self.finished.emit()
            
        except Exception as e:
            print(f"[MD5 ERROR] 批量MD5计算失败: {e}")
            self.finished.emit()


    
    def calculate_single_md5(self, file_path):
        """计算单个文件的MD5"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5()
                while chunk := f.read(8192):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except Exception as e:
            print(f"[MD5 ERROR] 计算文件MD5失败 {file_path}: {e}")
            return None

class PDFProcessingWorker(QObject):
    """PDF文件处理工作线程 - 多线程版本"""
    
    progress_updated = Signal(int, str)
    pdf_processed = Signal(str, str, bool)  # 文件路径, 操作类型, 是否成功
    finished = Signal(int, int, int)  # 成功数, 跳过数, 失败数
    error_occurred = Signal(str, str)  # 错误消息, 文件路径
    
    def __init__(self, main_app, pdf_files, operation_type="generate_covers"):
        super().__init__()
        self.main_app = main_app
        self.pdf_files = pdf_files
        self.operation_type = operation_type
        self.is_running = True
        self.lock = Lock()
        
    def stop(self):
        """停止处理"""
        with self.lock:
            self.is_running = False
    
    def process_pdfs(self):
        """批量处理PDF文件 - 多线程版本"""
        try:
            total_files = len(self.pdf_files)
            if total_files == 0:
                self.finished.emit(0, 0, 0)
                return
            
            success_count = 0
            skip_count = 0
            error_count = 0
            
            # === 新增：发送初始进度 ===
            self.progress_updated.emit(0, f"开始处理 {total_files} 个PDF文件...")
            
            # 使用线程池并行处理PDF文件
            with ThreadPoolExecutor(max_workers=min(4, total_files)) as executor:
                # 提交所有PDF处理任务
                future_to_pdf = {
                    executor.submit(self.process_single_pdf, pdf_path): pdf_path 
                    for pdf_path in self.pdf_files
                }
                
                # 处理完成的任务
                for i, future in enumerate(as_completed(future_to_pdf)):
                    # 检查是否停止
                    with self.lock:
                        if not self.is_running:
                            # 取消未完成的任务
                            for f in future_to_pdf:
                                f.cancel()
                            break
                    
                    pdf_path = future_to_pdf[future]
                    
                    try:
                        result = future.result()
                        if result:
                            success_count += 1
                            self.pdf_processed.emit(pdf_path, self.operation_type, True)
                        else:
                            error_count += 1
                            self.pdf_processed.emit(pdf_path, self.operation_type, False)
                    
                    except Exception as e:
                        error_count += 1
                        self.error_occurred.emit(f"处理PDF失败 {pdf_path}: {str(e)}", pdf_path)
                    
                    # === 新增：实时更新进度 ===
                    progress = int((i + 1) / total_files * 100)
                    status_msg = f"处理PDF文件中... ({i+1}/{total_files})"
                    self.progress_updated.emit(progress, status_msg)
            
            # 发送完成信号
            self.finished.emit(success_count, skip_count, error_count)
            
        except Exception as e:
            self.error_occurred.emit(f"批量PDF处理失败: {str(e)}", "global")
            self.finished.emit(0, 0, 0)
    
    def process_single_pdf(self, pdf_path):
        """处理单个PDF文件"""
        try:
            if not os.path.exists(pdf_path):
                return False
            
            if self.operation_type == "generate_covers":
                return self.main_app.generate_pdf_cover(pdf_path)
            elif self.operation_type == "extract_text":
                return self.extract_pdf_text(pdf_path)
            elif self.operation_type == "analyze_metadata":
                return self.analyze_pdf_metadata(pdf_path)
            else:
                return self.main_app.generate_pdf_cover(pdf_path)
                
        except Exception as e:
            print(f"[PDF PROCESS ERROR] 处理PDF失败 {pdf_path}: {e}")
            return False
    
    def extract_pdf_text(self, pdf_path):
        """提取PDF文本内容 - 多线程安全"""
        try:
            import fitz  # PyMuPDF
            
            pdf_document = fitz.open(pdf_path)
            text_content = ""
            
            # 限制处理的页数，避免大文件处理时间过长
            max_pages = min(10, len(pdf_document))
            
            for page_num in range(max_pages):
                page = pdf_document[page_num]
                text_content += page.get_text()
            
            pdf_document.close()
            
            # 保存文本内容到文件
            text_path = pdf_path + ".txt"
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            return True
            
        except Exception as e:
            print(f"[PDF TEXT EXTRACT ERROR] 提取文本失败 {pdf_path}: {e}")
            return False
    
    def analyze_pdf_metadata(self, pdf_path):
        """分析PDF元数据 - 多线程安全"""
        try:
            import fitz  # PyMuPDF
            
            pdf_document = fitz.open(pdf_path)
            metadata = pdf_document.metadata
            page_count = len(pdf_document)
            
            pdf_document.close()
            
            # 保存元数据到文件
            meta_path = pdf_path + ".meta.json"
            metadata_info = {
                "file_path": pdf_path,
                "page_count": page_count,
                "metadata": metadata,
                "file_size": os.path.getsize(pdf_path),
                "analysis_time": datetime.datetime.now().isoformat()
            }
            
            with open(meta_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(metadata_info, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"[PDF METADATA ERROR] 分析元数据失败 {pdf_path}: {e}")
            return False

class PDFValidationWorker(QObject):
    """PDF验证工作线程"""
    
    progress_updated = Signal(int, str)
    validation_finished = Signal(dict)  # 验证结果字典
    file_validated = Signal(str, bool, str)  # 文件路径, 是否有效, 验证信息
    finished = Signal()
    
    def __init__(self, pdf_files):
        super().__init__()
        self.pdf_files = pdf_files
        self.is_running = True
        self.lock = Lock()
        
    def stop(self):
        """停止验证"""
        with self.lock:
            self.is_running = False
    
    def validate_pdfs(self):
        """批量验证PDF文件 - 多线程版本"""
        try:
            total_files = len(self.pdf_files)
            if total_files == 0:
                self.validation_finished.emit({})
                self.finished.emit()
                return
            
            validation_results = {}
            
            # 使用线程池并行验证
            with ThreadPoolExecutor(max_workers=min(4, total_files)) as executor:
                # 提交所有验证任务
                future_to_pdf = {
                    executor.submit(self.validate_single_pdf, pdf_path): pdf_path 
                    for pdf_path in self.pdf_files
                }
                
                # 处理完成的任务
                for i, future in enumerate(as_completed(future_to_pdf)):
                    # 检查是否停止
                    with self.lock:
                        if not self.is_running:
                            # 取消未完成的任务
                            for f in future_to_pdf:
                                f.cancel()
                            break
                    
                    pdf_path = future_to_pdf[future]
                    
                    try:
                        is_valid, message = future.result()
                        validation_results[pdf_path] = {
                            'valid': is_valid,
                            'message': message
                        }
                        
                        # 发送单个文件验证结果
                        self.file_validated.emit(pdf_path, is_valid, message)
                        
                    except Exception as e:
                        validation_results[pdf_path] = {
                            'valid': False,
                            'message': f"验证异常: {str(e)}"
                        }
                        self.file_validated.emit(pdf_path, False, f"验证异常: {str(e)}")
                    
                    # 更新进度
                    progress = int((i + 1) / total_files * 100)
                    status_msg = f"验证PDF文件中... ({i+1}/{total_files})"
                    self.progress_updated.emit(progress, status_msg)
            
            # 发送完整验证结果
            self.validation_finished.emit(validation_results)
            self.finished.emit()
            
        except Exception as e:
            print(f"[PDF VALIDATION ERROR] 批量验证失败: {str(e)}")
            self.finished.emit()
    
    def validate_single_pdf(self, pdf_path):
        """验证单个PDF文件"""
        try:
            # 检查文件是否存在
            if not os.path.exists(pdf_path):
                return False, "文件不存在"
                
            # 检查文件大小
            file_size = os.path.getsize(pdf_path)
            if file_size == 0:
                return False, "文件为空"
                
            if file_size < 100:  # PDF文件通常至少几百字节
                return False, f"文件过小可能损坏 ({file_size} bytes)"
            
            # 检查PDF文件头
            with open(pdf_path, 'rb') as f:
                header = f.read(8)
                if not header.startswith(b'%PDF'):
                    return False, "不是有效的PDF文件格式"
            
            # 检查文件扩展名
            if not pdf_path.lower().endswith('.pdf'):
                return False, "不是PDF文件扩展名"
            
            # 可选：深度完整性检查（如果poppler可用）
            if self.is_poppler_available():
                try:
                    import subprocess
                    # 修复编码问题：指定UTF-8编码并忽略错误
                    result = subprocess.run(
                        ['pdfinfo', pdf_path],
                        capture_output=True, 
                        text=True, 
                        encoding='utf-8',
                        errors='ignore',  # 忽略编码错误
                        timeout=5
                    )
                    if result.returncode != 0:
                        return False, "PDF文件可能损坏"
                except:
                    pass  # 如果深度检查失败，仍然认为基础验证通过
                
            return True, "文件验证通过"
            
        except Exception as e:
            return False, f"验证失败: {str(e)}"
    
    def is_poppler_available(self):
        """检查poppler-utils是否可用"""
        try:
            import subprocess
            result = subprocess.run(['pdfinfo', '-v'], 
                                capture_output=True, text=True, timeout=2)
            return result.returncode == 0
        except:
            return False

    def validate_pdf_files_threaded(self, pdf_files=None):
        """多线程验证PDF文件"""
        if pdf_files is None:
            pdf_files = self.find_all_pdf_files()
        
        if not pdf_files:
            QMessageBox.information(self, "提示", "没有找到PDF文件")
            return
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("准备验证PDF文件...")
        
        # 创建工作线程
        self.pdf_validation_worker = PDFValidationWorker(pdf_files)
        self.pdf_validation_thread = QThread()
        
        self.pdf_validation_worker.moveToThread(self.pdf_validation_thread)
        self.pdf_validation_worker.progress_updated.connect(self.on_pdf_validation_progress)
        self.pdf_validation_worker.validation_finished.connect(self.on_pdf_validation_finished)
        self.pdf_validation_worker.file_validated.connect(self.on_single_pdf_validated)
        
        self.pdf_validation_thread.started.connect(self.pdf_validation_worker.validate_pdfs)
        self.pdf_validation_worker.finished.connect(self.pdf_validation_thread.quit)
        self.pdf_validation_worker.finished.connect(self.pdf_validation_worker.deleteLater)
        self.pdf_validation_thread.finished.connect(self.pdf_validation_thread.deleteLater)
        
        self.pdf_validation_thread.start()

    def on_pdf_validation_progress(self, progress, message):
        """PDF验证进度更新"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(message)

    def on_pdf_validation_finished(self, validation_results):
        """PDF验证完成"""
        self.progress_bar.setValue(100)
        self.progress_label.setText("PDF验证完成")
        
        # 统计结果
        total_files = len(validation_results)
        valid_files = sum(1 for result in validation_results.values() if result['valid'])
        invalid_files = total_files - valid_files
        
        # 显示结果
        result_msg = f"PDF验证完成:\n总文件数: {total_files}\n有效文件: {valid_files}\n无效文件: {invalid_files}"
        
        if invalid_files > 0:
            invalid_list = []
            for pdf_path, result in validation_results.items():
                if not result['valid']:
                    invalid_list.append(f"{os.path.basename(pdf_path)}: {result['message']}")
            
            if invalid_list:
                result_msg += f"\n\n无效文件详情:\n" + "\n".join(invalid_list[:10])  # 只显示前10个
                if len(invalid_list) > 10:
                    result_msg += f"\n... 还有 {len(invalid_list) - 10} 个无效文件"
        
        QMessageBox.information(self, "PDF验证结果", result_msg)
        
        # 3秒后隐藏进度条
        QTimer.singleShot(3000, self.hide_progress_bar)

    def on_single_pdf_validated(self, pdf_path, is_valid, message):
        """单个PDF文件验证完成"""
        status_icon = "✓" if is_valid else "❌"
        print(f"[PDF VALIDATION] {status_icon} {os.path.basename(pdf_path)}: {message}")



    def quick_validate_pdfs(self, dialog):
        """快速验证PDF文件"""
        dialog.accept()
        self.validate_pdf_files_threaded()

    def start_pdf_processing(self, dialog):
        """开始PDF处理"""
        operation_type = self.pdf_operation_combo.currentData()
        dialog.accept()
        
        if operation_type == "validate_files":
            self.validate_pdf_files_threaded()
        else:
            self.batch_process_pdfs_threaded(operation_type)

class FlowLayout(QLayout):
    """流式布局 - 自动换行的网格布局"""
    def __init__(self, parent=None, margin=5, spacing=10):
        super().__init__(parent)
        self.itemList = []
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0
        
        for item in self.itemList:
            widget = item.widget()
            if widget is None:
                continue
            
            spaceX = self.spacing()
            spaceY = self.spacing()
            
            nextX = x + widget.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + widget.sizeHint().width() + spaceX
                lineHeight = 0
            
            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), widget.sizeHint()))
            
            x = x + widget.sizeHint().width() + spaceX
            lineHeight = max(lineHeight, widget.sizeHint().height())
        
        return y + lineHeight - rect.y()


# 主窗口
class DirectoryScannerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # 添加关闭标志
        self._is_closing = False

        # 【修复】索引检查的线程安全：_indexes_checked_paths 与
        # _indexes_check_conn_key 会在工作线程（扫描循环等经 get_setting）与
        # 主线程（login_user / load_directories）被并发读改写，必须加锁保护。
        self._indexes_lock = threading.RLock()
        self._indexes_checked_paths = set()
        self._indexes_check_conn_key = None

        self._view_mode = 'list'  # 默认列表视图
        
        # 添加路径过滤属性
        self.current_path_filter = ""

        # 添加多线程工作器引用
        self.md5_worker = None
        self.md5_thread = None

        # 添加多线程工作器引用
        self.batch_cover_worker = None
        self.batch_cover_thread = None
        self.pdf_cover_worker = None
        self.pdf_cover_thread = None
        self.backup_worker = None
        self.backup_thread = None
        self.restore_worker = None
        self.restore_thread = None
        self.download_worker = None
        self.download_thread = None
        
        # 线程池用于小型任务
        self.thread_pool = ThreadPoolManager(max_workers=4)
                
        # 修改1: 处理打包后的资源路径问题
        if getattr(sys, 'frozen', False):
            # 打包后exe所在的目录
            self.app_dir = os.path.dirname(sys.executable)
        else:
            # 开发环境下的目录
            self.app_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 修改2: 确保数据库目录存在
        if not os.path.exists(self.app_dir):
            os.makedirs(self.app_dir)
            
        # 初始化用户管理和数据库备份
        self.user_manager = UserManager(self.app_dir)
        self.backup_manager = DatabaseBackupManager(self.app_dir, max_backups=30)
        
        # 当前扫描的主目录
        self.main_directory = ""
        
        # 扫描定时器
        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self.scan_directories)
    
        # PDF处理相关属性
        self.pdf_processing_worker = None
        self.pdf_processing_thread = None
        self.pdf_validation_worker = None
        self.pdf_validation_thread = None
        
        # 单次扫描相关属性
        self.single_scan_worker = None
        self.single_scan_thread = None
        
        # 数据库保存相关属性
        self.db_save_worker = None
        self.db_save_thread = None
        
        # 目录扫描相关属性
        self.directory_scan_worker = None
        self.directory_scan_thread = None
        
        # 静态文件下载相关属性
        self.static_download_worker = None
        self.static_download_thread = None

        # 初始化UI（最先完成，让界面立即可见）
        self.init_ui()
        
        # 初始化服务器（紧接着启动，不延迟）
        self.init_server()
        
        # 设置初始服务器状态显示
        QTimer.singleShot(100, self.update_server_status_display)
        
        # 立即启动Web服务器（不延迟，让用户看到服务器状态）
        QTimer.singleShot(500, self.auto_start_web_server)

        # 初始化静态文件（后台异步下载）
        # 【性能优化】原先后台异步之前还多调了一次同步的 self.init_static_files()。
        # 该同步版本会走 download_static_files() -> download_file()，
        # 直接在 UI 主线程上用 urllib.request.urlopen 做网络 IO。当前 static/epub.js
        # 与 jszip.min.js 都已存在，所以只是白跑 2 次 os.path.exists；
        # 但一旦文件缺失（首次部署 / 用户误删），启动就会在主线程被网络阻塞，
        # 且完全没有超时与进度反馈。异步版本 download_static_files_threaded()
        # 已具备：存在性检查（存在即不下载、不发任何网络请求）、QThread 后台执行、
        # 失败后仅记录不抛出。因此去掉同步调用，只保留异步路径。
        self.init_static_files_async()

        # 添加多目录扫描管理器
        self.scan_manager = MultiDirectoryScanManager(self)
        self.scan_manager.progress_updated.connect(self.on_scan_progress_updated)
        self.scan_manager.scan_completed.connect(self.on_scan_completed)
        self.scan_manager.error_occurred.connect(self.on_scan_error)

        # 最后检查用户登录 —— 在UI和服务器都就绪后，延迟显示登录对话框
        # 这样用户先看到完整的界面，再处理登录和数据加载
        if not self.user_manager.current_user:
            QTimer.singleShot(300, self._show_login_deferred)
        else:
            # 已有用户登录，显示加载进度条再加载数据
            QTimer.singleShot(200, self._load_data_with_progress)
        
        # 恢复上次的窗口大小
        self._restore_window_geometry()
    
    def _restore_window_geometry(self):
        """恢复上次保存的窗口大小"""
        try:
            geo_file = os.path.join(self.app_dir, "window_geometry.json")
            if os.path.exists(geo_file):
                with open(geo_file, 'r') as f:
                    geo = json.load(f)
                w, h = geo.get('width', 1000), geo.get('height', 600)
                self.resize(max(400, min(w, 3000)), max(300, min(h, 2000)))
        except Exception:
            pass
    
    def _save_window_geometry(self):
        """保存当前窗口大小"""
        try:
            geo_file = os.path.join(self.app_dir, "window_geometry.json")
            with open(geo_file, 'w') as f:
                json.dump({'width': self.width(), 'height': self.height()}, f)
        except Exception:
            pass
    
    def _show_login_deferred(self):
        """延迟显示登录对话框，让UI先渲染完成"""
        dialog = UserManagerDialog(self.user_manager, self)
        if dialog.exec() == QDialog.Accepted:
            self._clear_table()
            self.load_user_settings()
            self.update_window_title()
            self.update_status_bar(f"用户 {self.user_manager.current_user} 登录成功", 3000)
            self._load_data_with_progress()
            QTimer.singleShot(3000, self.start_auto_scan)
    
    def _load_data_with_progress(self):
        """显示加载进度条，然后加载目录数据"""
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("正在加载目录数据...")
        self.statusBar().showMessage("正在加载目录数据，请稍候...")
        # 让UI先刷新显示进度条
        QApplication.processEvents()
        # 延迟一帧后加载数据（确保进度条已渲染）
        QTimer.singleShot(50, self._do_load_directories)
    
    def _do_load_directories(self):
        """执行数据加载（表格填充），后续缩略图加载由 start_thumbnail_loading 管理进度"""
        self.load_directories()
        # 注意：不在这里隐藏进度条，由 _on_all_loading_complete 统一管理
    
    def _hide_loading_progress(self):
        """隐藏加载进度条"""
        self.progress_bar.setVisible(False)
        self.progress_label.setText("就绪")
        self.progress_bar.setValue(0)

    def init_static_files_async(self):
        """在后台线程中初始化静态文件"""
        self.download_static_files_threaded()


    def init_ui(self):
        # self.setWindowTitle("目录扫描管理系统")
        # self.setWindowTitle(f"{ProjectInfo.NAME} {ProjectInfo.VERSION} (Build: {ProjectInfo.BUILD_DATE})")
        # 初始设置标题（不包含用户名，因为此时用户可能还未登录）
        self.update_window_title()
        self.setMinimumSize(800, 600)
        self.resize(1000, 600)
        # self.resize(1450, 850)
        
        # 设置图标
        icon_path = os.path.join(self.app_dir, "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 创建主部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        
        # 工具栏
        toolbar = self.addToolBar("主工具栏")

        # === 服务器状态指示器 ===
        self.server_status_indicator = QLabel("🔴 服务器离线")
        self.server_status_indicator.setStyleSheet("""
            QLabel {
                padding: 5px 10px;
                border: 1px solid #ccc;
                border-radius: 10px;
                background-color: #ffebee;
                color: #c62828;
                font-weight: bold;
            }
        """)
        toolbar.addWidget(self.server_status_indicator)

        # 添加服务器控制按钮
        self.server_action = QAction(QIcon.fromTheme("network-server"), "🌐启动Web服务器", self)
        self.server_action.triggered.connect(self.toggle_server)
        toolbar.addAction(self.server_action)
        
        # 主目录管理按钮
        main_dir_action = QAction("📁主目录管理", self)
        main_dir_action.triggered.connect(self.manage_main_directories)
        toolbar.addAction(main_dir_action)
        
        # 扫描按钮
        scan_action = QAction("🔍扫描目录", self)
        scan_action.triggered.connect(self.scan_directories)
        toolbar.addAction(scan_action)
        
        # 切换视图按钮
        self.view_action = QAction("📋切换到网格视图", self)
        self.view_action.triggered.connect(self.toggle_view_mode)
        toolbar.addAction(self.view_action)
        
        # 清空列表按钮
        clear_list_action = QAction("🧹清空列表", self)
        clear_list_action.setToolTip("清空当前显示的列表（不删除数据库数据）")
        clear_list_action.triggered.connect(self.clear_current_list)
        toolbar.addAction(clear_list_action)
        
        # 分隔线
        toolbar.addSeparator()

        # 批量保存封面按钮
        batch_cover_action = QAction("💾批量保存封面", self)
        batch_cover_action.triggered.connect(self.batch_save_all_covers_threaded)
        toolbar.addAction(batch_cover_action)

        # PDF工具按钮
        pdf_tools_action = QAction("📄PDF工具", self)
        pdf_tools_action.triggered.connect(self.show_pdf_tools_dialog)
        toolbar.addAction(pdf_tools_action)

        # 设置按钮
        settings_action = QAction("🛠️设置", self)
        settings_action.triggered.connect(self.show_settings)
        toolbar.addAction(settings_action)
        
        # 用户管理按钮
        user_action = QAction("👥用户管理", self)
        user_action.triggered.connect(self.show_user_manager)
        toolbar.addAction(user_action)
        
        # 管理方案按钮
        preset_action = QAction("📋管理方案", self)
        preset_action.triggered.connect(self.show_preset_manager)
        toolbar.addAction(preset_action)
        
        # 数据库备份按钮
        backup_action = QAction("💾数据库备份", self)
        backup_action.triggered.connect(self.manual_backup)
        toolbar.addAction(backup_action)
        
        # 恢复按钮
        restore_action = QAction("🔄恢复数据库", self)
        restore_action.triggered.connect(self.show_restore_dialog)
        toolbar.addAction(restore_action)

        # 分隔线
        toolbar.addSeparator()

        # 关于按钮
        about_action = QAction("🏆关于", self)
        about_action.triggered.connect(self.show_about_dialog)
        toolbar.addAction(about_action)
        
        # 主目录显示
        self.dir_label = QLabel("主目录: 未设置")
        self.dir_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(self.dir_label)
        
        # ========== 统一的搜索、排序、过滤工具栏（合并为一行） ==========
        unified_toolbar = QHBoxLayout()
        unified_toolbar.setContentsMargins(0, 8, 0, 8)
        unified_toolbar.setSpacing(8)
        
        # 1. 搜索区域
        search_group = QGroupBox("🔍 搜索目录")
        search_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #333;
            }
        """)
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 4, 0, 0)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词搜索...支持拼音首字母")
        self.search_input.setMinimumWidth(180)
        self.search_input.setStyleSheet("padding: 6px 10px; border-radius: 4px; border: 1px solid #ccc;")
        self.search_input.returnPressed.connect(self.filter_directories)
        
        self.search_button = QPushButton("🔍")
        self.search_button.setToolTip("搜索")
        self.search_button.setFixedSize(40, 32)
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 16px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.search_button.clicked.connect(self.filter_directories)
        
        self.clear_button = QPushButton("✕")
        self.clear_button.setToolTip("清除搜索内容")
        self.clear_button.setFixedSize(40, 32)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #da190b; }
        """)
        self.clear_button.clicked.connect(self.clear_search)
        
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.clear_button)
        search_group.setLayout(search_layout)
        unified_toolbar.addWidget(search_group, 3)  # 占比3
        
        # 2. 排序区域
        sort_group = QGroupBox("📊 排序方式")
        sort_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #333;
            }
        """)
        sort_layout = QHBoxLayout()
        sort_layout.setContentsMargins(0, 4, 0, 0)
        sort_layout.setSpacing(5)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("按名称", "name")
        self.sort_combo.addItem("按日期", "date")
        self.sort_combo.addItem("按路径", "path")
        self.sort_combo.setStyleSheet("padding: 4px 8px; border-radius: 4px; border: 1px solid #ccc;")
        self.sort_combo.currentIndexChanged.connect(self.filter_directories)
        
        date_label_from = QLabel("从:")
        date_label_from.setStyleSheet("font-size: 11px; color: #666;")
        
        self.date_from_edit = QDateEdit()
        self.date_from_edit.setCalendarPopup(True)
        self.date_from_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_from_edit.setDate(QDate.currentDate().addYears(-10))
        self.date_from_edit.setStyleSheet("padding: 3px 5px; border-radius: 4px; border: 1px solid #ccc;")
        self.date_from_edit.setFixedWidth(110)
        self.date_from_edit.dateChanged.connect(self.filter_directories)
        
        date_label_to = QLabel("到:")
        date_label_to.setStyleSheet("font-size: 11px; color: #666;")
        
        self.date_to_edit = QDateEdit()
        self.date_to_edit.setCalendarPopup(True)
        self.date_to_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_to_edit.setDate(QDate.currentDate().addDays(1))
        self.date_to_edit.setStyleSheet("padding: 3px 5px; border-radius: 4px; border: 1px solid #ccc;")
        self.date_to_edit.setFixedWidth(110)
        self.date_to_edit.dateChanged.connect(self.filter_directories)
        
        sort_layout.addWidget(self.sort_combo)
        sort_layout.addWidget(date_label_from)
        sort_layout.addWidget(self.date_from_edit)
        sort_layout.addWidget(date_label_to)
        sort_layout.addWidget(self.date_to_edit)
        sort_group.setLayout(sort_layout)
        unified_toolbar.addWidget(sort_group, 2)  # 占比2
        
        # 3. 目录过滤区域
        filter_group = QGroupBox("📁 目录过滤")
        filter_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #333;
            }
        """)
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 4, 0, 0)
        filter_layout.setSpacing(5)
        
        self.path_filter_input = QLineEdit()
        self.path_filter_input.setPlaceholderText("路径关键词，多个用|分隔")
        self.path_filter_input.setMinimumWidth(160)
        self.path_filter_input.setStyleSheet("padding: 6px 10px; border-radius: 4px; border: 1px solid #ccc;")
        self.path_filter_input.returnPressed.connect(self.apply_path_filter)
        
        self.apply_filter_btn = QPushButton("✓")
        self.apply_filter_btn.setToolTip("应用过滤")
        self.apply_filter_btn.setFixedSize(36, 32)
        self.apply_filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c5ce7;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #5a4bd1; }
        """)
        self.apply_filter_btn.clicked.connect(self.apply_path_filter)
        
        self.clear_filter_btn = QPushButton("✕")
        self.clear_filter_btn.setToolTip("清除过滤")
        self.clear_filter_btn.setFixedSize(36, 32)
        self.clear_filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        self.clear_filter_btn.clicked.connect(self.clear_path_filter)
        
        self.select_dir_btn = QPushButton("📂")
        self.select_dir_btn.setToolTip("选择目录...")
        self.select_dir_btn.setFixedSize(36, 32)
        self.select_dir_btn.setStyleSheet("""
            QPushButton {
                background-color: #00b894;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #00a381; }
        """)
        self.select_dir_btn.clicked.connect(self.show_path_filter_dialog)
        
        filter_layout.addWidget(self.path_filter_input, 1)
        filter_layout.addWidget(self.apply_filter_btn)
        filter_layout.addWidget(self.clear_filter_btn)
        filter_layout.addWidget(self.select_dir_btn)
        filter_group.setLayout(filter_layout)
        unified_toolbar.addWidget(filter_group, 2)  # 占比2
        
        main_layout.addLayout(unified_toolbar)
        # ========== 统一的搜索栏结束 ==========
        
        # 过滤状态标签
        self.filter_status_label = QLabel("")
        self.filter_status_label.setStyleSheet("color: #6c5ce7; font-size: 11px; padding: 2px 5px;")
        self.filter_status_label.setVisible(False)
        main_layout.addWidget(self.filter_status_label)

        # === 进度条 ===
        progress_layout = QHBoxLayout()
        
        self.progress_label = QLabel("就绪")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)  # 初始时隐藏
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(progress_layout)

        # 添加一个空的滚动区域容器
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.grid_container = QWidget()
        self.scroll_area.setWidget(self.grid_container)
        main_layout.addWidget(self.scroll_area)
        # 初始时隐藏滚动区域（默认显示表格）
        self.scroll_area.hide()

        # 状态栏
        self.statusBar().showMessage("就绪")

        # === 状态栏服务器信息 ===
        self.status_server_info = QLabel("服务器: 未启动")
        self.statusBar().addPermanentWidget(self.status_server_info)

        # 确保表格控件始终存在（即使无数据也保持布局一致）
        self._ensure_table_exists()

        # 加载用户设置
        self.load_user_settings()


    def init_static_files(self):
        """初始化静态文件"""
        static_dir = os.path.join(self.app_dir, "static")
        os.makedirs(static_dir, exist_ok=True)
        
        # 检查并下载必要的静态文件
        self.download_static_files()
    
    def download_static_files(self):
        """下载必要的静态文件"""
        static_files = {
            'epub.js': {
                'url': 'https://cdn.jsdelivr.net/npm/epubjs/dist/epub.min.js',
                'description': 'EPUB.js库'
            },
            'jszip.min.js': {
                'url': 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js',
                'description': 'JSZip库'
            }
        }
        
        static_dir = os.path.join(self.app_dir, "static")
        
        for filename, file_info in static_files.items():
            print(f"[STATIC] 检查文件: {filename}")
            file_path = os.path.join(static_dir, filename)
            print(f"[STATIC] 目标路径: {file_path}")
            
            # 如果文件不存在或需要更新，则下载
            if not os.path.exists(file_path):
                print(f"[STATIC] 文件 {filename} 不存在，开始下载...")
                self.download_file(file_info['url'], file_path, file_info['description'])
                print(f"[STATIC] 文件 {filename} 下载完成")
    
    def download_file(self, url, file_path, description):
        """下载文件"""
        try:
            print(f"[STATIC] 正在下载 {description}...")
            
            import urllib.request
            import ssl
            
            # 创建SSL上下文（忽略证书验证）
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # 下载文件
            with urllib.request.urlopen(url, context=ssl_context) as response:
                print(f"[STATIC] 连接到 {url} 成功，开始读取数据...")
                file_data = response.read()
                print(f"[STATIC] 数据读取完成，大小: {len(file_data)} 字节")    
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            file_size = len(file_data)
            print(f"[STATIC] ✓ {description} 下载成功 ({self.format_file_size(file_size)})")
            
        except Exception as e:
            print(f"[STATIC] ❌ {description} 下载失败: {e}")
    
    def format_file_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"

    def show_user_manager(self):
        """显示用户管理对话框（工具栏调用），登录后延迟加载数据避免卡顿"""
        dialog = UserManagerDialog(self.user_manager, self)
        if dialog.exec() == QDialog.Accepted:
            self._clear_table()
            self.load_user_settings()
            self.update_window_title()
            self.update_status_bar(f"用户 {self.user_manager.current_user} 登录成功", 3000)
            self._load_data_with_progress()
            QTimer.singleShot(5000, self.start_auto_scan)
    
    def show_preset_manager(self):
        """显示预设方案管理对话框"""
        dialog = PresetManagerDialog(self.user_manager, self)
        dialog.exec()
    
    def clear_current_list(self):
        """清空当前列表显示（不删除数据库数据，重新扫描即可恢复）"""
        self._clear_table()
        self.progress_bar.setVisible(False)
        self.progress_label.setText("就绪")
        self.statusBar().showMessage("列表已清空（数据库数据未删除，重新扫描可恢复）", 3000)
    
    def _clear_table(self):
        """清空表格和缓存（切换用户时调用）"""
        self._ensure_table_exists()
        if hasattr(self, 'table_widget') and self.table_widget:
            self.table_widget.setRowCount(0)
        if hasattr(self, '_thumbnail_load_info'):
            self._thumbnail_load_info.clear()
        if hasattr(self, '_thumbnail_timers'):
            for t in self._thumbnail_timers:
                if t.isActive():
                    t.stop()
            self._thumbnail_timers.clear()
        self.clear_pixmap_cache()
        with self._cover_cache_lock:
            self._cover_cache.clear()
        self._stream_cleanup()
        self.statusBar().showMessage("正在切换用户...")
    
    def _ensure_table_exists(self):
        """确保表格控件存在并显示在布局中（即使没有数据也保持布局一致）"""
        if not hasattr(self, 'table_widget') or not self.table_widget:
            self.table_widget = QTableWidget()
            self.table_widget.setColumnCount(6)
            self.table_widget.setHorizontalHeaderLabels(["封面", "目录名称", "其他缩略图", "状态", "目录地址", "文件列表"])
            self.table_widget.setColumnWidth(0, 200)
            self.table_widget.setColumnWidth(1, 200)
            self.table_widget.setColumnWidth(2, 300)
            self.table_widget.setColumnWidth(3, 80)
            self.table_widget.setColumnWidth(4, 250)
            self.table_widget.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
            self.table_widget.verticalHeader().setDefaultSectionSize(150)
            self.table_widget.setRowCount(0)
            self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
            self.table_widget.setAlternatingRowColors(True)
            self.table_widget.cellClicked.connect(self.on_table_cell_clicked)
            layout = self.centralWidget().layout()
            if layout:
                layout.addWidget(self.table_widget)
            if hasattr(self, 'scroll_area') and self.is_widget_valid(self.scroll_area):
                self.scroll_area.hide()

        
    def _indexes_check_only(self, db_path):
        """【修复】只读检查索引是否齐全，**任何线程**都可安全调用。

        线程安全：对共享状态（已检查路径集合 / 连接键）的读写在 _indexes_lock
        保护下完成，避免多 worker 并发读改写产生竞态。
        """
        if not db_path:
            return False
        with self._indexes_lock:
            ready = self._indexes_checked_paths
            if db_path in ready and self._indexes_check_conn_key == db_path:
                return True
        conn = None
        try:
            conn = sqlite3.connect(db_path)   # 只读查询，无写操作
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='index' "
                "AND tbl_name='directories' AND name IN "
                "('idx_directories_name','idx_directories_path',"
                "'idx_directories_last_modified','idx_directories_is_directory')"
            )
            have = cursor.fetchone()[0]
        except Exception as e:
            print(f"[WARN] 检查用户库索引失败: {e}")
            return False
        finally:
            if conn:
                conn.close()
        if have >= 4:
            with self._indexes_lock:
                self._indexes_checked_paths.add(db_path)
                self._indexes_check_conn_key = db_path
            return True
        return False

    def _indexes_ensure(self, db_path=None):
        """【修复】确保索引就绪（缺失才真正建索引）。

        **只允许在主线程的确定时点调用**：login_user（已有）与 load_directories
        开头（此处"正在查询数据库..."已有进度反馈，建索引耗时 0.43-1.29s 可接受）。
        绝不在 get_setting 这类 worker 高频入口上调用，避免阻塞 worker 并与
        SQLite 写入争锁。
        """
        if db_path is None:
            db_path = self.user_manager.current_db_path
        if not db_path:
            return False
        if self._indexes_check_only(db_path):
            return True
        # 索引不全：真正建索引（UserManager 内部幂等，CREATE INDEX IF NOT EXISTS）
        # 【修复 F1】只在确实建成时才写缓存。原先丢弃返回值后无条件标记"已就绪"，
        # 一旦建索引失败（库被锁/磁盘满/只读），进程内将永久认为索引就绪，
        # 导致 13.8x 的性能退化静默持续到下次重启。失败时返回 False 且不写缓存，
        # 由下一次 load_directories 重新检查+重试。
        if not self.user_manager.ensure_user_db_indexes(db_path):
            return False
        with self._indexes_lock:
            self._indexes_checked_paths.add(db_path)
            self._indexes_check_conn_key = db_path
        return True

    def load_user_settings(self):
        if not self.user_manager.current_db_path:
            return
        
        # 从数据库加载主目录
        conn = sqlite3.connect(self.user_manager.current_db_path)
        cursor = conn.cursor()
        
        # 加载主目录设置
        cursor.execute("SELECT value FROM settings WHERE key = 'main_directory'")
        result = cursor.fetchone()
        if result:
            self.main_directory = result[0]
            self.dir_label.setText(f"主目录: {self.main_directory}")
        else:
            self.main_directory = ""
            self.dir_label.setText("主目录: 未设置")
        
        conn.close()

        # 确保启动自动扫描
        self.start_auto_scan()

    def scan_single_main_directory(self, path, depth):
        """扫描单个主目录 - 多线程版本"""
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"准备扫描: {os.path.basename(path)}")
        
        # 获取扫描模式
        scan_mode = self.get_setting('scan_mode', 'directories')
        
        # 创建扫描工作线程
        self.single_scan_worker = DirectoryScanWorker(path, depth, scan_mode, self)
        self.single_scan_thread = QThread()
        
        self.single_scan_worker.moveToThread(self.single_scan_thread)
        self.single_scan_worker.progress_updated.connect(self.on_single_scan_progress)
        self.single_scan_worker.scan_finished.connect(self.on_single_scan_finished)
        self.single_scan_worker.error_occurred.connect(self.on_single_scan_error)
        
        self.single_scan_thread.started.connect(self.single_scan_worker.scan_directory)
        self.single_scan_worker.scan_finished.connect(self.single_scan_thread.quit)
        self.single_scan_worker.scan_finished.connect(self.single_scan_worker.deleteLater)
        self.single_scan_thread.finished.connect(self.single_scan_thread.deleteLater)
        
        self.single_scan_thread.start()

    def on_single_scan_progress(self, progress, message):
        """单目录扫描进度更新"""
        self.progress_bar.setValue(progress // 2)  # 扫描占50%
        self.progress_label.setText(message)

    def on_single_scan_finished(self, directories):
        """单目录扫描完成"""
        # 保存到数据库
        self.save_single_scan_results(directories)

    def save_single_scan_results(self, directories):
        """保存单目录扫描结果"""
        if not directories:
            self.on_scan_completed()
            return
        
        worker = DatabaseSaveWorker(self.user_manager.current_db_path, directories)
        thread = QThread()
        
        worker.moveToThread(thread)
        worker.progress_updated.connect(self.on_single_save_progress)
        worker.save_finished.connect(self.on_single_save_finished)
        worker.error_occurred.connect(self.on_single_scan_error)
        
        thread.started.connect(worker.save_to_database)
        worker.save_finished.connect(thread.quit)
        worker.save_finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        
        # 保持引用防止被垃圾回收
        self._single_save_thread = thread
        self._single_save_worker = worker
        
        thread.start()

    def on_single_save_progress(self, progress, message):
        """单目录保存进度更新"""
        self.progress_bar.setValue(50 + progress // 2)  # 保存占50%
        self.progress_label.setText(message)

    def on_single_save_finished(self, success_count, error_count):
        """单目录保存完成"""
        # 创建备份
        self.backup_manager.create_backup(self.user_manager.current_db_path)
        
        # 更新界面
        self.progress_bar.setValue(100)
        self.progress_label.setText(f"扫描完成: {success_count}成功, {error_count}失败")
        self.load_directories()
        
        # 保存封面（如果启用）
        if self.get_setting('scan_save_cover', '0') == '1':
            cover_dirs = [d for d in self.get_current_directories() if d.get("is_directory", 1) == 1]
            if cover_dirs:
                self.save_covers_async(cover_dirs, *self.get_cover_save_settings())
        
        # 3秒后隐藏进度条
        QTimer.singleShot(3000, self.hide_progress_bar)

    def on_single_scan_error(self, error_message):
        """单目录扫描错误"""
        self.progress_bar.setValue(0)
        self.progress_label.setText("扫描失败")
        QMessageBox.critical(self, "扫描错误", error_message)
        self.hide_progress_bar()

    # 工具方法
    def hide_progress_bar(self):
        """隐藏进度条"""
        self.progress_bar.setVisible(False)
        self.progress_label.setText("就绪")


    def delete_main_directory(self, dir_id):
        """删除主目录"""
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这个主目录吗？\n这不会删除实际文件，只会从列表中移除。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            
            # 删除主目录记录
            cursor.execute("DELETE FROM main_directories WHERE id = ?", (dir_id,))
            
            # 同时删除相关的目录记录（可选）
            # cursor.execute("DELETE FROM directories WHERE is_main_dir = 1 AND path LIKE ?", (f"%{path}%",))
            
            conn.commit()
            
            # 刷新列表
            self.load_main_directories()
            
            QMessageBox.information(self, "成功", "主目录已删除")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除主目录时出错:\n{e}")
        finally:
            if conn:
                conn.close()


    def load_main_directories(self):
        """从数据库加载主目录列表"""
        if not self.user_manager.current_db_path:
            return
        
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, name, path, scan_depth, created_time FROM main_directories ORDER BY created_time DESC")
            main_dirs = cursor.fetchall()
            
            self.main_dir_table.setRowCount(0)
            
            for row_idx, (dir_id, name, path, depth, created_time) in enumerate(main_dirs):
                self.main_dir_table.insertRow(row_idx)
                
                # 名称
                self.main_dir_table.setItem(row_idx, 0, QTableWidgetItem(name))
                
                # 路径
                path_item = QTableWidgetItem(path)
                path_item.setData(Qt.UserRole, dir_id)  # 保存ID以便后续使用
                self.main_dir_table.setItem(row_idx, 1, path_item)
                
                # 扫描深度
                depth_item = QTableWidgetItem(str(depth))
                depth_item.setTextAlignment(Qt.AlignCenter)
                self.main_dir_table.setItem(row_idx, 2, depth_item)
                
                # 操作按钮
                btn_widget = QWidget()
                btn_layout = QHBoxLayout()
                btn_layout.setContentsMargins(0, 0, 0, 0)
                
                scan_btn = QPushButton("扫描")
                scan_btn.clicked.connect(lambda _, p=path, d=depth: self.scan_single_main_directory(p, d))
                scan_btn.setFixedWidth(60)
            
                edit_btn = QPushButton("编辑")
                edit_btn.clicked.connect(lambda _, row=row_idx: self.edit_main_directory(row))
                edit_btn.setFixedWidth(60)
                edit_btn.setStyleSheet("background-color: #4CAF50; color: white;")
            
                delete_btn = QPushButton("删除")
                delete_btn.clicked.connect(lambda _, id=dir_id: self.delete_main_directory(id))
                delete_btn.setFixedWidth(60)
                delete_btn.setStyleSheet("background-color: #ffeb3b;")
                
                btn_layout.addWidget(scan_btn)
                btn_layout.addWidget(edit_btn)
                btn_layout.addWidget(delete_btn)
                btn_widget.setLayout(btn_layout)
                self.main_dir_table.setCellWidget(row_idx, 3, btn_widget)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载主目录时出错:\n{e}")
        finally:
            if conn:
                conn.close()


    def add_main_directory(self):
        """添加新的主目录"""
        path = self.new_main_dir_path.text().strip()
        if not path:
            QMessageBox.warning(self, "无效输入", "目录路径不能为空")
            return
        
        # 不阻塞验证（网络/映射盘可能因延迟误判），扫描时会处理错误
        
        name = self.new_main_dir_name.text().strip()
        if not name:
            name = os.path.basename(path)
        
        scan_depth = self.new_main_dir_depth.value()
        
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            
            # 检查路径是否已经存在
            cursor.execute("SELECT id FROM main_directories WHERE path = ?", (path,))
            if cursor.fetchone():
                QMessageBox.warning(self, "已存在", "该路径已经被添加为主目录")
                return
            
            # 插入新记录
            created_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO main_directories (path, name, scan_depth, created_time) VALUES (?, ?, ?, ?)",
                (path, name, scan_depth, created_time)
            )
            
            conn.commit()
            
            # 清空输入框
            self.new_main_dir_path.clear()
            self.new_main_dir_name.clear()
            
            # 刷新列表
            self.load_main_directories()
            
            QMessageBox.information(self, "成功", "主目录已添加")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加主目录时出错:\n{e}")
        finally:
            if conn:
                conn.close()


    def manage_main_directories(self):
        """管理多个主目录的对话框"""
        if not self.user_manager.current_db_path:
            QMessageBox.warning(self, "未登录", "请先登录用户")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("管理主目录")
        dialog.setMinimumSize(600, 400)

        # 在对话框关闭时自动保存设置
        dialog.finished.connect(self.save_main_directory_settings)

        layout = QVBoxLayout()
        
        # 主目录列表
        self.main_dir_table = QTableWidget()
        self.main_dir_table.setColumnCount(4)
        self.main_dir_table.setHorizontalHeaderLabels(["名称", "路径", "扫描深度", "操作"])
        self.main_dir_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.main_dir_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.main_dir_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.main_dir_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.main_dir_table.verticalHeader().setVisible(False)
        
        # 添加按钮
        add_group = QGroupBox("添加主目录")
        add_layout = QHBoxLayout()
        
        self.new_main_dir_path = QLineEdit()
        self.new_main_dir_path.setPlaceholderText("目录路径")
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(lambda: self.new_main_dir_path.setText(
            QFileDialog.getExistingDirectory(options=QFileDialog.DontUseNativeDialog)))
        
        self.new_main_dir_name = QLineEdit()
        self.new_main_dir_name.setPlaceholderText("显示名称")
        
        self.new_main_dir_depth = QSpinBox()
        self.new_main_dir_depth.setMinimum(0)
        self.new_main_dir_depth.setMaximum(10)
        self.new_main_dir_depth.setValue(3)  # 默认深度为3
        
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self.add_main_directory)
        
        add_layout.addWidget(QLabel("路径:"))
        add_layout.addWidget(self.new_main_dir_path)
        add_layout.addWidget(browse_btn)
        add_layout.addWidget(QLabel("名称:"))
        add_layout.addWidget(self.new_main_dir_name)
        add_layout.addWidget(QLabel("深度:"))
        add_layout.addWidget(self.new_main_dir_depth)
        add_layout.addWidget(add_btn)
        add_group.setLayout(add_layout)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        scan_all_btn = QPushButton("扫描所有主目录")
        scan_all_btn.clicked.connect(self.scan_directories)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        
        btn_layout.addWidget(scan_all_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        
        layout.addWidget(self.main_dir_table)
        layout.addWidget(add_group)
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        
        # 加载主目录
        self.load_main_directories()
        
        dialog.exec()

    def edit_main_directory(self, row):
        """编辑主目录信息"""
        # 获取当前行的数据
        dir_id = self.main_dir_table.item(row, 1).data(Qt.UserRole)
        current_name = self.main_dir_table.item(row, 0).text()
        current_path = self.main_dir_table.item(row, 1).text()
        current_depth = int(self.main_dir_table.item(row, 2).text())
        
        # 创建编辑对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑主目录")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # 名称编辑
        name_layout = QHBoxLayout()
        name_label = QLabel("名称:")
        self.edit_name_input = QLineEdit(current_name)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.edit_name_input)
        
        # 路径编辑
        path_layout = QHBoxLayout()
        path_label = QLabel("路径:")
        self.edit_path_input = QLineEdit(current_path)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(lambda: self.edit_path_input.setText(
            QFileDialog.getExistingDirectory(options=QFileDialog.DontUseNativeDialog)))
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.edit_path_input)
        path_layout.addWidget(browse_btn)
        
        # 深度编辑
        depth_layout = QHBoxLayout()
        depth_label = QLabel("扫描深度:")
        self.edit_depth_input = QSpinBox()
        self.edit_depth_input.setMinimum(0)
        self.edit_depth_input.setMaximum(10)
        self.edit_depth_input.setValue(current_depth)
        depth_layout.addWidget(depth_label)
        depth_layout.addWidget(self.edit_depth_input)
        
        # 按钮
        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(lambda: self.save_main_directory_edit(dialog, dir_id, row))
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        # 添加所有控件到布局
        layout.addLayout(name_layout)
        layout.addLayout(path_layout)
        layout.addLayout(depth_layout)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec()


    def save_main_directory_settings(self):
        """保存主目录设置到数据库"""
        if not self.user_manager.current_db_path:
            return
        
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            
            # 保存当前主目录
            if self.main_directory:
                cursor.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    ("main_directory", self.main_directory)
                )
            
            conn.commit()
        except Exception as e:
            print(f"保存主目录设置失败: {e}")
        finally:
            if conn:
                conn.close()


    def save_main_directory_edit(self, dialog, dir_id, row):
        """保存主目录编辑"""
        new_name = self.edit_name_input.text().strip()
        new_path = self.edit_path_input.text().strip()
        new_depth = self.edit_depth_input.value()
        
        if not new_path:
            QMessageBox.warning(dialog, "无效输入", "目录路径不能为空")
            return
        
        # 不阻塞验证，扫描时处理错误
        
        if not new_name:
            new_name = os.path.basename(new_path)
        
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            
            # 检查路径是否已被其他记录使用
            cursor.execute("SELECT id FROM main_directories WHERE path = ? AND id != ?", (new_path, dir_id))
            if cursor.fetchone():
                QMessageBox.warning(dialog, "路径冲突", "该路径已经被其他主目录使用")
                return
            
            # 更新记录
            cursor.execute(
                "UPDATE main_directories SET name = ?, path = ?, scan_depth = ? WHERE id = ?",
                (new_name, new_path, new_depth, dir_id)
            )
            
            conn.commit()
            
            # 更新表格显示
            self.main_dir_table.item(row, 0).setText(new_name)
            self.main_dir_table.item(row, 1).setText(new_path)
            self.main_dir_table.item(row, 2).setText(str(new_depth))
            
            QMessageBox.information(dialog, "成功", "主目录信息已更新")
            dialog.accept()
            
        except Exception as e:
            QMessageBox.critical(dialog, "错误", f"更新主目录时出错:\n{e}")
        finally:
            if conn:
                conn.close()



    def scan_directories(self):
        """多线程扫描目录（支持增量扫描）"""
        # 检查是否启用增量扫描
        use_incremental = self.get_setting('incremental_scan', '1') == '1'
        
        if use_incremental:
            self.scan_manager.incremental_mode = True
            self.update_status_bar("使用增量扫描模式（仅扫描变化的目录）", 3000)
        else:
            self.scan_manager.incremental_mode = False
            self.update_status_bar("使用全量扫描模式", 3000)
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("准备扫描...")
        
        # 开始扫描
        self.scan_manager.scan_all_directories()
    
    def on_scan_progress_updated(self, progress, message):
        """扫描进度更新"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(message)
        self.update_status_bar(message)
    
    def on_scan_completed(self):
        """扫描完成 - 委托 load_directories 管理进度条"""
        self.progress_label.setText("扫描完成，正在加载数据...")
        self.load_directories()  # load_directories 内部自行管理进度条
    
    def on_scan_error(self, error_message):
        """扫描错误"""
        self.progress_bar.setValue(0)
        self.progress_label.setText("扫描失败")
        QMessageBox.critical(self, "扫描错误", error_message)
        self.hide_progress_bar()
        

    




    def load_directories(self):
        """加载目录数据到表格（优化版：进度反馈 + 延迟加载）"""
        if not self.user_manager.current_db_path:
            return
        
        # 获取文件显示模式设置
        file_display_mode = self.get_setting('file_display_mode', 'all')
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("正在查询数据库...")
        QApplication.processEvents()
        if hasattr(self, '_thumbnail_timers'):
            for timer in self._thumbnail_timers:
                if timer.isActive():
                    timer.stop()
        self._thumbnail_timers = []
        
        conn = None
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            
            # 设置数据库优化参数
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA cache_size=-40000")  # 40MB缓存（原 2MB 太小，大库分页会频繁读盘）
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.execute("PRAGMA mmap_size=268435456")  # 256MB 内存映射，减少 read 系统调用
            cursor.execute("PRAGMA query_only=ON")  # 【性能优化】本连接纯读取，杜绝误写
            
            # 【性能优化】确保索引就绪（历史库从未建过索引，退化为全表排序，慢 13.8 倍）
            # 【修复】这里是主线程的确定时点（用户可见"正在查询数据库..."，已有进度反馈），
            # 索引缺失时在此真正建索引；不放在 get_setting 那种 worker 高频入口上。
            self._indexes_ensure()
            
            # 先验证表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='directories'")
            if not cursor.fetchone():
                self._ensure_table_exists()
                self._is_loading = False
                self.progress_bar.setVisible(False)
                self.progress_label.setText("就绪")
                self.statusBar().showMessage("数据库表不存在，请先扫描目录")
                return
            
            # 【性能优化】无效数据清理：原先每次刷新都无条件 DELETE + commit，
            # 在纯读连接上写事务会把 WAL 撑大并触发全表扫描。改为先用主键索引
            # 零成本探测是否真的存在脏行，只有存在时才清理；正常情况下跳过整个写事务。
            cursor.execute("PRAGMA query_only=OFF")  # 清理分支需要写权限（只影响本连接）
            cursor.execute("""
                SELECT id FROM directories
                WHERE name IS NULL OR name = '' OR path IS NULL OR path = ''
                LIMIT 1
            """)
            if cursor.fetchone() is not None:
                cursor.execute("""
                    DELETE FROM directories 
                    WHERE name IS NULL OR name = '' OR path IS NULL OR path = ''
                """)
                conn.commit()
            cursor.execute("PRAGMA query_only=ON")
            
            # 获取总记录数
            cursor.execute("SELECT COUNT(*) FROM directories WHERE name IS NOT NULL AND name != '' AND path IS NOT NULL AND path != ''")
            total_count = cursor.fetchone()[0]
            
            if total_count == 0:
                self.statusBar().showMessage("没有找到目录数据")
                self._ensure_table_exists()
                self._is_loading = False
                self.progress_bar.setVisible(False)
                self.progress_label.setText("就绪")
                return
            
            # 更新进度：数据库查询中
            self.progress_bar.setValue(10)
            self.progress_label.setText(f"查询数据库中... 共 {total_count} 条记录")
            QApplication.processEvents()
            
            # 确保表格控件存在
            self._ensure_table_exists()
            
            # 设置表格结构
            self.table_widget.setColumnCount(6)
            self.table_widget.setHorizontalHeaderLabels(["封面", "目录名称", "其他缩略图", "状态", "目录地址", "文件列表"])
            self.table_widget.setColumnWidth(0, 200)
            self.table_widget.setColumnWidth(1, 200)
            self.table_widget.setColumnWidth(2, 300)
            self.table_widget.setColumnWidth(3, 80)
            self.table_widget.setColumnWidth(4, 250)
            self.table_widget.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
            self.table_widget.verticalHeader().setDefaultSectionSize(150)
            self.table_widget.setSortingEnabled(False)
            
            # ===== 流式加载：QTimer 协作调度（不阻塞事件循环） =====
            self._is_loading = True
            self._thumbnail_load_info = {}
            self.table_widget.setUpdatesEnabled(False)
            
            # 保存流式加载状态为实例变量（供 QTimer 回调使用）
            self._stream_conn = conn
            self._stream_cursor = cursor
            self._stream_last_name = ''
            self._stream_seen_paths = set()
            self._stream_valid_count = 0
            self._stream_batch_index = 0
            self._stream_total_count = total_count
            self._stream_file_display_mode = file_display_mode
            conn = None  # 防止 finally 中重复关闭
            
            self.progress_bar.setValue(10)
            self.progress_label.setText(f"流式加载中... 共 {total_count} 条")
            
            # 启动第一个批次（QTimer 驱动，不阻塞事件循环）
            QTimer.singleShot(0, self._stream_load_next_batch)
            return  # 提前返回，后续由 QTimer 链 + _stream_load_finished 处理
        
        except sqlite3.Error as e:
            self._stream_cleanup()
            self.progress_bar.setVisible(False)
            self.progress_label.setText("就绪")
            QMessageBox.critical(self, "数据库错误", f"读取数据库时出错:\n{e}")
        except Exception as e:
            self._stream_cleanup()
            self.progress_bar.setVisible(False)
            self.progress_label.setText("就绪")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "加载错误", f"加载目录时发生错误:\n{e}")

    # ===== 多线程并行加载：将行数据分块，在线程池中并行处理I/O =====
    
    def _prepare_row_data_offthread(self, row, info, load_type):
        """在Worker线程中执行纯I/O操作（不碰GUI），返回准备好的数据字典
        支持三种load_type: 'cover' | 'thumbnails' | 'files'
        """
        result = {}
        path = info['path']
        is_directory = info['is_directory']
        file_display_mode = info.get('file_display_mode', 'all')
        
        try:
            if load_type == 'cover':
                if is_directory == 1:
                    cover_path = self.find_cover_image(path)
                    if cover_path and os.path.exists(cover_path):
                        pixmap = self.safe_load_and_scale_image(cover_path, 180, 120)
                        result['cover_pixmap'] = pixmap if pixmap and not pixmap.isNull() else None
                        result['cover_path'] = cover_path
                    else:
                        result['cover_pixmap'] = None
                        result['cover_path'] = None
                else:
                    if path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')) and os.path.exists(path):
                        pixmap = self.safe_load_and_scale_image(path, 180, 120)
                        result['cover_pixmap'] = pixmap if pixmap and not pixmap.isNull() else None
                        result['cover_path'] = path
                    else:
                        result['cover_pixmap'] = None
                        result['cover_path'] = None
                
            elif load_type == 'thumbnails':
                if is_directory == 1:
                    all_images = self.find_all_images(path, use_multithreading=False)
                    cover_path = self.find_cover_image(path)
                    
                    # 过滤掉封面，限制最多8张
                    unique_images = []
                    for img in all_images:
                        if cover_path and os.path.abspath(img) == os.path.abspath(cover_path):
                            continue
                        unique_images.append(img)
                        if len(unique_images) >= 8:
                            break
                    
                    # 在线程中预加载缩略图pixmap
                    thumb_pixmaps = []
                    for img_path in unique_images:
                        pixmap = self.safe_load_and_scale_image(img_path, 80, 60)
                        if pixmap and not pixmap.isNull():
                            thumb_pixmaps.append((img_path, pixmap))
                    
                    result['thumb_pixmaps'] = thumb_pixmaps
                    result['thumb_total'] = len(unique_images)
                else:
                    result['thumb_pixmaps'] = []
                    result['thumb_total'] = 0
                    
            elif load_type == 'files':
                if is_directory == 1 and os.path.isdir(path):
                    # 在线程中列出并分类文件
                    image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.ico']
                    video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg']
                    document_extensions = ['.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
                                          '.epub', '.mobi', '.azw', '.rtf', '.odt', '.ods', '.odp']
                    
                    all_files = []
                    try:
                        for item in os.listdir(path):
                            item_path = os.path.join(path, item)
                            if os.path.isfile(item_path):
                                all_files.append(item)
                    except PermissionError:
                        pass
                    
                    # 根据显示模式筛选
                    display_files = []
                    if file_display_mode == 'images':
                        display_files = [f for f in all_files if any(f.lower().endswith(ext) for ext in image_extensions)]
                    elif file_display_mode == 'videos':
                        display_files = [f for f in all_files if any(f.lower().endswith(ext) for ext in video_extensions)]
                    elif file_display_mode == 'documents':
                        display_files = [f for f in all_files if any(f.lower().endswith(ext) for ext in document_extensions)]
                    elif file_display_mode == 'none':
                        display_files = []
                    else:  # 'all'
                        display_files = [f for f in all_files if not any(f.lower().endswith(ext) for ext in image_extensions)]
                    
                    result['file_names'] = display_files[:8]  # 最多8个
                    result['file_total'] = len(display_files)
                    result['file_all_count'] = len(all_files)
                else:
                    result['file_names'] = []
                    result['file_total'] = 0
                    result['file_all_count'] = 0
                    
        except Exception as e:
            print(f"[PREPARE ERROR] 准备行{row}的{load_type}数据失败: {e}")
            result['error'] = str(e)
        
        return result
    
    def _apply_row_data_mainthread(self, row, prepared, info, load_type):
        """在主线程中将准备好的数据应用到GUI控件"""
        if hasattr(self, '_is_closing') and self._is_closing:
            return
        if not hasattr(self, 'table_widget') or self.table_widget is None:
            return
        if row >= self.table_widget.rowCount():
            return
        
        is_directory = info['is_directory']
        
        try:
            if load_type == 'cover':
                cover_widget = self.table_widget.cellWidget(row, 0)
                if cover_widget and isinstance(cover_widget, QLabel):
                    cover_pixmap = prepared.get('cover_pixmap')
                    cover_path = prepared.get('cover_path')
                    if cover_pixmap:
                        cover_widget.setPixmap(cover_pixmap)
                        if cover_path:
                            cover_widget.mousePressEvent = lambda event, img_path=cover_path: self.on_image_clicked(event, img_path)
                    elif cover_path:
                        cover_widget.setText("📁\n无图片" if is_directory == 1 else "📄\n非图片文件")
                    else:
                        cover_widget.setText("📁" if is_directory == 1 else "📄")
                info['loaded_cover'] = True
                
            elif load_type == 'thumbnails':
                thumb_pixmaps = prepared.get('thumb_pixmaps', [])
                thumb_total = prepared.get('thumb_total', 0)
                
                # 创建缩略图容器
                container = QWidget()
                layout = QHBoxLayout()
                layout.setContentsMargins(2, 2, 2, 2)
                layout.setSpacing(2)
                container.setLayout(layout)
                
                if thumb_pixmaps:
                    for img_path, pixmap in thumb_pixmaps[:8]:
                        thumb_label = QLabel()
                        thumb_label.setFixedSize(80, 60)
                        thumb_label.setAlignment(Qt.AlignCenter)
                        thumb_label.setCursor(Qt.PointingHandCursor)
                        thumb_label.setStyleSheet("border: 1px solid #ddd; background-color: #f8f9fa; border-radius: 3px;")
                        thumb_label.setPixmap(pixmap)
                        thumb_label.mousePressEvent = self.create_thumbnail_click_handler(img_path)
                        layout.addWidget(thumb_label)
                    
                    if thumb_total > 8:
                        more_label = QLabel(f"+{thumb_total - 8}")
                        more_label.setAlignment(Qt.AlignCenter)
                        more_label.setStyleSheet("color: #666; font-size: 10px;")
                        layout.addWidget(more_label)
                else:
                    no_image_label = QLabel("📷\n无图片")
                    no_image_label.setAlignment(Qt.AlignCenter)
                    no_image_label.setFixedSize(80, 60)
                    no_image_label.setStyleSheet("""
                        QLabel {
                            color: #999; font-size: 10px;
                            background-color: #f8f9fa; border: 1px solid #ddd; border-radius: 3px;
                        }
                    """)
                    layout.addWidget(no_image_label)
                
                if hasattr(self, 'table_widget') and self.table_widget is not None:
                    if row < self.table_widget.rowCount():
                        self.table_widget.setCellWidget(row, 2, container)
                info['loaded_thumbnails'] = True
                
            elif load_type == 'files':
                file_names = prepared.get('file_names', [])
                file_total = prepared.get('file_total', 0)
                file_all_count = prepared.get('file_all_count', 0)
                path = info['path']
                
                file_container = QWidget()
                file_layout = QHBoxLayout()
                file_layout.setContentsMargins(2, 2, 2, 2)
                file_layout.setSpacing(4)
                file_container.setLayout(file_layout)
                
                if not file_names:
                    no_file_label = QLabel("📭 无文件")
                    no_file_label.setStyleSheet("color: #999; font-size: 11px;")
                    file_layout.addWidget(no_file_label)
                else:
                    scroll_area = QScrollArea()
                    scroll_area.setWidgetResizable(True)
                    scroll_area.setFixedHeight(120)
                    scroll_area.setStyleSheet("""
                        QScrollArea {
                            border: 1px solid #dee2e6; border-radius: 3px;
                            background-color: #f8f9fa;
                        }
                    """)
                    
                    files_inner = QWidget()
                    files_inner_layout = QVBoxLayout()
                    files_inner_layout.setContentsMargins(4, 4, 4, 4)
                    files_inner_layout.setSpacing(2)
                    
                    for file_name in file_names:
                        file_path = os.path.join(path, file_name)
                        file_widget = self.create_file_item_widget(file_name, file_path)
                        files_inner_layout.addWidget(file_widget)
                    
                    files_inner.setLayout(files_inner_layout)
                    scroll_area.setWidget(files_inner)
                    file_layout.addWidget(scroll_area)
                    
                    remaining = file_all_count - len(file_names)
                    if remaining > 0:
                        more_label = QLabel(f"... 还有 {remaining} 个文件")
                        more_label.setStyleSheet("color: #666; font-size: 10px;")
                        file_layout.addWidget(more_label)
                
                if hasattr(self, 'table_widget') and self.table_widget is not None:
                    if row < self.table_widget.rowCount():
                        self.table_widget.setCellWidget(row, 5, file_container)
                info['loaded_files'] = True
                
        except RuntimeError as e:
            if "wrapped C/C++ object" in str(e):
                pass
            else:
                print(f"[ERROR] 应用行数据失败 row {row}: {e}")
        except Exception as e:
            print(f"[ERROR] 应用行数据失败 row {row}: {e}")
    
    # ===== QTimer 协作式流式加载（不阻塞事件循环，UI 始终流畅） =====
    
    def _stream_load_next_batch(self):
        """处理下一批数据，然后通过 QTimer 调度下一批（协作式多任务）"""
        if hasattr(self, '_is_closing') and self._is_closing:
            self._stream_cleanup()
            return
        
        stream_batch_size = 200
        
        # --- 阶段1：keyset分页查询 ---
        if self._stream_last_name:
            self._stream_cursor.execute("""
                SELECT name, path, directory_exists, created_time, last_modified, is_directory 
                FROM directories 
                WHERE name IS NOT NULL AND name != '' 
                AND path IS NOT NULL AND path != ''
                AND name > ?
                ORDER BY name
                LIMIT ?
            """, (self._stream_last_name, stream_batch_size))
        else:
            self._stream_cursor.execute("""
                SELECT name, path, directory_exists, created_time, last_modified, is_directory 
                FROM directories 
                WHERE name IS NOT NULL AND name != '' 
                AND path IS NOT NULL AND path != ''
                ORDER BY name
                LIMIT ?
            """, (stream_batch_size,))
        
        batch = self._stream_cursor.fetchall()
        
        if not batch:
            # 全部完成
            self._stream_load_finished()
            return
        
        self._stream_last_name = batch[-1][0]
        self._stream_batch_index += 1
        
        # --- 阶段2：快速校验去重 ---
        valid_batch = []
        for name, path, exists, created_time, last_modified, is_directory in batch:
            if (name and name.strip() and 
                path and path.strip() and 
                path not in self._stream_seen_paths):
                valid_batch.append((name, path, exists, created_time, last_modified, is_directory))
                self._stream_seen_paths.add(path)
        
        # --- 阶段3：追加到表格（局部变量缓存避免 self. 属性查找） ---
        if valid_batch:
            tw = self.table_widget
            new_start = self._stream_valid_count
            new_end = new_start + len(valid_batch)
            tw.setRowCount(new_end)
            fm = self._stream_file_display_mode
            
            # 缓存所有 self.xxx 为局部变量（避免循环中重复属性查找）
            bg_green = self._BRUSH_GREEN
            bg_red = self._BRUSH_RED
            bg_white = self._BRUSH_WHITE
            bg_blue = self._BRUSH_BLUE
            # 【性能优化】表格级共用 QSS 只设一次（循环外），循环内用 setObjectName 区分
            self._apply_table_qss()
            thumb_info = self._thumbnail_load_info
            align_center = Qt.AlignCenter
            pointing_hand = Qt.PointingHandCursor
            item_not_editable = ~Qt.ItemIsEditable
            
            for i, (name, path, exists, _ct, _lm, is_directory) in enumerate(valid_batch):
                row_idx = new_start + i
                tw.setRowHeight(row_idx, 150)
                
                # 封面占位符
                cw = QLabel("📁" if is_directory == 1 else "📄")
                cw.setFixedSize(180, 120)
                cw.setAlignment(align_center)
                cw.setCursor(pointing_hand)
                # 【性能优化】改表格级共用 QSS，循环内只设 objectName（等价样式，见 _STYLE_* 定义）
                cw.setObjectName("coverPlaceholder")
                tw.setCellWidget(row_idx, 0, cw)
                
                # 目录名称
                ni = QTableWidgetItem(name)
                ni.setFlags(ni.flags() & item_not_editable)
                tw.setItem(row_idx, 1, ni)
                
                # 缩略图占位符
                tw_ph = QLabel("📷 加载中...")
                tw_ph.setFixedSize(280, 120)
                tw_ph.setAlignment(align_center)
                tw_ph.setObjectName("thumbPlaceholder")
                tw.setCellWidget(row_idx, 2, tw_ph)
                
                # 状态
                si = QTableWidgetItem("上架" if exists else "下架")
                si.setFlags(si.flags() & item_not_editable)
                if exists:
                    si.setBackground(bg_green)
                    si.setForeground(bg_white)
                else:
                    si.setBackground(bg_red)
                    si.setForeground(bg_white)
                tw.setItem(row_idx, 3, si)
                
                # 目录地址
                pi = QTableWidgetItem(path)
                pi.setFlags(pi.flags() & item_not_editable)
                pi.setForeground(bg_blue)
                tw.setItem(row_idx, 4, pi)
                
                # 文件列表占位符
                fp = QLabel("📂 加载中...")
                fp.setAlignment(align_center)
                fp.setObjectName("filePlaceholder")
                fp.setCursor(pointing_hand)
                tw.setCellWidget(row_idx, 5, fp)
                
                thumb_info[row_idx] = {
                    'path': path, 'is_directory': is_directory,
                    'file_display_mode': fm,
                    'loaded_cover': False, 'loaded_thumbnails': False, 'loaded_files': False
                }
            
            self._stream_valid_count = new_end
            
            # 进度反馈（每5批更新一次）
            if self._stream_batch_index % 5 == 0:
                pct = 10 + int((self._stream_valid_count / self._stream_total_count) * 82)
                self.progress_bar.setValue(pct)
                self.progress_label.setText(f"流式加载中... {self._stream_valid_count} 行已显示")
        
        # 调度下一批（0ms = 立即交还控制权给事件循环）
        QTimer.singleShot(0, self._stream_load_next_batch)
    
    def _stream_load_finished(self):
        """流式加载全部完成"""
        total_valid = self._stream_valid_count
        
        # 清理流式状态
        self._stream_cleanup()
        
        # 重新启用表格更新
        self.table_widget.setUpdatesEnabled(True)
        
        self.progress_bar.setValue(92)
        self.progress_label.setText("启动缩略图加载...")
        
        self.table_widget.cellClicked.connect(self.on_table_cell_clicked)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.setAlternatingRowColors(True)
        if total_valid < 5000:
            self.table_widget.setSortingEnabled(True)
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        
        self.statusBar().showMessage(f"加载了 {total_valid} 个有效目录")
        self._is_loading = False
        
        # 启动缩略图异步加载
        self.start_thumbnail_loading()
    
    def _stream_cleanup(self):
        """清理流式加载的临时资源"""
        if hasattr(self, '_stream_conn') and self._stream_conn:
            try:
                self._stream_conn.close()
            except:
                pass
        # 清理流式状态变量
        for attr in ['_stream_conn', '_stream_cursor', '_stream_last_name', 
                     '_stream_seen_paths', '_stream_valid_count', '_stream_batch_index',
                     '_stream_total_count', '_stream_file_display_mode']:
            if hasattr(self, attr):
                delattr(self, attr)
    
    def start_thumbnail_loading(self):
        """分阶段延迟加载：封面 → 缩略图 → 文件列表，统一进度条直到全部完成"""
        if not hasattr(self, '_thumbnail_load_info') or not self._thumbnail_load_info:
            self._on_all_loading_complete()
            return
        
        # 首次调用时计算总工作量
        if not hasattr(self, '_load_total_count'):
            cover_count = len([r for r, i in self._thumbnail_load_info.items() if not i.get('loaded_cover', False)])
            thumb_count = len([r for r, i in self._thumbnail_load_info.items() if not i.get('loaded_thumbnails', False)])
            file_count = len([r for r, i in self._thumbnail_load_info.items() if not i.get('loaded_files', False)])
            self._load_total_count = cover_count + thumb_count + file_count
            self._load_completed_count = 0
            if self._load_total_count > 0:
                self.progress_bar.setValue(92)
                self.progress_label.setText(f"加载封面/缩略图/文件列表... 共 {self._load_total_count} 项")
        
        # 阶段1: 先加载封面图片
        cover_rows = [row for row, info in self._thumbnail_load_info.items() if not info.get('loaded_cover', False)]
        if cover_rows:
            self._deferred_load_worker_parallel(cover_rows, 'cover', 20, 80)
            return
        
        # 阶段2: 加载其他缩略图
        thumb_rows = [row for row, info in self._thumbnail_load_info.items() if not info.get('loaded_thumbnails', False)]
        if thumb_rows:
            self._deferred_load_worker_parallel(thumb_rows, 'thumbnails', 20, 150)
            return
        
        # 阶段3: 加载文件列表
        file_rows = [row for row, info in self._thumbnail_load_info.items() if not info.get('loaded_files', False)]
        if file_rows:
            self._deferred_load_worker_parallel(file_rows, 'files', 30, 200)
            return
        
        # 全部完成
        self._on_all_loading_complete()
    
    def _on_all_loading_complete(self):
        """所有加载阶段完成，进度条到100%并延迟隐藏，释放跟踪内存"""
        self.progress_bar.setValue(100)
        self.progress_label.setText("加载完成")
        # 清理跟踪变量和已完成的加载信息（释放内存）
        if hasattr(self, '_load_total_count'):
            del self._load_total_count
        if hasattr(self, '_load_completed_count'):
            del self._load_completed_count
        # 清理已完成条目的缩略图信息（保留未完成的给后续增量加载）
        if hasattr(self, '_thumbnail_load_info'):
            done_keys = [k for k, v in self._thumbnail_load_info.items() 
                        if v.get('loaded_cover') and v.get('loaded_thumbnails') and v.get('loaded_files')]
            for k in done_keys:
                del self._thumbnail_load_info[k]
        # 2秒后隐藏进度条
        QTimer.singleShot(2000, self._hide_loading_progress)
    
    def _update_load_progress(self, completed_increment):
        """更新加载进度（节流：仅每10项更新一次进度条）"""
        if hasattr(self, '_load_completed_count') and hasattr(self, '_load_total_count'):
            self._load_completed_count += completed_increment
            if self._load_total_count > 0 and self._load_completed_count % 10 == 0:
                pct = 92 + int((self._load_completed_count / self._load_total_count) * 8)
                self.progress_bar.setValue(min(pct, 99))
                self.progress_label.setText(f"加载中... {self._load_completed_count}/{self._load_total_count}")
    
    def _deferred_load_worker_parallel(self, rows, load_type, batch_size, delay_ms):
        """多线程并行延迟加载工作器
        将行列表分块，每个块在线程池中并行处理I/O，然后回到主线程更新GUI"""
        cpu_count = os.cpu_count() or 4
        # 根据负载类型调整并发数：封面和缩略图I/O重，用较多线程；文件列表I/O轻，用较少线程
        if load_type == 'cover':
            max_workers = min(cpu_count, 8)
        elif load_type == 'thumbnails':
            max_workers = min(cpu_count, 6)
        else:
            max_workers = min(cpu_count, 4)
        
        def load_batch():
            if hasattr(self, '_is_closing') and self._is_closing:
                return
            if not rows:
                return
            
            # 取一批行
            batch = rows[:batch_size]
            for row in batch:
                if row in rows:
                    rows.remove(row)
            
            if not batch:
                if rows:
                    QTimer.singleShot(delay_ms, load_batch)
                else:
                    QTimer.singleShot(200, self.start_thumbnail_loading)
                return
            
            # 将这批行分成多个块，每个块交给线程池处理
            chunk_size = max(1, len(batch) // max_workers)
            chunks = [batch[i:i + chunk_size] for i in range(0, len(batch), chunk_size)]
            
            def process_chunk(chunk_rows):
                """在Worker线程中处理一个块：只做I/O，不碰GUI"""
                chunk_results = []
                for row in chunk_rows:
                    info = self._thumbnail_load_info.get(row)
                    if info:
                        prepared = self._prepare_row_data_offthread(row, info, load_type)
                        chunk_results.append((row, prepared, info))
                return chunk_results
            
            # 使用线程池并行处理所有块
            all_results = []
            with ThreadPoolExecutor(max_workers=min(len(chunks), max_workers)) as executor:
                futures = [executor.submit(process_chunk, chunk) for chunk in chunks]
                for future in as_completed(futures):
                    try:
                        chunk_results = future.result()
                        if chunk_results:
                            all_results.extend(chunk_results)
                    except Exception as e:
                        print(f"[LOAD ERROR] 并行处理块失败: {e}")
            
            # 在主线程中应用GUI更新（通过QTimer确保在主线程执行）
            if all_results:
                def apply_all():
                    count = len(all_results)
                    for row, prepared, info in all_results:
                        self._apply_row_data_mainthread(row, prepared, info, load_type)
                    # 更新进度条
                    self._update_load_progress(count)
                    QApplication.processEvents()
                
                QTimer.singleShot(0, apply_all)
            
            # 继续处理剩余行
            if rows:
                QTimer.singleShot(delay_ms, load_batch)
            else:
                # 当前阶段完成，启动下一阶段
                QTimer.singleShot(300, self.start_thumbnail_loading)
        
        QTimer.singleShot(200, load_batch)

    def load_thumbnail_for_row(self, row, path, is_directory):
        """为指定行加载缩略图（在_load_row_content中调用）"""
        if hasattr(self, '_is_closing') and self._is_closing:
            return
        if not hasattr(self, 'table_widget') or self.table_widget is None:
            return
        if row >= self.table_widget.rowCount():
            return
        
        try:
            if is_directory == 1:
                all_images = self.find_all_images(path, use_multithreading=False)  # 使用串行处理避免线程问题
                
                # 获取封面图片路径
                cover_path = self.find_cover_image(path)
                
                # 过滤掉封面图片，限制最大数量
                unique_images = []
                for img in all_images:
                    if cover_path and os.path.abspath(img) == os.path.abspath(cover_path):
                        continue
                    unique_images.append(img)
                    if len(unique_images) >= 8:
                        break
                
                # 再次检查表格部件和行是否有效
                if not hasattr(self, 'table_widget') or self.table_widget is None:
                    return
                if row >= self.table_widget.rowCount():
                    return
                
                # 创建缩略图容器
                container = QWidget()
                layout = QHBoxLayout()
                layout.setContentsMargins(2, 2, 2, 2)
                layout.setSpacing(2)
                container.setLayout(layout)
                
                if unique_images:
                    for img_path in unique_images[:8]:
                        thumb_label = QLabel()
                        thumb_label.setFixedSize(80, 60)
                        thumb_label.setAlignment(Qt.AlignCenter)
                        thumb_label.setCursor(Qt.PointingHandCursor)
                        thumb_label.setStyleSheet("border: 1px solid #ddd; background-color: #f8f9fa; border-radius: 3px;")
                        
                        # 设置预览图片
                        self.set_preview_image(thumb_label, img_path)
                        thumb_label.mousePressEvent = self.create_thumbnail_click_handler(img_path)
                        layout.addWidget(thumb_label)
                    
                    if len(unique_images) > 8:
                        more_label = QLabel(f"+{len(unique_images) - 8}")
                        more_label.setAlignment(Qt.AlignCenter)
                        more_label.setStyleSheet("color: #666; font-size: 10px;")
                        layout.addWidget(more_label)
                else:
                    # 没有图片时显示提示
                    no_image_label = QLabel("📷\n无图片")
                    no_image_label.setAlignment(Qt.AlignCenter)
                    no_image_label.setFixedSize(80, 60)
                    no_image_label.setStyleSheet("""
                        QLabel {
                            color: #999;
                            font-size: 10px;
                            background-color: #f8f9fa;
                            border: 1px solid #ddd;
                            border-radius: 3px;
                        }
                    """)
                    layout.addWidget(no_image_label)
                
                # 最终检查并设置
                if hasattr(self, 'table_widget') and self.table_widget is not None:
                    if row < self.table_widget.rowCount():
                        self.table_widget.setCellWidget(row, 2, container)
                        
            else:
                # 文件类型，显示文件图标
                file_label = QLabel("📄")
                file_label.setAlignment(Qt.AlignCenter)
                file_label.setFixedSize(280, 120)
                file_label.setStyleSheet("font-size: 48px; color: #999; background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 3px;")
                
                if hasattr(self, 'table_widget') and self.table_widget is not None:
                    if row < self.table_widget.rowCount():
                        self.table_widget.setCellWidget(row, 2, file_label)
                        
        except RuntimeError as e:
            if "wrapped C/C++ object" in str(e):
                pass
            else:
                print(f"[ERROR] 加载缩略图失败 row {row}: {e}")
        except Exception as e:
            print(f"[ERROR] 加载缩略图失败 row {row}: {e}")
            # 设置错误显示
            try:
                error_label = QLabel("❌ 加载失败")
                error_label.setAlignment(Qt.AlignCenter)
                error_label.setFixedSize(280, 120)
                error_label.setStyleSheet("""
                    QLabel {
                        color: #dc3545;
                        font-size: 12px;
                        background-color: #f8d7da;
                        border: 1px solid #f5c6cb;
                        border-radius: 3px;
                    }
                """)
                
                if hasattr(self, 'table_widget') and self.table_widget is not None:
                    if row < self.table_widget.rowCount():
                        self.table_widget.setCellWidget(row, 2, error_label)
            except:
                pass

    def create_thumbnails_widget(self, path, is_directory):
        """创建其他缩略图组件 - 修复版本"""
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        container.setLayout(layout)

        if is_directory == 1:  # 如果是目录
            # 查找所有图片
            all_images = self.find_all_images(path, use_multithreading=True)
            
            # 获取封面图片路径
            cover_path = self.find_cover_image(path)
            
            # 过滤掉封面图片
            unique_images = []
            for img in all_images:
                if cover_path and os.path.abspath(img) == os.path.abspath(cover_path):
                    continue
                unique_images.append(img)
                if len(unique_images) >= 8:  # 限制最多8个
                    break
            
            if unique_images:
                # 创建缩略图
                for img_path in unique_images:
                    thumb_label = QLabel()
                    thumb_label.setFixedSize(80, 60)
                    thumb_label.setAlignment(Qt.AlignCenter)
                    thumb_label.setCursor(Qt.PointingHandCursor)
                    thumb_label.setStyleSheet("border: 1px solid #ddd; background-color: #f8f9fa;")
                    
                    self.set_preview_image(thumb_label, img_path)
                    thumb_label.mousePressEvent = self.create_thumbnail_click_handler(img_path)
                    layout.addWidget(thumb_label)
                
                # 如果还有其他图片但被限制了显示，显示提示信息
                if len(all_images) - len(unique_images) > 8:
                    more_label = QLabel(f"+{len(all_images) - len(unique_images)}")
                    more_label.setAlignment(Qt.AlignCenter)
                    more_label.setStyleSheet("color: #666; font-size: 10px;")
                    layout.addWidget(more_label)
            else:
                # 没有图片时显示提示
                no_image_label = QLabel("📷\n无图片")
                no_image_label.setAlignment(Qt.AlignCenter)
                no_image_label.setFixedSize(80, 60)
                no_image_label.setStyleSheet("color: #999; font-size: 10px; background-color: #f8f9fa; border: 1px solid #ddd;")
                layout.addWidget(no_image_label)
            
            # 存储缩略图路径以便点击事件使用
            container.thumbnail_paths = unique_images

        else:  # 如果是文件
            # 单个文件，显示文件图标
            file_label = QLabel("📄")
            file_label.setAlignment(Qt.AlignCenter)
            file_label.setFixedSize(80, 60)
            file_label.setStyleSheet("font-size: 32px; color: #999; background-color: #f8f9fa; border: 1px solid #ddd;")
            layout.addWidget(file_label)
        
        return container




    def find_all_images(self, directory, use_multithreading=False):
        """查找目录中的所有图片文件"""
        if not os.path.isdir(directory):
            return []
        
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
        images = []
        
        try:
            # 查找当前目录下的图片文件
            for file in os.listdir(directory):
                full_path = os.path.join(directory, file)
                if os.path.isfile(full_path) and any(file.lower().endswith(ext) for ext in image_extensions):
                    images.append(full_path)
            
            # 按文件名排序
            images.sort()
        
            # 限制图片数量，避免过多计算
            max_images = 50
            if len(images) > max_images:
                images = images[:max_images]
            
            # 使用串行处理去重
            return self.find_unique_images_serial(images)
                    
        except PermissionError:
            pass
        except Exception as e:
            print(f"[IMAGE ERROR] 查找图片失败 {directory}: {e}")
        
        return images

    def find_unique_images_multithreaded(self, image_paths):
        """多线程查找唯一图片（基于MD5）"""
        if not image_paths:
            return []
        
        # 创建MD5计算工作线程
        self.md5_worker = MD5CalculationWorker(image_paths)
        self.md5_thread = QThread()
        
        # 使用队列等待结果
        result_queue = queue.Queue()
        
        def on_md5_calculated(md5_map):
            """MD5计算完成回调"""
            unique_images = self.filter_unique_images_by_md5(image_paths, md5_map)
            result_queue.put(unique_images)
        
        self.md5_worker.moveToThread(self.md5_thread)
        self.md5_worker.calculation_finished.connect(on_md5_calculated)
        self.md5_worker.finished.connect(self.md5_thread.quit)
        
        self.md5_thread.started.connect(self.md5_worker.calculate_md5_batch)
        self.md5_worker.finished.connect(self.md5_worker.deleteLater)
        self.md5_thread.finished.connect(self.md5_thread.deleteLater)
        
        # 启动线程
        self.md5_thread.start()
        
        # 等待结果（带超时）
        try:
            return result_queue.get(timeout=15)  # 减少超时时间到15秒
        except queue.Empty:
            print("[MD5 WARNING] MD5计算超时，返回原始图片列表")
            # === 新增：超时时停止线程 ===
            if self.md5_worker:
                self.md5_worker.stop()
            if self.md5_thread and self.md5_thread.isRunning():
                self.md5_thread.quit()
                self.md5_thread.wait(2000)  # 等待2秒
            return image_paths

    def find_unique_images_serial(self, image_paths):
        """串行查找唯一图片 - 优化版本"""
        unique_images = []
        seen_md5s = set()
        
        # 限制最大处理数量
        max_process = min(len(image_paths), 100)
        
        for i, img_path in enumerate(image_paths[:max_process]):
            try:
                # 快速计算MD5（限制文件大小）
                file_size = os.path.getsize(img_path)
                if file_size > 50 * 1024 * 1024:  # 跳过大于50MB的文件
                    unique_images.append(img_path)
                    continue
                    
                md5_value = self.calculate_md5_quick(img_path)
                if md5_value and md5_value not in seen_md5s:
                    seen_md5s.add(md5_value)
                    unique_images.append(img_path)
            except Exception as e:
                # 如果计算MD5失败，仍然保留该图片
                print(f"[MD5 WARNING] 计算MD5失败 {img_path}: {e}")
                unique_images.append(img_path)
        
        # 如果有限制数量，添加剩余图片
        if len(image_paths) > max_process:
            unique_images.extend(image_paths[max_process:])
        
        return unique_images


    def calculate_md5_quick(self, file_path):
        """快速计算MD5（用于串行处理）"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5()
                while chunk := f.read(8192):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except Exception as e:
            return None

    def filter_unique_images_by_md5(self, image_paths, md5_map):
        """根据MD5映射过滤唯一图片"""
        unique_images = []
        seen_md5s = set()
        
        for img_path in image_paths:
            md5_value = md5_map.get(img_path)
            if md5_value and md5_value not in seen_md5s:
                seen_md5s.add(md5_value)
                unique_images.append(img_path)
            elif md5_value:
                print(f"[DEBUG] 跳过重复图片: {img_path} (MD5指纹相同)")
            else:
                # 如果MD5计算失败，仍然保留该图片
                unique_images.append(img_path)
        
        return unique_images








    def copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.update_status_bar("路径已复制到剪贴板", 2000)

    def filter_directories(self):
        """统一的目录过滤方法 - 支持搜索、拼音、排序、日期过滤和路径过滤"""
        if not hasattr(self, 'table_widget'):
            return
        
        search_text = self.search_input.text().lower().strip()
        
        # 获取路径过滤条件
        path_condition, path_params = self.get_path_filter_condition()
        
        # 重新从数据库获取数据，而不是过滤现有表格
        if not self.user_manager.current_db_path:
            return
        
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            
            # 构建基础查询
            base_query = """
                SELECT name, path, directory_exists, created_time, last_modified, is_directory 
                FROM directories 
                WHERE name IS NOT NULL AND name != '' 
                AND path IS NOT NULL AND path != ''
            """
            
            conditions = []
            params = []
            
            # 添加路径过滤条件
            if path_condition:
                conditions.append(f"({path_condition})")
                params.extend(path_params)

            # 添加日期过滤条件（如果控件存在）
            if hasattr(self, 'date_from_edit') and hasattr(self, 'date_to_edit'):
                date_from = self.date_from_edit.date().toString("yyyy-MM-dd")
                date_to = self.date_to_edit.date().addDays(1).toString("yyyy-MM-dd")
                conditions.append("last_modified >= ? AND last_modified < ?")
                params.append(date_from)
                params.append(date_to)
            
            # 添加排序条件（如果控件存在）
            order_clause = "ORDER BY name"  # 默认按名称
            if hasattr(self, 'sort_combo'):
                sort_method = self.sort_combo.currentData()
                if sort_method == "date":
                    order_clause = "ORDER BY last_modified DESC"
                elif sort_method == "path":
                    order_clause = "ORDER BY path"
            
            # 构建完整查询
            if conditions:
                base_query += " AND " + " AND ".join(conditions)
            base_query += " " + order_clause
            
            # 添加搜索条件（名称或路径匹配，支持拼音）
            filtered_rows = []
            if search_text:
                # 先获取初步过滤的数据，不带搜索词
                cursor.execute(base_query, params)
                all_rows = cursor.fetchall()
                
                # 在Python中进行拼音匹配
                for row in all_rows:
                    name = row[0]
                    path = row[1]
                    if (search_text in name.lower() or 
                        search_text in path.lower() or
                        PinyinSearchHelper.contains_pinyin_initials(name, search_text) or
                        PinyinSearchHelper.contains_pinyin_initials(path, search_text)):
                        filtered_rows.append(row)
            else:
                # 没有搜索条件，直接执行完整查询
                cursor.execute(base_query, params)
                filtered_rows = cursor.fetchall()

            conn.close()
        
            # 根据视图模式更新显示
            current_view = getattr(self, '_view_mode', 'list')
            if current_view == 'grid':
                # 网格视图：刷新网格
                self.refresh_grid_display()
            else:
                # 列表视图：更新表格
                self.update_table_with_data(filtered_rows)

            # 更新状态栏
            visible_count = len(filtered_rows)
            filter_info = ""
            if hasattr(self, 'current_path_filter') and self.current_path_filter:
                filter_info = f" (路径过滤: {self.current_path_filter[:30]}...)"
            self.statusBar().showMessage(f"显示 {visible_count} 个匹配项目{filter_info}")
            
        except Exception as e:
            print(f"[FILTER ERROR] {e}")
            import traceback
            traceback.print_exc()
            self.statusBar().showMessage(f"过滤失败: {e}")





    
    def show_settings(self):
        if not self.user_manager.current_user:
            QMessageBox.warning(self, "未登录", "请先登录用户")
            return
        
        dialog = SettingsDialog(self.user_manager, self)
        if dialog.exec() == QDialog.Accepted:
            # 重新加载显示设置
            self.load_directories()
            
            # 重新启动自动扫描定时器
            self.start_auto_scan()
    
    def start_auto_scan(self):
        """启动自动扫描定时器 - 增强完整版本"""
        print("[DEBUG] 开始启动自动扫描定时器...")
        
        # 1. 检查前提条件
        if not self.user_manager.current_db_path:
            print("[ERROR] 无法启动自动扫描：未找到当前数据库路径")
            return False
        
        # 确保数据库文件存在
        if not os.path.exists(self.user_manager.current_db_path):
            print(f"[ERROR] 数据库文件不存在: {self.user_manager.current_db_path}")
            return False
    
        # === 新增：线程安全检查 ===
        if not hasattr(self, 'scan_timer'):
            print("[ERROR] scan_timer 未初始化")
            return False
        
        # 确保在主线程中操作定时器
        if not self.scan_timer.thread() == QThread.currentThread():
            print("[WARNING] 定时器操作不在主线程，使用信号槽机制")
            # 使用单次定时器在主线程中重新调用此方法
            QTimer.singleShot(0, self.start_auto_scan)
            return False
            
        # 安全停止现有定时器
        if self.scan_timer.isActive():
            try:
                self.scan_timer.stop()
                print("[DEBUG] 已停止现有的自动扫描定时器")
            except RuntimeError as e:
                print(f"[WARNING] 停止定时器时出错: {e}")
        
        # 获取设置值
        interval, auto_scan = self.get_auto_scan_settings()
        
        if auto_scan:
            try:
                # === 新增：延迟启动自动扫描，避免保存设置后立即扫描 ===
                def delayed_auto_scan():
                    if not self.scan_timer.isActive():  # 确保定时器没有被手动停止
                        self.progress_bar.setVisible(True)
                        self.progress_bar.setValue(0)
                        self.progress_label.setText("自动扫描开始...")
                        QApplication.processEvents()
                        
                        # 执行扫描
                        self.scan_directories()
                        
                        # 扫描完成后延迟隐藏进度条
                        QTimer.singleShot(3000, self.hide_progress_bar)
                
                # 设置定时器调用带进度条的扫描函数
                self.scan_timer.timeout.disconnect()
                self.scan_timer.timeout.connect(delayed_auto_scan)
                
                # === 新增：延迟10秒后启动第一次扫描，避免立即扫描 ===
                QTimer.singleShot(60000, lambda: self.scan_timer.start(interval) if auto_scan else None)
                
                print(f"[SUCCESS] 自动扫描定时器已启动，将在60秒后开始第一次扫描，间隔: {interval/1000}秒")
                return True
            except Exception as e:
                print(f"[ERROR] 启动自动扫描定时器失败: {e}")
                return False
        else:
            print("[INFO] 自动扫描已禁用")
            return False


    def get_auto_scan_settings(self):
        """安全获取自动扫描相关设置"""
        interval = 3600 * 1000  # 默认1小时
        auto_scan = True  # 默认启用
        
        conn = None
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            
            # 获取扫描间隔
            cursor.execute("SELECT value FROM settings WHERE key = 'scan_interval'")
            result = cursor.fetchone()
            if result:
                try:
                    interval = int(result[0]) * 1000
                except (ValueError, TypeError):
                    print(f"[WARNING] 无效的扫描间隔设置: {result[0]}，使用默认值")
            
            # 获取自动扫描设置
            cursor.execute("SELECT value FROM settings WHERE key = 'auto_scan'")
            result = cursor.fetchone()
            if result:
                auto_scan = result[0] == "1"
                
        except Exception as e:
            print(f"[ERROR] 获取自动扫描设置时出错: {e}")
        finally:
            if conn:
                conn.close()
        
        return interval, auto_scan





    def monitor_auto_scan(self):
        """监控自动扫描状态"""
        if not self.user_manager.current_db_path:
            return False, False
        
        # 再次查询以确认设置
        conn = None
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            
            # 检查定时器状态
            if not self.scan_timer.isActive():
                # 如果定时器未运行但应该运行，重新启动
                auto_scan = self.get_setting('auto_scan', '1') == '1'
                if auto_scan:
                    # 验证定时器是否真正启动
                    if not self.scan_timer.isActive():
                        print("[WARNING] 自动扫描定时器意外停止，尝试重新启动...")
                    return self.start_auto_scan()
        
        except Exception as e:
            print(f"[ERROR] 监控自动扫描状态时出错: {e}")
            return False, False
        finally:
            if conn:
                conn.close()
        
        return True, True




    def validate_settings(self):
        """验证所有设置是否正常生效"""
        issues = []
        
        # 验证数据库连接
        if not self.user_manager.current_db_path:
            issues.append("❌ 未找到当前数据库路径")
        else:
            # 检查数据库文件是否存在
            if not os.path.exists(self.user_manager.current_db_path):
                issues.append("❌ 数据库文件不存在")
        
        # 验证扫描模式设置
        scan_mode = self.get_setting('scan_mode', 'directories')
        issues.append(f"✅ 扫描模式: {scan_mode}")
        
        # 验证自动扫描设置
        auto_scan = self.get_setting('auto_scan', '1') == '1'
        if auto_scan:
            issues.append("✅ 自动扫描: 已启用")
        else:
            issues.append("ℹ️ 自动扫描: 已禁用")
        
        # 验证扫描间隔
        scan_interval = self.get_setting('scan_interval', '3600')
        try:
            interval_seconds = int(scan_interval)
            if interval_seconds < 60:
                issues.append("⚠️ 扫描间隔过短 (< 1分钟)")
        except (ValueError, TypeError):
            issues.append("❌ 扫描间隔设置无效")
        
        # 验证过滤设置
        include_filter = self.get_setting('include_filter', '')
        if include_filter:
            issues.append(f"✅ 包含过滤: {include_filter}")
        else:
            issues.append("ℹ️ 包含过滤: 未设置")
        
        exclude_filter = self.get_setting('exclude_filter', '')
        if exclude_filter:
            issues.append(f"✅ 排除过滤: {exclude_filter}")

        # === 新增：验证封面保存设置 ===
        cover_save_mode, cover_save_dir = self.get_cover_save_settings()
        issues.append(f"✅ 封面保存模式: {cover_save_mode}")
        
        if cover_save_dir:
            if os.path.exists(cover_save_dir):
                issues.append(f"✅ 封面保存目录: {cover_save_dir}")
            else:
                issues.append(f"⚠️ 封面保存目录不存在: {cover_save_dir}")
        else:
            issues.append("ℹ️ 封面保存目录: 未设置")

        # 验证跳过空白目录设置
        skip_empty_dirs = self.get_setting('skip_empty_dirs', '0') == '1'
        if skip_empty_dirs:
            issues.append("✅ 跳过空白目录: 已启用")
        else:
            issues.append("ℹ️ 跳过空白目录: 已禁用")


        return issues


    def get_setting(self, key, default=None):
        """安全获取设置值 -  DirectoryScannerApp专用版本"""
        if not self.user_manager.current_db_path:
            return default

        # 【修复】get_setting 会在工作线程（扫描循环、封面/缩略图 worker）里被
        # 高频调用，因此这里**只做只读检查**，绝不触发真正建索引：
        # 已就绪则零开销通过；未就绪则返回 False，由主线程的 login_user /
        # load_directories 确定时点调用 _indexes_ensure() 真正补齐。
        self._indexes_check_only(self.user_manager.current_db_path)

        conn = None
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = cursor.fetchone()
            if result:
                return result[0]
            return default
        except Exception as e:
            print(f"[ERROR] 获取设置 {key} 时出错: {e}")
            return default
        finally:
            if conn:
                conn.close()


    
    def manual_backup(self):
        """手动备份数据库 - 改为使用多线程"""
        self.manual_backup_threaded()
    
    def show_restore_dialog(self):
        if not self.user_manager.current_db_path:
            QMessageBox.warning(self, "未登录", "请先登录用户")
            return
        
        dialog = RestoreDatabaseDialog(self.backup_manager, self.user_manager.current_db_path, self)
        if dialog.exec() == QDialog.Accepted:
            # 数据库已恢复，重新加载数据
            self.load_directories()
            QMessageBox.information(self, "恢复完成", "数据库已恢复，请检查数据是否正确")

    def scan_directory_with_depth(self, root_dir, max_depth, scan_mode):
        """扫描指定深度的目录和/或文件"""
        items = []
        processed_paths = set()
        
        # 获取扫描模式 - 增强错误处理
        scan_mode = "directories"  # 默认值
        conn = None
        try:
            if self.user_manager.current_db_path:
                conn = sqlite3.connect(self.user_manager.current_db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM settings WHERE key = 'scan_mode'")
                result = cursor.fetchone()
                if result:
                    scan_mode = result[0]
        except Exception as e:
            print(f"[WARNING] 获取扫描模式失败，使用默认值: {e}")
        finally:
            if conn:
                conn.close()

        # 记录当前使用的扫描模式

        # === 新增：扫描进度统计 ===
        total_items_processed = 0
        estimated_total = 1000  # 预估总数，会在扫描过程中调整
    
        # 使用队列进行广度优先搜索
        from collections import deque
        queue = deque([(root_dir, 0)])  # (path, current_depth)
        
        while queue:
            current_path, current_depth = queue.popleft()
            
            # 只处理到指定深度
            if current_depth > max_depth:
                continue
            
            # 检查路径是否已处理
            if current_path in processed_paths:
                continue
            processed_paths.add(current_path)
        
            # === 新增：实时更新扫描进度 ===
            total_items_processed += 1
            if total_items_processed % 10 == 0:  # 每处理10个项目更新一次进度
                progress_percent = min(30, int((total_items_processed / estimated_total) * 30))  # 扫描阶段占30%
                current_progress = self.progress_bar.value()
                if progress_percent > current_progress:
                    self.progress_bar.setValue(progress_percent)
                    self.progress_label.setText(f"正在扫描文件系统... ({total_items_processed} 个项目)")
                    QApplication.processEvents()
        
            try:
                # 检查路径是否存在且可访问
                if not os.path.exists(current_path):
                    continue
                    
                # 获取路径信息
                stat = os.stat(current_path)
                created_time = datetime.datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
                modified_time = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                
                # 根据扫描模式决定是否添加当前项
                is_dir = os.path.isdir(current_path)
                should_add = False
                
                if scan_mode == "directories" and is_dir:
                    should_add = True
                elif scan_mode == "files" and not is_dir:
                    should_add = True
                elif scan_mode == "both":
                    should_add = True
            
                # === 新增：如果是目录，检查是否为空目录 ===
                if should_add and is_dir:
                    # 检查目录是否为空
                    try:
                        dir_contents = os.listdir(current_path)
                        # 过滤掉隐藏文件和系统文件
                        visible_contents = [item for item in dir_contents 
                                        if not item.startswith('.') and not item.startswith('~')]
                        
                        # 如果是空目录，根据设置决定是否跳过
                        if not visible_contents:
                            if skip_empty_dirs:
                                should_add = False
                    except (PermissionError, FileNotFoundError):
                        should_add = False
            
                # 加强数据验证：确保路径和名称有效
                if should_add:
                    name = os.path.basename(current_path)
                    
                    # 过滤无效数据：名称不能为空，路径不能为空，排除系统文件
                    # 增加判断：如果没有目录名称或没有路径，就不添加到列表
                    if (name and name.strip() and 
                        current_path and current_path.strip() and
                        not name.startswith('.') and  # 排除隐藏文件
                        not name.startswith('~')):    # 排除临时文件
                        
                        items.append({
                            "name": name,
                            "path": current_path,
                            "directory_exists": 1,
                            "created_time": created_time,
                            "last_modified": modified_time,
                            "is_main_dir": current_depth == 0 and is_dir,
                            "is_directory": 1 if is_dir else 0
                        })
                
                # 如果是目录且不是最大深度，则添加子项到队列
                if is_dir and current_depth < max_depth:
                    try:
                        sub_items = []
                        for entry in os.listdir(current_path):
                            full_path = os.path.join(current_path, entry)
                            # 过滤掉隐藏文件和系统文件
                            if not entry.startswith('.') and not entry.startswith('~'):
                                sub_items.append(full_path)
                    
                        # 更新预估总数
                        estimated_total += len(sub_items)
                        
                        for full_path in sub_items:
                            queue.append((full_path, current_depth + 1))
                            
                    except (PermissionError, FileNotFoundError):
                        continue
                        
            except (FileNotFoundError, PermissionError, OSError) as e:
                print(f"跳过无法访问的路径 {current_path}: {e}")
                continue
                    
        return items



    def create_preview_widget(self, path, is_directory):
        """创建图片预览组件"""
        preview_widget = QLabel()
        preview_widget.setFixedSize(220, 150)  # 固定预览区域大小
        preview_widget.setAlignment(Qt.AlignCenter)
        preview_widget.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
        """)
        
        if is_directory:
            # 如果是目录，查找封面图片
            cover_path = self.find_cover_image(path)
            if cover_path:
                self.set_preview_image(preview_widget, cover_path)
            else:
                # 没有封面则显示目录中的第一张图片
                first_image = self.find_first_image(path)
                if first_image:
                    self.set_preview_image(preview_widget, first_image)
                else:
                    preview_widget.setText("📁")  # 没有图片则显示文件夹图标
        else:
            # 如果是文件且是图片，直接显示
            if path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                self.set_preview_image(preview_widget, path)
            else:
                preview_widget.setText("📄")  # 不是图片则显示文件图标
                
        return preview_widget

    # ===== 图片缓存（类级别LRU缓存，避免重复加载） =====
    # 【性能优化】由普通 dict 改为 OrderedDict 以支持真正的 LRU 淘汰策略。
    # 相比原来的 FIFO（满额直接砍掉一半），LRU 能保持热点数据常驻。
    _pixmap_cache = OrderedDict()  # {cache_key: QPixmap}
    _pixmap_cache_max = 200        # 最大缓存数量
    _pixmap_cache_lock = Lock()    # 线程安全锁
    
    # ===== 封面路径缓存（避免重复 os.listdir 查找） =====
    # 【性能优化】同样改为 OrderedDict 支持 LRU。
    _cover_cache = OrderedDict()   # {dir_path: cover_image_path or None}
    _cover_cache_max = 500         # 最大缓存数量
    _cover_cache_lock = Lock()
    
    # ===== 预计算的颜色/画刷/样式（避免循环中重复创建） =====
    _BRUSH_GREEN = QBrush(QColor("#4CAF50"))
    _BRUSH_RED = QBrush(QColor("#F44336"))
    _BRUSH_WHITE = QBrush(QColor("#FFFFFF"))
    _BRUSH_BLUE = QBrush(QColor("#0066cc"))
    
    _STYLE_COVER_PLACEHOLDER = "background-color: #f8f9fa; border: 1px solid #dee2e6; color: #6c757d; font-size: 12px;"
    _STYLE_THUMB_PLACEHOLDER = "color: #999; font-size: 12px; background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 3px;"
    _STYLE_FILE_PLACEHOLDER = "color: #999; font-size: 12px; background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 3px;"

    # 【性能优化】表格级共用 QSS：逐控件 setStyleSheet 会为每个 QLabel 触发一次
    # 样式解析+polish，2000 行 × 3 个占位符 = 6000 次。
    # 改为表格级设置一次，循环内只 setObjectName。
    # 实测（offscreen，N=2000×3，多次采样）：提速约 1.3x-2.3x，中位数 ≈1.5x。
    # 注意：offscreen 环境缺字体会显著放大绝对耗时并造成大幅抖动，
    # 故此处倍数仅作量级参考，不要在别处引用为精确值。
    # 已独立验证视觉等价：三个选择器与上面的 _STYLE_*_PLACEHOLDER 逐声明完全一致。
    _TABLE_QSS = (
        "QLabel#coverPlaceholder { background-color: #f8f9fa; border: 1px solid #dee2e6;"
        " color: #6c757d; font-size: 12px; }"
        "QLabel#thumbPlaceholder { color: #999; font-size: 12px; background-color: #f8f9fa;"
        " border: 1px solid #dee2e6; border-radius: 3px; }"
        "QLabel#filePlaceholder { color: #999; font-size: 12px; background-color: #f8f9fa;"
        " border: 1px solid #dee2e6; border-radius: 3px; }"
    )

    def _apply_table_qss(self):
        """【性能优化】给表格控件设置一次共用占位符样式（循环外调用）。

        幂等：重复调用只是重设同一份 QSS，不会累积。
        """
        if hasattr(self, 'table_widget') and self.table_widget is not None:
            self.table_widget.setStyleSheet(self._TABLE_QSS)
    
    def safe_load_and_scale_image(self, image_path, target_width=180, target_height=120):
        """安全加载和缩放图片，带缓存优化（线程安全）"""
        try:
            # 参数验证
            if not image_path or not os.path.exists(image_path):
                return None
            
            # 构建缓存key
            cache_key = (image_path, target_width, target_height)
            
            # 线程安全地检查缓存
            with self._pixmap_cache_lock:
                if cache_key in self._pixmap_cache:
                    # 【性能优化】命中缓存时将其移动到末尾（LRU）
                    self._pixmap_cache.move_to_end(cache_key)
                    return self._pixmap_cache[cache_key]
            
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                return None
                
            # 确保目标尺寸是整数
            target_width = int(target_width)
            target_height = int(target_height)
            
            # 确保是正整数
            target_width = max(1, target_width)
            target_height = max(1, target_height)
            
            # 使用 QSize 对象来避免类型问题
            target_size = QSize(target_width, target_height)
            
            # 缩放图片，使用FastTransformation提升性能（略低于SmoothTransformation但快很多）
            scaled_pixmap = pixmap.scaled(
                target_size, 
                Qt.KeepAspectRatio, 
                Qt.FastTransformation  # 使用快速变换替代平滑变换，大幅提升速度
            )
            
            # 线程安全地更新缓存
            with self._pixmap_cache_lock:
                # 【性能优化】如果已存在（并发下可能），先移动到末尾
                if cache_key in self._pixmap_cache:
                    self._pixmap_cache.move_to_end(cache_key)
                
                self._pixmap_cache[cache_key] = scaled_pixmap
                
                # 缓存管理：超过上限时弹出最旧的（LRU 头部淘汰）
                if len(self._pixmap_cache) > self._pixmap_cache_max:
                    self._pixmap_cache.popitem(last=False)
            
            return scaled_pixmap
            
        except Exception as e:
            print(f"[ERROR] 安全加载图片失败: {e}")
            return None
    
    def clear_pixmap_cache(self):
        """清除图片缓存（切换用户时调用）"""
        with self._pixmap_cache_lock:
            self._pixmap_cache.clear()

    def set_preview_image(self, label, image_path):
        """设置预览图片 - 使用安全方法"""
        try:
            scaled_pixmap = self.safe_load_and_scale_image(image_path)
            if scaled_pixmap and not scaled_pixmap.isNull():
                label.setPixmap(scaled_pixmap)
            else:
                label.setText("❌")
        except Exception as e:
            print(f"设置预览图片出错: {e}")
            label.setText("❌")

    def on_thumbnail_clicked(self, event, image_path, row, index):
        """处理缩略图点击事件 - 专门用于调试和确保正确性"""
        print(f"[DEBUG] 点击缩略图: 行{row}, 索引{index}, 图片路径: {image_path}")
        
        if event.button() == Qt.LeftButton:  # 左键点击
            # 验证图片文件是否存在
            if os.path.exists(image_path):
                self.show_full_image(image_path)
            else:
                QMessageBox.warning(self, "图片不存在", f"无法找到图片文件:\n{image_path}")
        else:
            # 调用原有的鼠标事件处理
            if hasattr(self.sender(), 'mousePressEvent'):
                QLabel.mousePressEvent(self.sender(), event)







    
    def find_cover_image(self, path):
        """查找目录或文件的封面图片，支持PDF截图生成（带目录缓存）"""
        try:
            # 安全检查
            if not path or not isinstance(path, str):
                return None
            
            # 如果是PDF文件，生成封面截图
            if path.lower().endswith('.pdf'):
                return self.handle_pdf_cover(path)
            
            # 如果是目录，先查缓存（避免重复 os.listdir）
            if os.path.isdir(path):
                with self._cover_cache_lock:
                    if path in self._cover_cache:
                        # 【性能优化】命中缓存时移动到末尾（LRU）
                        self._cover_cache.move_to_end(path)
                        return self._cover_cache[path]
                
                result = self.find_directory_cover(path)
                
                # 写入缓存
                with self._cover_cache_lock:
                    # 【性能优化】如果已存在（并发下可能），先移动到末尾
                    if path in self._cover_cache:
                        self._cover_cache.move_to_end(path)
                    
                    self._cover_cache[path] = result
                    
                    # 缓存管理：超过上限时弹出最旧的（LRU 头部淘汰）
                    if len(self._cover_cache) > self._cover_cache_max:
                        self._cover_cache.popitem(last=False)
                
                return result
            
            # 如果是图片文件，直接返回路径
            if self.is_image_file(path):
                return path
                
            return None
            
        except Exception as e:
            print(f"[ERROR] 查找封面失败 {path}: {e}")
            return None

    def handle_pdf_cover(self, pdf_path):
        """处理PDF封面生成"""
        try:
            # 1. 首先检查是否有已生成的PDF封面
            existing_cover = self.get_existing_pdf_cover(pdf_path)
            if existing_cover:
                return existing_cover
            
            # 2. 如果设置允许，生成新的PDF封面
            if self.get_setting('generate_pdf_covers', '1') == '1':
                generated_cover = self.generate_pdf_cover(pdf_path)
                if generated_cover:
                    return generated_cover
            
            # 3. 返回默认PDF图标
            return self.get_default_pdf_icon()
            
        except Exception as e:
            print(f"[ERROR] 处理PDF封面失败 {pdf_path}: {e}")
            return self.get_default_pdf_icon()

    def get_existing_pdf_cover(self, pdf_path):
        """检查是否存在已生成的PDF封面"""
        try:
            # 使用MD5哈希生成唯一文件名
            pdf_hash = hashlib.md5(pdf_path.encode('utf-8')).hexdigest()
            
            # 可能的封面存储目录
            cover_dirs = [
                os.path.join(self.app_dir, "pdf_covers"),
                os.path.join(self.app_dir, "covers", "pdf"),
                os.path.expanduser("~/目录封面/PDF封面"),
                os.path.expanduser("~/.directory_scanner/pdf_covers")
            ]
            
            # 支持的图片格式
            extensions = ['.jpg', '.jpeg', '.png', '.webp']
            
            for cover_dir in cover_dirs:
                if os.path.exists(cover_dir):
                    for ext in extensions:
                        cover_path = os.path.join(cover_dir, f"{pdf_hash}{ext}")
                        if os.path.exists(cover_path):
                            # 验证文件是否有效
                            if self.is_valid_image_file(cover_path):
                                return cover_path
                            else:
                                # 删除无效文件
                                try:
                                    os.remove(cover_path)
                                except:
                                    pass
            return None
            
        except Exception as e:
            print(f"[ERROR] 检查PDF封面失败 {pdf_path}: {e}")
            return None

    def generate_pdf_cover(self, pdf_path, output_dir=None):
        """生成PDF文件的封面截图"""
        try:
            if not os.path.exists(pdf_path):
                print(f"[ERROR] PDF文件不存在: {pdf_path}")
                return False
        
            # 在方法开始处添加系统依赖检查
            missing_deps = []
            try:
                import fitz
            except ImportError:
                missing_deps.append("PyMuPDF")
                print("[INFO] PyMuPDF 未安装，跳过此方法")
            
            try:
                from pdf2image import convert_from_path
            except ImportError:
                missing_deps.append("pdf2image")
                print("[INFO] pdf2image 未安装，跳过此方法")    
            
            if not self.is_poppler_available():
                missing_deps.append("poppler-utils")
                print("[INFO] poppler-utils 未安装，跳过此方法") 
            
            if len(missing_deps) == 3:  # 所有方法都不可用
                print(f"[INFO] PDF封面生成功能不可用，缺少依赖: {', '.join(missing_deps)}")
                return False
            
            # 设置输出目录
            if output_dir is None:
                output_dir = os.path.join(self.app_dir, "pdf_covers")
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成唯一的封面文件名
            pdf_hash = hashlib.md5(pdf_path.encode('utf-8')).hexdigest()
            cover_path = os.path.join(output_dir, f"{pdf_hash}.jpg")
            
            # 如果封面已存在且有效，直接返回
            if os.path.exists(cover_path) and self.is_valid_image_file(cover_path):
                return cover_path
            
            print(f"[INFO] 正在为PDF生成封面: {os.path.basename(pdf_path)}")
            
            # 方法1: 使用 PyMuPDF (推荐，速度快)
            if self.generate_pdf_cover_fitz(pdf_path, cover_path):
                return cover_path
            
            # 方法2: 使用 pdf2image 作为备选
            if self.generate_pdf_cover_pdf2image(pdf_path, cover_path):
                return cover_path
                
            # 方法3: 使用 poppler-utils
            if self.generate_pdf_cover_poppler(pdf_path, cover_path):
                return cover_path
                
            print(f"[WARNING] 所有PDF封面生成方法都失败了: {pdf_path}")
            return None
            
        except Exception as e:
            print(f"[ERROR] 生成PDF封面失败 {pdf_path}: {e}")
            return None

    def generate_pdf_cover_fitz(self, pdf_path, output_path):
        """使用 PyMuPDF 生成PDF封面"""
        try:
            import fitz  # PyMuPDF
            
            # 打开PDF文件
            pdf_document = fitz.open(pdf_path)
            
            if len(pdf_document) == 0:
                pdf_document.close()
                return False
            
            # 获取第一页
            first_page = pdf_document[0]
            
            # 根据设置选择质量
            quality_setting = self.get_setting('pdf_cover_quality', '1')
            zoom_levels = {'0': 1.5, '1': 2.0, '2': 3.0}  # 低、中、高质量
            zoom = zoom_levels.get(quality_setting, 2.0)
            
            # 将页面转换为图片
            matrix = fitz.Matrix(zoom, zoom)
            pix = first_page.get_pixmap(matrix=matrix, alpha=False)
            
            # 保存为JPEG
            pix.save(output_path)
            pdf_document.close()
            
            print(f"[SUCCESS] PyMuPDF封面生成成功: {output_path}")
            return True
            
        except ImportError:
            print("[INFO] PyMuPDF 未安装，跳过此方法")
            return False
        except Exception as e:
            print(f"[ERROR] PyMuPDF生成封面失败: {e}")
            return False

    def generate_pdf_cover_pdf2image(self, pdf_path, output_path):
        """使用 pdf2image 生成PDF封面"""
        try:
            from pdf2image import convert_from_path
            
            # 根据设置选择DPI
            quality_setting = self.get_setting('pdf_cover_quality', '1')
            dpi_levels = {'0': 100, '1': 150, '2': 200}  # 低、中、高质量
            dpi = dpi_levels.get(quality_setting, 150)
            
            # 转换第一页为图片
            images = convert_from_path(
                pdf_path, 
                first_page=1, 
                last_page=1, 
                dpi=dpi,
                fmt='JPEG'
            )
            
            if images:
                # 保存图片
                images[0].save(output_path, 'JPEG', quality=85)
                print(f"[SUCCESS] pdf2image封面生成成功: {output_path}")
                return True
            return False
                
        except ImportError:
            print("[INFO] pdf2image 未安装，跳过此方法")
            return False
        except Exception as e:
            print(f"[ERROR] pdf2image生成封面失败: {e}")
            return False

    def generate_pdf_cover_poppler(self, pdf_path, output_path):
        """使用 poppler-utils 生成PDF封面"""
        # 新增：检查poppler是否可用
        if not self.is_poppler_available():
            print("[INFO] poppler-utils 未安装，跳过此方法")
            return False
        
        try:
            import subprocess
            import tempfile
            
            # 创建临时文件名
            temp_dir = tempfile.gettempdir()
            temp_prefix = os.path.join(temp_dir, "pdf_cover_")
            
            # 使用 pdftoppm 命令转换第一页
            cmd = [
                'pdftoppm', 
                '-jpeg', 
                '-f', '1', 
                '-l', '1', 
                '-singlefile',
                pdf_path, 
                temp_prefix
            ]
            
            # 根据质量设置调整大小
            quality_setting = self.get_setting('pdf_cover_quality', '1')
            size_options = {'0': '-scale-to', '1': '-scale-to', '2': '-scale-to-x'}
            size_values = {'0': '400', '1': '600', '2': '800'}
            
            if quality_setting in size_options:
                cmd.extend([size_options[quality_setting], size_values[quality_setting]])
            
            # 修复编码问题
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                encoding='utf-8', errors='ignore', timeout=30)
            
            if result.returncode == 0:
                # 查找生成的文件
                temp_jpg = temp_prefix + ".jpg"
                if os.path.exists(temp_jpg):
                    # 移动到目标位置
                    import shutil
                    shutil.move(temp_jpg, output_path)
                    return True
                    
        except FileNotFoundError:
            print("[INFO] poppler-utils 未安装，跳过此方法")
            return False
        except Exception as e:
            print(f"[ERROR] poppler生成封面失败: {e}")
            return False

    def find_directory_cover(self, directory_path):
        """查找目录中的封面图片"""
        try:
            if not os.path.isdir(directory_path):
                return None
            
            # 优先查找的图片文件名（按优先级排序）
            # 【性能优化】原先对这 20 个候选名逐个 os.path.exists（20 次 syscall），
            # 未命中时再 listdir 一次。改为只 listdir 一次，用小写集合做 O(1) 匹配，
            # 候选名命中顺序（即优先级）与原实现完全一致。
            cover_names = [
                'cover.jpg', 'cover.jpeg', 'cover.png', 'cover.webp',
                'folder.jpg', 'folder.jpeg', 'folder.png', 'folder.webp',
                'front.jpg', 'front.jpeg', 'front.png', 'front.webp',
                'poster.jpg', 'poster.jpeg', 'poster.png', 'poster.webp',
                'thumb.jpg', 'thumb.jpeg', 'thumb.png', 'thumb.webp',
            ]

            # 如果没有找到特定封面，查找目录中的第一张图片
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']

            try:
                # 一次 listdir 拿到全部条目（原实现未命中时要 listdir，命中时也要 exists）
                files = os.listdir(directory_path)
            except PermissionError:
                print(f"[WARNING] 无权限访问目录: {directory_path}")
                return None
            except Exception as e:
                print(f"[WARNING] 读取目录失败 {directory_path}: {e}")
                return None

            # 小写名 -> 实际文件名，用于候选封面名 O(1) 匹配
            lower_map = {}
            for f in files:
                lower_map.setdefault(f.lower(), f)

            # 首先检查特定的封面文件名（优先级顺序不变）。
            # 注意：这里刻意用「候选名字面拼接」而不是 listdir 里的实际文件名——
            # Windows 文件系统大小写不敏感，原实现 os.path.exists('cover.jpg')
            # 对实际名为 COVER.JPG 的文件同样命中并返回字面路径 cover.jpg。
            # 保持字面拼接以维持与原实现的返回值完全一致。
            for cover_name in cover_names:
                if cover_name not in lower_map:
                    continue
                cover_path = os.path.join(directory_path, cover_name)
                if os.path.isfile(cover_path) and self.is_valid_image_file(cover_path):
                    return cover_path

            # 若没有特定封面，取排序后的第一张图片（与原实现一致）
            files.sort()  # 按文件名排序，确保一致性

            for file in files:
                file_path = os.path.join(directory_path, file)
                if (os.path.isfile(file_path) and
                        any(file.lower().endswith(ext) for ext in image_extensions) and
                        self.is_valid_image_file(file_path)):
                    return file_path

            return None
            
        except Exception as e:
            print(f"[ERROR] 查找目录封面失败 {directory_path}: {e}")
            return None

    def is_image_file(self, file_path):
        """检查文件是否为图片"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff']
        return (os.path.isfile(file_path) and 
                any(file_path.lower().endswith(ext) for ext in image_extensions))

    def is_valid_image_file(self, file_path):
        """验证图片文件是否有效"""
        try:
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                return False
            
            # 尝试打开图片验证
            from PIL import Image
            Image.MAX_IMAGE_PIXELS = None
            with Image.open(file_path) as img:
                img.verify()
            return True
            
        except Exception:
            return False

    def get_default_pdf_icon(self):
        """获取默认的PDF图标"""
        # 可以返回一个内置的PDF图标路径，或者生成一个SVG
        default_icon_path = os.path.join(self.app_dir, "assets", "pdf_icon.png")
        
        if os.path.exists(default_icon_path):
            return default_icon_path
        
        # 如果默认图标不存在，返回None使用系统默认
        return None


    def batch_generate_pdf_covers(self):
        """批量生成所有PDF文件的封面 - 增强错误处理"""
        if not self.user_manager.current_db_path:
            QMessageBox.warning(self, "未登录", "请先登录用户")
            return
        
        try:
            # 获取所有PDF文件
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT path FROM directories 
                WHERE path LIKE '%.pdf' AND directory_exists = 1
            """)
            pdf_files = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if not pdf_files:
                QMessageBox.information(self, "提示", "没有找到PDF文件")
                return
            
            # === 新增：过滤无效PDF文件 ===
            valid_pdf_files = []
            invalid_pdf_files = []
            
            for pdf_path in pdf_files:
                if self.is_valid_pdf(pdf_path):
                    valid_pdf_files.append(pdf_path)
                else:
                    invalid_pdf_files.append(pdf_path)
            
            print(f"[BATCH PDF] 找到 {len(pdf_files)} 个PDF文件")
            print(f"[BATCH PDF] 有效文件: {len(valid_pdf_files)} 个")
            print(f"[BATCH PDF] 无效文件: {len(invalid_pdf_files)} 个")
            
            if not valid_pdf_files:
                QMessageBox.warning(self, "提示", "没有找到有效的PDF文件")
                return
            
            # 显示无效文件列表
            if invalid_pdf_files:
                invalid_list = "\n".join([os.path.basename(p) for p in invalid_pdf_files[:10]])  # 只显示前10个
                if len(invalid_pdf_files) > 10:
                    invalid_list += f"\n... 还有 {len(invalid_pdf_files) - 10} 个文件"
                
                QMessageBox.information(self, "跳过无效文件", 
                                    f"跳过了 {len(invalid_pdf_files)} 个无效PDF文件:\n{invalid_list}")
            
            # 创建进度对话框（只处理有效文件）
            progress = QProgressDialog("正在生成PDF封面...", "取消", 0, len(valid_pdf_files), self)
            progress.setWindowTitle("批量生成PDF封面")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            
            success_count = 0
            failed_files = []
            
            # 只处理有效的PDF文件
            for i, pdf_path in enumerate(valid_pdf_files):
                progress.setValue(i)
                progress.setLabelText(f"正在处理 ({i+1}/{len(valid_pdf_files)}): {os.path.basename(pdf_path)}")
                
                if progress.wasCanceled():
                    break
                    
                if os.path.exists(pdf_path):
                    cover_path = self.generate_pdf_cover(pdf_path)
                    if cover_path:
                        success_count += 1
                    else:
                        failed_files.append(os.path.basename(pdf_path))
                else:
                    failed_files.append(f"{os.path.basename(pdf_path)} (文件不存在)")
                
                QApplication.processEvents()
            
            progress.setValue(len(valid_pdf_files))
            
            # 显示结果
            result_msg = f"成功生成 {success_count}/{len(valid_pdf_files)} 个PDF封面"
            if failed_files:
                result_msg += f"\n\n失败的文件:\n" + "\n".join(failed_files[:10])
                if len(failed_files) > 10:
                    result_msg += f"\n... 还有 {len(failed_files) - 10} 个文件失败"
            
            QMessageBox.information(self, "批量生成完成", result_msg)
                                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"批量生成PDF封面时出错:\n{e}")








    def enhanced_search(self, name, path, search_text):
        """增强的搜索功能，支持拼音首字母搜索"""
        
        # 1. 普通文本匹配
        if search_text in name.lower() or search_text in path.lower():
            return True
        
        # 2. 拼音首字母匹配
        name_initials = PinyinSearchHelper.text_to_pinyin_initials(name)
        path_initials = PinyinSearchHelper.text_to_pinyin_initials(path)
        
        # 检查拼音首字母
        if search_text in name_initials or search_text in path_initials:
            return True
        
        return False

    def show_about_dialog(self):
        """显示关于对话框"""
        about_info = ProjectInfo.get_about_info()
        tech_info = ProjectInfo.get_technical_info()
        version_history = ProjectInfo.get_version_history()
        
        # 创建关于对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(f"关于 {about_info['name']}")
        dialog.setMinimumSize(600, 500)
        
        layout = QVBoxLayout()
        
        # 标题和版本信息
        title_label = QLabel(f"<h1>{about_info['name']}</h1>")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 使用动态版本号
        version_label = QLabel(f"版本: {ProjectInfo.VERSION} | 构建日期: {ProjectInfo.BUILD_DATE}")  # 直接使用类属性
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # 基本信息
        info_group = QGroupBox("基本信息")
        info_layout = QVBoxLayout()
        
        info_layout.addWidget(QLabel(f"作者: {about_info['author']}"))
        info_layout.addWidget(QLabel(f"许可证: {about_info['license']}"))
        info_layout.addWidget(QLabel(f"版权: {about_info['copyright']}"))
        info_layout.addWidget(QLabel(f"项目地址: {about_info['url']}"))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 功能特性
        features_group = QGroupBox("主要功能")
        features_layout = QVBoxLayout()
        
        for feature in about_info['features']:
            features_layout.addWidget(QLabel(f"• {feature}"))
        
        features_group.setLayout(features_layout)
        layout.addWidget(features_group)
        
        # 技术信息
        tech_group = QGroupBox("技术信息")
        tech_layout = QVBoxLayout()
        
        tech_layout.addWidget(QLabel(f"编程语言: {tech_info['technology_stack']['language']}"))
        tech_layout.addWidget(QLabel(f"GUI框架: {tech_info['technology_stack']['gui_framework']}"))
        tech_layout.addWidget(QLabel(f"数据库: {tech_info['technology_stack']['database']}"))
        
        tech_group.setLayout(tech_layout)
        layout.addWidget(tech_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        close_button = QPushButton("关闭")
        close_button.clicked.connect(dialog.accept)
        
        help_button = QPushButton("使用帮助")
        help_button.clicked.connect(self.show_help_dialog)
        
        button_layout.addWidget(help_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec()

    def show_help_dialog(self):
        """显示使用帮助对话框"""
        help_text = ProjectInfo.get_help_text()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("使用帮助")
        dialog.setMinimumSize(700, 600)
        
        layout = QVBoxLayout()
        
        # 使用 QTextEdit 来显示格式化的帮助文本
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(help_text)
        
        layout.addWidget(text_edit)
        
        # 按钮
        button_layout = QHBoxLayout()
        close_button = QPushButton("关闭")
        close_button.clicked.connect(dialog.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec()

    def show_full_image(self, image_path):
        """显示完整图片的对话框"""
        if not image_path or not os.path.exists(image_path):
            QMessageBox.warning(self, "图片不存在", "无法找到指定的图片文件")
            return
        
        try:
            # 创建图片显示对话框
            dialog = QDialog(self)
            dialog.setWindowTitle(f"图片预览 - {os.path.basename(image_path)}")
            dialog.setMinimumSize(800, 600)
            
            layout = QVBoxLayout()
            
            # 图片显示区域
            image_label = QLabel()
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setStyleSheet("background-color: #f0f0f0;")
            
            # 使用安全方法加载图片
            screen_geometry = QApplication.primaryScreen().availableGeometry()
            max_width = int(screen_geometry.width() * 0.8)
            max_height = int(screen_geometry.height() * 0.8)
            
            scaled_pixmap = self.safe_load_and_scale_image(image_path, max_width, max_height)
            if scaled_pixmap and not scaled_pixmap.isNull():
                image_label.setPixmap(scaled_pixmap)
                # 设置对话框大小
                dialog.resize(scaled_pixmap.width() + 20, scaled_pixmap.height() + 60)
            else:
                image_label.setText("无法加载图片")
            
            # 图片信息
            info_label = QLabel(f"图片路径: {image_path}")
            info_label.setWordWrap(True)
            info_label.setStyleSheet("padding: 5px; background-color: white;")
            
            # 按钮
            button_layout = QHBoxLayout()
            close_button = QPushButton("关闭")
            close_button.clicked.connect(dialog.close)
            
            button_layout.addStretch()
            button_layout.addWidget(close_button)
            
            # 添加到布局
            layout.addWidget(image_label)
            layout.addWidget(info_label)
            layout.addLayout(button_layout)
            
            dialog.setLayout(layout)
            dialog.exec()
            
        except Exception as e:
            print(f"[DEBUG] 加载图片时出错: {e}")
            QMessageBox.critical(self, "错误", f"加载图片时出错:\n{e}")

            

    def setup_image_click_events(self):
        """为所有图片设置点击事件 - 完全重写版本"""
        if not hasattr(self, 'table_widget'):
            return
        
        for row in range(self.table_widget.rowCount()):
            # 1. 设置封面图片点击事件
            cover_widget = self.table_widget.cellWidget(row, 0)
            if cover_widget and isinstance(cover_widget, QLabel):
                path_item = self.table_widget.item(row, 4)
                if path_item:
                    path = path_item.text()
                    cover_path = self.find_cover_image(path)
                    if cover_path:
                        # 使用新的点击处理器
                        cover_widget.mousePressEvent = self.create_thumbnail_click_handler(cover_path)
            
            # 2. 设置其他缩略图点击事件
            thumbnails_widget = self.table_widget.cellWidget(row, 2)
            if thumbnails_widget and hasattr(thumbnails_widget, 'thumbnail_paths'):
                # 使用存储的缩略图路径
                thumbnail_paths = thumbnails_widget.thumbnail_paths
                
                # 遍历所有缩略图标签
                for i in range(thumbnails_widget.layout().count()):
                    thumb_label = thumbnails_widget.layout().itemAt(i).widget()
                    if (thumb_label and isinstance(thumb_label, QLabel) and 
                        thumb_label.pixmap() is not None and i < len(thumbnail_paths)):
                        # 为每个缩略图设置正确的点击事件
                        thumb_label.mousePressEvent = self.create_thumbnail_click_handler(thumbnail_paths[i])




    def on_image_clicked(self, event, image_path):
        """处理图片点击事件 - 保持兼容性"""
        if event.button() == Qt.LeftButton:  # 左键点击
            self.show_full_image(image_path)
        else:
            # 调用原有的鼠标事件处理
            QLabel.mousePressEvent(self.sender(), event)


    def get_cover_save_settings(self):
        """获取封面保存设置"""
        cover_save_mode = self.get_setting('cover_save_mode', 'smart')
        cover_save_dir = self.get_setting('cover_save_dir', '')
        return cover_save_mode, cover_save_dir

    def save_cover_image(self, dir_path, cover_path):
        """保存封面图片 - 线程安全版本"""
        try:
            # 获取封面保存设置
            cover_save_mode, cover_save_dir = self.get_cover_save_settings()
            
            if not cover_save_dir:
                print(f"[COVER SAVE ERROR] 封面保存目录未设置")
                return False
            
            # 确保保存目录存在
            os.makedirs(cover_save_dir, exist_ok=True)
            
            # 根据模式确定保存路径
            save_path = self.get_expected_cover_path(dir_path, cover_save_dir, cover_save_mode)
            if not save_path:
                print(f"[COVER SAVE ERROR] 无法生成封面保存路径: {dir_path}")
                return False
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # 复制封面文件 - 使用文件锁确保线程安全
            import shutil
            
            # 使用临时文件避免并发写入冲突
            temp_path = save_path + '.tmp'
            try:
                shutil.copy2(cover_path, temp_path)
                
                # 验证复制后的文件
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                    # 原子性重命名操作
                    if os.path.exists(save_path):
                        os.remove(save_path)  # 删除旧文件
                    os.rename(temp_path, save_path)
                    
                    print(f"[COVER SAVE SUCCESS] 封面保存成功: {save_path}")
                    return True
                else:
                    print(f"[COVER SAVE ERROR] 临时文件创建失败: {temp_path}")
                    return False
                    
            except Exception as e:
                # 清理临时文件
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                raise e
                
        except Exception as e:
            print(f"[COVER SAVE ERROR] 保存封面失败 {cover_path} -> {save_path}: {e}")
            return False



    def is_av_format(self, dir_name):
        """检查目录名称是否符合AV格式 (XXXX-####)"""
        # AV格式正则：字母和数字组成的模式，通常为XXXX-####格式
        av_pattern = r'^[a-zA-Z]{2,6}-\d{2,6}$'
        return re.match(av_pattern, dir_name) is not None

    def get_series_save_path(self, dir_name, base_dir, cover_image_path):
        """获取系列模式下的保存路径"""
        # 提取系列名称（XXXX部分）
        series_match = re.match(r'^([a-zA-Z]{2,6})-\d{2,6}$', dir_name)
        if not series_match:
            return None
        
        series_name = series_match.group(1)
        series_dir = os.path.join(base_dir, series_name)
        
        # 确保系列目录存在
        os.makedirs(series_dir, exist_ok=True)
        
        # 获取文件扩展名
        ext = os.path.splitext(cover_image_path)[1]
        
        # 构建保存路径
        save_filename = f"{dir_name}{ext}"
        return os.path.join(series_dir, save_filename)

    def get_first_char_save_path(self, dir_name, base_dir, cover_image_path):
        """获取首字模式下的保存路径"""
        # 获取首字母（中文取拼音首字母，英文取首字母）
        first_char = self.get_first_character(dir_name)
        
        # 构建首字母目录
        first_char_dir = os.path.join(base_dir, first_char.upper())
        
        # 确保首字母目录存在
        os.makedirs(first_char_dir, exist_ok=True)
        
        # 获取文件扩展名
        ext = os.path.splitext(cover_image_path)[1]
        
        # 构建保存路径
        save_filename = f"{dir_name}{ext}"
        return os.path.join(first_char_dir, save_filename)

    def get_first_character(self, text):
        """获取文本的首字母"""
        if not text:
            return "OTHER"
        
        first_char = text[0]
        
        # 如果是中文字符，获取拼音首字母
        if '\u4e00' <= first_char <= '\u9fff':
            return PinyinSearchHelper.get_pinyin_initials(first_char).upper()
        else:
            # 英文字符，直接取首字母
            return first_char.upper() if first_char.isalpha() else "OTHER"

    def batch_save_all_covers_threaded(self):
        if not self.user_manager.current_db_path:
            QMessageBox.warning(self, "未登录", "请先登录用户")
            return

        # 检查保存目录
        success, cover_save_dir = self.ensure_cover_save_directory()
        if not success:
            QMessageBox.critical(self, "目录错误", f"封面保存目录准备失败:\n{cover_save_dir}")
            return

        cover_save_mode = self.get_setting('cover_save_mode', 'smart')
    
        # === 新增：获取跳过设置 ===
        skip_existing = self.get_setting('skip_existing_covers', '1') == '1'  # 新增这行

        # 确认操作
        reply = QMessageBox.question(
            self, "确认批量保存",
            f"确定要为所有已扫描目录保存封面图片吗？\n"
            f"保存目录: {cover_save_dir}\n"
            f"保存模式: {cover_save_mode}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            
            # 获取所有目录
            cursor.execute("SELECT path FROM directories WHERE is_directory = 1")
            directories = cursor.fetchall()
            
            total_count = len(directories)
            saved_count = 0
            failed_count = 0
            error_details = []

            self.update_status_bar("正在批量保存封面...")

            # 创建进度对话框
            progress_dialog = QProgressDialog("正在批量保存封面...", "取消", 0, total_count, self)
            progress_dialog.setWindowTitle("批量保存封面")
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.show()

            for i, (dir_path,) in enumerate(directories):
                if progress_dialog.wasCanceled():
                    break
                    
                progress_dialog.setValue(i)
                progress_dialog.setLabelText(f"正在处理: {os.path.basename(dir_path)}... ({i+1}/{total_count})")
                QApplication.processEvents()
                
                self.update_status_bar(f"批量保存封面: {i+1}/{total_count}")

                if os.path.exists(dir_path):
                    cover_path = self.find_cover_image(dir_path)
                    if cover_path and os.path.exists(cover_path):
                        # 新增：检查是否需要跳过
                        expected_save_path = self.get_expected_cover_path(dir_path, cover_save_dir, cover_save_mode)
                        if skip_existing and expected_save_path and os.path.exists(expected_save_path):
                            # 检查MD5是否相同
                            if self.is_same_image_by_md5(cover_path, expected_save_path):
                                print(f"[DEBUG] 批量保存时跳过封面: {dir_path} (MD5相同)")
                                continue  # 跳过保存
            
                        if self.save_cover_image(dir_path, cover_path):
                            saved_count += 1
                        else:
                            failed_count += 1
                            error_details.append(f"保存失败: {dir_path}")
                    else:
                        failed_count += 1
                        error_details.append(f"无封面图片: {dir_path}")
                else:
                    failed_count += 1
                    error_details.append(f"目录不存在: {dir_path}")
            
            progress_dialog.close()

            # === 修改这里：使用线程安全的状态栏更新 ===
            completion_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.update_status_bar(f"批量保存完成 - 成功 {saved_count} 个目录 | 完成时间: {completion_time}", 5000)


            # 显示详细结果
            result_msg = f"批量保存完成！\n成功: {saved_count} 个\n失败: {failed_count} 个"
            
            if failed_count > 0:
                result_msg += f"\n\n失败详情（前10个）:"
                for i, detail in enumerate(error_details[:10]):
                    result_msg += f"\n{i+1}. {detail}"
                if len(error_details) > 10:
                    result_msg += f"\n... 还有 {len(error_details) - 10} 个失败项"
            
            # 保存详细日志到文件
            if error_details:
                log_file = os.path.join(cover_save_dir, "cover_save_errors.log")
                try:
                    with open(log_file, 'w', encoding='utf-8') as f:
                        f.write(f"封面保存错误日志 - {datetime.datetime.now()}\n")
                        f.write(f"成功: {saved_count}, 失败: {failed_count}\n\n")
                        for detail in error_details:
                            f.write(f"{detail}\n")
                    result_msg += f"\n\n详细错误日志已保存到: {log_file}"
                except Exception as e:
                    print(f"[ERROR] 保存错误日志失败: {e}")

            # === 新增：记录批量保存完成时间 ===
            completion_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result_msg += f"\n\n完成时间: {completion_time}"

            QMessageBox.information(self, "批量保存完成", result_msg)
            self.statusBar().showMessage(f"批量保存完成 - 成功 {saved_count} 个目录 | 完成时间: {completion_time}")
            
        except Exception as e:
            print(f"[ERROR] 批量保存封面时出错: {e}")
            QMessageBox.critical(self, "批量保存失败", f"批量保存封面时出错:\n{e}")
            self.statusBar().showMessage("批量保存失败")
        finally:
            if conn:
                conn.close()


    def batch_save_missing_covers(self):
        """只为缺少封面的目录保存封面"""
        if not self.user_manager.current_db_path:
            QMessageBox.warning(self, "未登录", "请先登录用户")
            return
        
        cover_save_mode, cover_save_dir = self.get_cover_save_settings()
        if not cover_save_dir:
            QMessageBox.warning(self, "未设置保存目录", "请先在设置中设置封面保存目录")
            return
        
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            
            # 获取所有目录
            cursor.execute("SELECT path FROM directories WHERE is_directory = 1")
            directories = cursor.fetchall()
            
            missing_count = 0
            saved_count = 0
            
            self.statusBar().showMessage("正在检查缺少封面的目录...")
            QApplication.processEvents()
            
            # 首先统计缺少封面的目录
            for dir_path, in directories:
                if os.path.exists(dir_path):
                    expected_cover_path = self.get_expected_cover_path(dir_path, cover_save_dir, cover_save_mode)
                    if not expected_cover_path or not os.path.exists(expected_cover_path):
                        missing_count += 1
            
            if missing_count == 0:
                QMessageBox.information(self, "无需保存", "所有目录的封面图片都已保存")
                return
            
            # 确认操作
            reply = QMessageBox.question(
                self, "确认保存缺失封面",
                f"检测到 {missing_count} 个目录缺少封面图片，确定要保存吗？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
            
            # 保存缺失的封面
            current_count = 0
            for i, (dir_path,) in enumerate(directories):
                if os.path.exists(dir_path):
                    expected_cover_path = self.get_expected_cover_path(dir_path, cover_save_dir, cover_save_mode)
                    if not expected_cover_path or not os.path.exists(expected_cover_path):
                        current_count += 1
                        self.statusBar().showMessage(f"正在保存缺失封面... ({current_count}/{missing_count})")
                        QApplication.processEvents()
                        
                        cover_path = self.find_cover_image(dir_path)
                        if cover_path and os.path.exists(cover_path):
                            if self.save_cover_image(dir_path, cover_path):
                                saved_count += 1

            # === 新增：记录保存完成时间 ===
            completion_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
           
            QMessageBox.information(self, "保存完成", f"成功保存 {saved_count} 个缺失封面\n完成时间: {completion_time}")
            self.statusBar().showMessage(f"缺失封面保存完成 - 成功 {saved_count} 个 | 完成时间: {completion_time}")
            
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存缺失封面时出错:\n{e}")
            self.statusBar().showMessage("保存缺失封面失败")
        finally:
            if conn:
                conn.close()

    def get_expected_cover_path(self, directory_path, base_dir, cover_save_mode):
        """获取预期的封面保存路径"""
        dir_name = os.path.basename(directory_path)
        
        try:
            if cover_save_mode == 'smart':
                if self.is_av_format(dir_name):
                    return self.get_series_save_path(dir_name, base_dir, ".jpg")  # 假设扩展名
                else:
                    return self.get_first_char_save_path(dir_name, base_dir, ".jpg")
            elif cover_save_mode == 'series':
                return self.get_series_save_path(dir_name, base_dir, ".jpg")
            elif cover_save_mode == 'first_char':
                return self.get_first_char_save_path(dir_name, base_dir, ".jpg")
        except:
            pass
        
        return None

    def check_cover_save_status(self):
        """检查封面保存状态"""
        if not self.user_manager.current_db_path:
            return

        # 使用新的目录获取方法
        cover_save_dir = self.get_cover_save_directory()
        cover_save_mode = self.get_setting('cover_save_mode', 'smart')
        

        cover_save_mode, cover_save_dir = self.get_cover_save_settings()
        if not cover_save_dir:
            QMessageBox.information(self, "未设置", "请先设置封面保存目录")
            return
        
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM directories WHERE is_directory = 1")
            total_dirs = cursor.fetchone()[0]
            
            saved_count = 0
            for dir_path, in cursor.execute("SELECT path FROM directories WHERE is_directory = 1"):
                if os.path.exists(dir_path):
                    expected_path = self.get_expected_cover_path(dir_path, cover_save_dir, cover_save_mode)
                    if expected_path and os.path.exists(expected_path):
                        saved_count += 1
            
            status_msg = f"封面保存状态:\n总目录数: {total_dirs}\n已保存封面: {saved_count}\n缺失封面: {total_dirs - saved_count}"
            
            if total_dirs - saved_count > 0:
                status_msg += f"\n\n点击'只保存缺失封面'按钮可补全缺失封面"
            
            QMessageBox.information(self, "封面保存状态", status_msg)
            
        except Exception as e:
            QMessageBox.critical(self, "检查失败", f"检查封面保存状态时出错:\n{e}")
        finally:
            if conn:
                conn.close()



    def ensure_cover_save_directory(self):
        """确保封面保存目录存在且有写入权限"""
        cover_save_dir = self.get_cover_save_directory()
        
        if not cover_save_dir:
            return False, "封面保存目录未设置"
        
        try:
            # 创建目录（如果不存在）
            os.makedirs(cover_save_dir, exist_ok=True)
            
            # 测试写入权限
            test_file = os.path.join(cover_save_dir, "write_test.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            
            return True, cover_save_dir
        except Exception as e:
            return False, f"目录创建或权限测试失败: {e}"

    def get_cover_save_directory(self):
        """增强的封面保存目录获取方法"""
        cover_save_dir = self.get_setting('cover_save_dir', '')
        
        # 如果用户未设置，使用默认目录
        if not cover_save_dir:
            # 使用用户主目录下的"目录封面"文件夹，避免权限问题
            default_dir = os.path.join(os.path.expanduser("~"), "目录封面")
            return default_dir
        
        return cover_save_dir

    def debug_cover_save_status(self):
        """调试封面保存状态"""
        cover_save_dir = self.get_cover_save_directory()
        print(f"[DEBUG] 封面保存目录: {cover_save_dir}")
        print(f"[DEBUG] 目录存在: {os.path.exists(cover_save_dir)}")
        print(f"[DEBUG] 目录可写: {os.access(cover_save_dir, os.W_OK) if os.path.exists(cover_save_dir) else 'N/A'}")
        
        # 测试保存一个目录
        if hasattr(self, 'table_widget') and self.table_widget.rowCount() > 0:
            test_dir_path = self.table_widget.item(0, 4).text()
            test_cover_path = self.find_cover_image(test_dir_path)
            print(f"[DEBUG] 测试目录: {test_dir_path}")
            print(f"[DEBUG] 测试封面: {test_cover_path}")
            print(f"[DEBUG] 封面存在: {os.path.exists(test_cover_path) if test_cover_path else 'N/A'}")

    def get_saved_cover_path(self, directory_path):
        """获取已保存的封面图片路径"""
        cover_save_mode, cover_save_dir = self.get_cover_save_settings()
        if not cover_save_dir:
            return None
        
        dir_name = os.path.basename(directory_path)
        
        try:
            # 根据保存模式构建预期的保存路径
            if cover_save_mode == 'smart':
                if self.is_av_format(dir_name):
                    save_path = self.get_series_save_path(dir_name, cover_save_dir, ".jpg")
                else:
                    save_path = self.get_first_char_save_path(dir_name, cover_save_dir, ".jpg")
            elif cover_save_mode == 'series':
                save_path = self.get_series_save_path(dir_name, cover_save_dir, ".jpg")
            elif cover_save_mode == 'first_char':
                save_path = self.get_first_char_save_path(dir_name, cover_save_dir, ".jpg")
            else:
                # 默认使用智能模式
                if self.is_av_format(dir_name):
                    save_path = self.get_series_save_path(dir_name, cover_save_dir, ".jpg")
                else:
                    save_path = self.get_first_char_save_path(dir_name, cover_save_dir, ".jpg")
            
            # 检查文件是否存在（尝试常见图片扩展名）
            for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                test_path = save_path.rsplit('.', 1)[0] + ext
                if os.path.exists(test_path):
                    return test_path
            
            return None
            
        except Exception as e:
            print(f"[DEBUG] 获取保存封面路径失败: {e}")
            return None

    def is_same_image_by_md5(self, img_path1, img_path2):
        """通过MD5比较两个图片文件是否相同"""
        if not os.path.exists(img_path1) or not os.path.exists(img_path2):
            return False
        
        try:
            # 计算第一个图片的MD5
            with open(img_path1, 'rb') as f1:
                hash1 = hashlib.md5()
                while chunk := f1.read(8192):
                    hash1.update(chunk)
            
            # 计算第二个图片的MD5
            with open(img_path2, 'rb') as f2:
                hash2 = hashlib.md5()
                while chunk := f2.read(8192):
                    hash2.update(chunk)
            
            # 比较MD5值
            return hash1.hexdigest() == hash2.hexdigest()
            
        except Exception as e:
            print(f"[WARNING] MD5比较失败 {img_path1} vs {img_path2}: {e}")
            return False

    def create_thumbnail_click_handler(self, image_path):
        """创建缩略图点击事件处理器 - 修复变量捕获问题"""
        def thumbnail_click_handler(event):
            if event.button() == Qt.LeftButton:
                self.show_full_image(image_path)
            else:
                # 调用原有的鼠标事件处理
                if hasattr(self.sender(), 'mousePressEvent'):
                    QLabel.mousePressEvent(self.sender(), event)
        return thumbnail_click_handler

    def show_scan_progress(self, message, value=None):
        """显示扫描进度 - 线程安全版本"""
        # === 新增：线程安全检查 ===
        if QThread.currentThread() != self.thread():
            # 如果不在主线程，使用信号槽机制
            QMetaObject.invokeMethod(self, "show_scan_progress", 
                                Qt.ConnectionType.QueuedConnection,
                                Q_ARG(str, message),
                                Q_ARG(int, value) if value is not None else Q_ARG(int, -1))
            return
        
        self.progress_bar.setVisible(True)
        if value is not None:
            self.progress_bar.setValue(value)
        self.progress_label.setText(message)
        QApplication.processEvents()

    def update_status_bar(self, message, timeout=0):
        """线程安全的状态栏更新"""
        def update():
            self.statusBar().showMessage(message, timeout)
        
        # 如果不在主线程，使用信号槽机制
        if QThread.currentThread() != self.thread():
            QMetaObject.invokeMethod(self, "update_status_bar_slot", 
                                Qt.ConnectionType.QueuedConnection,
                                Q_ARG(str, message),
                                Q_ARG(int, timeout))
        else:
            update()

    @Slot(str, int)
    def update_status_bar_slot(self, message, timeout):
        """状态栏更新槽函数"""
        self.statusBar().showMessage(message, timeout)

    def has_images_in_directory(self, directory_path):
        """检查目录是否包含图片文件"""
        if not os.path.isdir(directory_path):
            return False
        
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
        
        try:
            # 检查目录是否为空
            contents = os.listdir(directory_path)
            if not contents:
                return False  # 空目录
            
            # 检查是否有图片文件
            for file in contents:
                full_path = os.path.join(directory_path, file)
                if os.path.isfile(full_path):
                    if any(file.lower().endswith(ext) for ext in image_extensions):
                        return True  # 找到至少一个图片文件
            

            return False  # 没有找到图片文件
            
        except (PermissionError, FileNotFoundError):
            return False  # 无法访问的目录

    def update_window_title(self):
        """更新窗口标题，包含用户名信息和登录时间"""
        base_title = f"{ProjectInfo.NAME} {ProjectInfo.VERSION} (Build: {ProjectInfo.BUILD_DATE})"
        
        if self.user_manager.current_user:
            # 获取当前日期和时间
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            title = f"{base_title} - 用户: {self.user_manager.current_user} - 登录时间: {current_time}"
        else:
            title = f"{base_title} - 未登录"
        
        self.setWindowTitle(title)

    def on_table_cell_clicked(self, row, column):
        """处理表格单元格点击事件"""
        if column == 4:  # 目录地址列
            path_item = self.table_widget.item(row, column)
            if path_item:
                directory_path = path_item.text()
                
                # === 注意：这里直接使用表格中的路径，这已经是数据库中的路径 ===
                print(f"[DEBUG] 使用数据库路径打开目录: {directory_path}")
                
                # === 新增：路径转义处理 ===
                # 修复反斜杠转义问题
                directory_path = directory_path.replace('\\', '\\\\')
                
                # === 新增：网络路径检查 ===
                normalized_path = self.normalize_path(directory_path)
                if normalized_path.startswith('//'):
                    # 检查网络连通性
                    is_connected, message = self.check_network_connectivity(normalized_path)
                    if not is_connected:
                        reply = QMessageBox.question(
                            self, "网络连接问题",
                            f"{message}\n\n是否仍然尝试打开？",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No
                        )
                        if reply == QMessageBox.No:
                            return
                
                # 调用打开目录方法
                self.open_directory(directory_path)




    def normalize_path(self, path):
        """规范化路径，统一分隔符并处理网络路径"""
        if not path:
            return path
        
        # 将反斜杠统一为正斜杠
        normalized_path = path.replace('\\', '/')
        
        # 处理网络路径格式
        if normalized_path.startswith('//'):
            # 确保网络路径格式正确
            if not normalized_path.startswith('//'):
                normalized_path = '//' + normalized_path.lstrip('/')
        
        return normalized_path

    @Slot(str)
    def open_directory(self, directory_path):
        """打开指定目录 - 增强版本，支持网络路径和错误处理（线程安全）"""
        print(f"[DEBUG] 请求打开目录1: {directory_path}")
        if not directory_path:
            QMessageBox.warning(self, "路径为空", "目录路径为空")
            return False
        
        print(f"[DEBUG] 打开目录原始路径1: {directory_path}")
        
        # === 新增：统一路径分隔符 ===
        directory_path = self.normalize_path_separators(directory_path)
        print(f"[DEBUG] 规范化后路径: {directory_path}")
        
        # 原有的其他代码保持不变...
        original_path = directory_path
        
        # 如果是网络路径，使用专门的规范化方法
        if directory_path.startswith('\\\\'):
            directory_path = self.normalize_network_path(directory_path)
        
        # === 新增：网络路径特殊处理 ===
        is_network_path = directory_path.startswith('\\\\')
        
        if is_network_path:
            print(f"[DEBUG] 检测到网络路径: {directory_path}")
            
            # 首先尝试直接打开
            success = self.open_network_path_direct(directory_path)
            if not success:
                # 如果直接打开失败，尝试备用方案
                success = self.open_network_path_alternative(directory_path)
            
            if success:
                self.update_status_bar(f"正在打开网络路径: {directory_path}", 3000)
            else:
                self.update_status_bar(f"网络路径打开失败: {directory_path}", 5000)
            
            return success
        
        # === 原有的本地路径处理逻辑 ===
        # 修复路径分隔符问题
        import re
        
        # 修复模式：中文字符后紧跟英文字符的情况
        pattern = r'([\u4e00-\u9fff])([a-zA-Z])'
        fixed_path = re.sub(pattern, r'\1/\2', directory_path)
        
        if fixed_path != directory_path:
            print(f"[DEBUG] 路径修复: {directory_path} -> {fixed_path}")
            directory_path = fixed_path
        
        # 规范化路径
        normalized_path = self.normalize_path(directory_path)
        
        # 检查路径是否存在
        print(f"[DEBUG] 试图打开目录: {normalized_path}")
        if not os.path.exists(normalized_path):
            print(f"[DEBUG] 目录不存在: {normalized_path}")
            
            # 提供手动修复选项
            reply = QMessageBox.question(
                self, "目录不存在", 
                f"无法找到目录:\n{normalized_path}\n\n是否手动选择正确目录？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                # 让用户手动选择目录
                manual_dir = QFileDialog.getExistingDirectory(
                    self, "选择正确的目录", 
                    os.path.dirname(original_path) if os.path.dirname(original_path) else "."
                )
                if manual_dir:
                    return self.open_directory(manual_dir)
            
            return False
        
        # 原有的打开目录逻辑
        try:
            # 跨平台打开目录的方法
            if sys.platform == "win32":
                # Windows - 直接使用路径
                print(f"[DEBUG] Windows路径: {normalized_path}")
                os.startfile(normalized_path)
            elif sys.platform == "darwin":
                # macOS
                subprocess.run(["open", normalized_path], check=True)
            else:
                # Linux
                subprocess.run(["xdg-open", normalized_path], check=True)
        
            # === 新增：打印数据库对应数据 ===
            self.print_database_data_for_directory(normalized_path)

            self.update_status_bar(f"已打开目录: {normalized_path}", 3000)
            return True
            
        except subprocess.CalledProcessError as e:
            self.update_status_bar(f"打开目录失败: {e}", 5000)
            print(f"[ERROR] 打开目录失败: {e}")
            QMessageBox.critical(self, "打开目录失败", f"无法打开目录:\n{normalized_path}\n错误: {e}")
            return False
        except Exception as e:
            self.update_status_bar(f"打开目录失败: {e}", 5000)
            print(f"[ERROR] 打开目录失败: {e}")
            QMessageBox.critical(self, "打开目录失败", f"无法打开目录:\n{normalized_path}\n错误: {e}")
            return False







    def open_network_path_direct(self, network_path):
        """直接打开网络路径"""
        try:
            if sys.platform == "win32":
                print(f"[DEBUG] 尝试直接打开Windows网络路径: {network_path}")
                # 使用Popen而不是run，避免等待
                subprocess.Popen(['explorer', network_path], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
                return True
            else:
                # 其他系统转换为正斜杠
                unix_path = network_path.replace('\\\\', '//').replace('\\', '/')
                subprocess.Popen(["xdg-open", unix_path], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
                return True
        except Exception as e:
            print(f"[DEBUG] 直接打开网络路径失败: {e}")
            return False


    def open_network_path(self, network_path):
        """专门处理网络路径"""
        try:
            if sys.platform == "win32":
                # Windows 网络路径 - 使用反斜杠
                windows_network_path = network_path.replace('/', '\\')
                subprocess.run(['explorer', windows_network_path], check=True)
            else:
                # 其他系统尝试用文件管理器打开
                subprocess.run(["xdg-open", network_path], check=True)
                
            self.statusBar().showMessage(f"正在打开网络路径: {network_path}", 3000)
            return True
        except Exception as e:
            print(f"[DEBUG] 网络路径打开失败，尝试备用方案: {e}")
            return self.open_network_path_alternative(network_path)

    def open_network_path_alternative(self, network_path):
        """网络路径备用打开方案 - 增强版本"""
        print(f"[DEBUG] 网络路径打开失败，尝试备用方案: {network_path}")
        
        try:
            if sys.platform == "win32":
                # 方案1: 使用start命令（已存在）
                windows_network_path = network_path.replace('/', '\\')
                print(f"[DEBUG] 尝试Windows网络路径: {windows_network_path}")
                
                # 方案2: 直接使用explorer并捕获错误
                try:
                    result = subprocess.run(['explorer', windows_network_path], 
                                        capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        return True
                    else:
                        print(f"[DEBUG] explorer命令返回非零状态: {result.returncode}")
                except subprocess.TimeoutExpired:
                    print(f"[DEBUG] explorer命令超时，但可能已成功")
                    return True  # 超时也可能表示已成功打开
                
                # 方案3: 使用start命令（shell方式）
                try:
                    subprocess.run(['start', '', windows_network_path], 
                                shell=True, timeout=10)
                    print(f"[DEBUG] start命令执行完成")
                    return True  # start命令通常立即返回
                except subprocess.TimeoutExpired:
                    print(f"[DEBUG] start命令超时，但可能已成功")
                    return True
                
                # 方案4: 尝试映射网络驱动器方式（如果路径格式支持）
                if '\\' in windows_network_path and windows_network_path.count('\\') >= 3:
                    try:
                        # 提取服务器和共享名
                        parts = windows_network_path.split('\\')
                        if len(parts) >= 4:
                            server = parts[2]
                            share = parts[3]
                            drive_letter = self.find_available_drive_letter()
                            if drive_letter:
                                # 尝试映射网络驱动器
                                map_cmd = f'net use {drive_letter}: \\\\{server}\\{share}'
                                subprocess.run(map_cmd, shell=True, timeout=5)
                                
                                # 构建映射后的路径
                                mapped_path = f"{drive_letter}:\\" + "\\".join(parts[4:])
                                subprocess.run(['explorer', mapped_path], timeout=10)
                                
                                # 稍后断开映射
                                QTimer.singleShot(5000, lambda: subprocess.run(f'net use {drive_letter}: /delete', shell=True))
                                return True
                    except Exception as e:
                        print(f"[DEBUG] 网络驱动器映射失败: {e}")
            
            elif sys.platform == "darwin":
                # macOS
                subprocess.run(['open', network_path], check=True, timeout=10)
                return True
            else:
                # Linux - 尝试不同的文件管理器
                file_managers = ['nautilus', 'dolphin', 'thunar', 'pcmanfm', 'nemo']
                for manager in file_managers:
                    try:
                        subprocess.run([manager, network_path], check=True, timeout=10)
                        return True
                    except:
                        continue
                        
            # 如果所有方法都失败，显示路径让用户手动操作
            return self.show_manual_open_dialog(network_path)
            
        except subprocess.TimeoutExpired:
            print(f"[DEBUG] 备用方案超时，但可能已成功: {network_path}")
            return True  # 超时也可能表示已成功打开
        except Exception as e:
            print(f"[DEBUG] 备用方案也失败: {e}")
            return self.show_manual_open_dialog(network_path)

    def find_available_drive_letter(self):
        """查找可用的驱动器字母（Windows）"""
        if sys.platform != "win32":
            return None
        
        try:
            # 获取已使用的驱动器
            import string
            used_drives = set()
            for letter in string.ascii_uppercase:
                if os.path.exists(f"{letter}:"):
                    used_drives.add(letter)
            
            # 从Z开始反向查找可用驱动器
            for letter in reversed(string.ascii_uppercase):
                if letter not in used_drives and letter not in ['A', 'B', 'C']:  # 避免系统盘
                    return letter
        except:
            pass
        
        return None


    def show_manual_open_dialog(self, path):
        """显示手动打开对话框"""
        reply = QMessageBox.information(
            self, 
            "无法自动打开", 
            f"路径: {path}\n\n无法自动打开，请手动在文件管理器中访问此路径。\n是否复制路径到剪贴板？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.copy_to_clipboard(path)
        return False


    def check_network_connectivity(self, network_path):
        """检查网络连接性 - 可选方案：添加设置控制"""
        try:
            # 检查是否启用了网络连通性检查
            enable_network_check = self.get_setting('enable_network_check', '0') == '1'
            if not enable_network_check:
                return True, "跳过网络检查"  # 默认跳过检查
                
            # 提取主机名
            if network_path.startswith('//'):
                parts = network_path[2:].split('/')
                hostname = parts[0] if parts else ''
                
                # 使用ping检查网络连通性 - 隐藏窗口
                if sys.platform == "win32":
                    result = subprocess.run(['ping', '-n', '1', hostname], 
                                        capture_output=True, text=True,
                                        creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    result = subprocess.run(['ping', '-c', '1', hostname], 
                                        stdout=subprocess.DEVNULL, 
                                        stderr=subprocess.DEVNULL)
                
                if result.returncode == 0:
                    return True, f"网络设备 {hostname} 可达"
                else:
                    return False, f"无法连接到网络设备 {hostname}"
                        
        except Exception as e:
            return False, f"网络检查失败: {e}"
        
        return False, "无法解析网络路径"


    # 服务器相关方法
    def init_server(self):
        """初始化多线程服务器 - 自动检测可用端口"""
        # 从设置中获取基础端口
        base_port = int(self.get_setting('server_port', '8080'))
        
        # 获取实际可用的端口
        available_port = self.get_available_port(base_port)
        
        # 如果端口发生变化，保存到设置中
        if available_port != base_port:
            self.set_setting('server_port', str(available_port))
            print(f"[SERVER] 端口 {base_port} 已被占用，已自动切换到端口 {available_port}")
        
        self.server = DirectoryScannerServer(self, host='0.0.0.0', port=available_port)
        self.server_status = False

    def get_available_port(self, start_port, max_attempts=100):
        """获取可用的端口号"""
        import socket
        
        for port in range(start_port, start_port + max_attempts):
            try:
                # 尝试创建socket连接测试端口是否可用
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('0.0.0.0', port))
                    return port
            except OSError:
                # 端口被占用，继续尝试下一个
                print(f"[SERVER] 端口 {port} 已被占用，尝试下一个...")
                continue
        
        # 如果找不到可用端口，返回原始端口（让后续启动时抛出异常）
        print(f"[SERVER WARNING] 在范围 {start_port}-{start_port+max_attempts-1} 内找不到可用端口")
        return start_port

    def set_setting(self, key, value):
        """保存设置值"""
        if not self.user_manager.current_db_path:
            return False
        
        conn = None
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[ERROR] 保存设置 {key} 时出错: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def is_port_available(self, port):
        """检查端口是否可用"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                return True
        except OSError:
            return False

    def toggle_server(self):
        """切换服务器状态"""
        if not hasattr(self, 'server'):
            self.init_server()
        
        if self.server_status:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        """启动多线程服务器 - 增加端口冲突处理"""
        if hasattr(self, 'server') and self.server.start():
            self.server_status = True
            self.update_server_status_display()
            self.server_action.setText("🚫停止Web服务器")
            
            server_url = self.server.get_server_url()
            port = self.server.port
            
            # 检查是否使用了备用端口
            base_port = int(self.get_setting('server_port', '8080'))
            if port != base_port:
                server_url = f"http://0.0.0.0:{port}"
                self.update_status_bar(f"Web服务器已启动 (端口 {base_port} 被占用，自动切换到 {port}): {server_url}", 5000)
            else:
                self.update_status_bar(f"Web服务器已启动 (多线程模式): {server_url}", 5000)
            
            # 只在手动启动时显示信息对话框，自动启动时不显示
            if not hasattr(self, '_auto_started') or not self._auto_started:
                self.show_server_info()
            
            return True
        else:
            if not hasattr(self, '_auto_started') or not self._auto_started:
                QMessageBox.critical(self, "服务器错误", "无法启动Web服务器")
                self.update_status_bar("Web服务器启动失败", 5000)
            return False


    def stop_server(self):
        """停止服务器"""
        if hasattr(self, 'server') and self.server_status:
            self.server.stop()
            self.server_status = False
            self.server_action.setText("🌐启动Web服务器")
            self.server_action.setIcon(QIcon.fromTheme("network-server"))
            self.statusBar().showMessage("Web服务器已停止")
            self.update_server_status_display()
            self.update_status_bar("Web服务器已停止", 3000)

    def show_server_info(self):
        """显示服务器信息 - 更新为多线程信息"""
        if not self.server_status:
            return
        
        server_url = self.server.get_server_url()
        
        message = f"""
    Web服务器已启动！

    访问地址: {server_url}
    运行模式: 多线程 (最大10个并发线程)

    功能特性:
    • 📁 查看所有目录和文件
    • 🔍 搜索目录（支持拼音首字母）
    • 🖼️ 查看封面图片
    • 📂 一键打开目录
    • 🔄 远程扫描目录
    • 📱 响应式设计，支持手机访问
    • 🚀 多线程处理，支持高并发

    注意:
    • 服务器运行在: {server_url}
    • 同一网络下的其他设备也可以访问
    • 点击"停止Web服务器"可关闭服务
    • 多线程模式可同时处理多个请求
    """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Web服务器信息")
        msg_box.setText(message)
        msg_box.addButton("复制访问地址", QMessageBox.ActionRole)
        msg_box.addButton("在浏览器中打开", QMessageBox.ActionRole)
        msg_box.addButton("确定", QMessageBox.AcceptRole)
        
        result = msg_box.exec()
        
        if result == 0:  # 复制访问地址
            QApplication.clipboard().setText(server_url)
            self.statusBar().showMessage("访问地址已复制到剪贴板")
        elif result == 1:  # 在浏览器中打开
            import webbrowser
            webbrowser.open(server_url)


    def closeEvent(self, event):
        """应用程序关闭事件 - 增强版本"""
        self._is_closing = True
        
        # 保存窗口大小
        self._save_window_geometry()
        
        print("[DEBUG] 开始关闭应用程序，清理所有线程...")
    
        # 清理扫描状态文件
        self.cleanup_scan_states()

        # 添加：清理缩略图加载信息
        if hasattr(self, '_thumbnail_load_info'):
            self._thumbnail_load_info.clear()
        
        # 清理图片缓存
        self.clear_pixmap_cache()
        
        # 清理封面路径缓存
        with self._cover_cache_lock:
            self._cover_cache.clear()

        if hasattr(self, '_thumbnail_timers'):
            for timer in self._thumbnail_timers:
                if timer.isActive():
                    timer.stop()
            self._thumbnail_timers.clear()

        # 1. 停止服务器
        if hasattr(self, 'server') and self.server_status:
            print("[DEBUG] 停止Web服务器...")
            self.stop_server()

        # 2. 停止所有工作线程（增加等待时间）
        print("[DEBUG] 停止所有工作线程...")
        self.stop_all_threads()

        # 3. 停止扫描定时器
        if hasattr(self, 'scan_timer') and self.scan_timer.isActive():
            print("[DEBUG] 停止扫描定时器...")
            self.scan_timer.stop()

        # 4. 停止多目录扫描管理器
        if hasattr(self, 'scan_manager'):
            print("[DEBUG] 停止扫描管理器...")
            self.scan_manager.stop_all()

        # 5. 特别处理MD5计算线程
        if hasattr(self, 'md5_worker') and self.md5_worker:
            print("[DEBUG] 停止MD5计算线程...")
            self.md5_worker.stop()

        if hasattr(self, 'md5_thread') and self.md5_thread and self.md5_thread.isRunning():
            print("[DEBUG] 等待MD5线程结束...")
            self.md5_thread.quit()
            self.md5_thread.wait(3000)  # 等待3秒

        # 6. 等待所有事件循环完成
        print("[DEBUG] 处理剩余事件...")
        QApplication.processEvents()
        
        # 7. 给线程一点时间自然退出
        import time
        time.sleep(0.5)

        # 8. 检查仍在运行的线程（不强制设置daemon，避免异常）
        import threading
        for thread in threading.enumerate():
            if thread != threading.current_thread() and thread.is_alive():
                print(f"[WARNING] 线程仍在运行: {thread.name}")

        print("[DEBUG] 应用程序关闭完成")
        event.accept()

    def cleanup_scan_states(self):
        """清理旧格式扫描状态文件"""
        try:
            state_dir = os.path.join(self.app_dir, "scan_states")
            if os.path.exists(state_dir):
                import pickle as _pkl
                for fname in os.listdir(state_dir):
                    fpath = os.path.join(state_dir, fname)
                    try:
                        with open(fpath, 'rb') as f:
                            data = _pkl.load(f)
                        # 删除无版本标记的旧格式文件
                        if not isinstance(data, dict) or data.get('__version__') != 2:
                            os.remove(fpath)
                    except:
                        os.remove(fpath)  # 损坏的文件也删除
        except Exception:
            pass

    def stop_all_threads(self):
        """停止所有工作线程 - 增强版本"""
        print("[DEBUG] 开始停止所有线程...")
        
        # 等待所有线程自然结束的列表
        active_threads = []
        
        # === 修改：PDF处理线程安全停止 ===
        if hasattr(self, 'pdf_processing_worker') and self.pdf_processing_worker:
            print("[DEBUG] 停止PDF处理线程...")
            try:
                if (hasattr(self, 'pdf_processing_thread') and 
                    self.pdf_processing_thread and 
                    self.pdf_processing_thread.isRunning()):
                    
                    self.pdf_processing_worker.stop()
                    self.pdf_processing_thread.quit()
                    active_threads.append(self.pdf_processing_thread)
            except Exception as e:
                print(f"[DEBUG] 停止PDF处理线程时出错: {e}")
            finally:
                self.pdf_processing_worker = None
                self.pdf_processing_thread = None

        # === PDF验证线程安全停止 ===
        if hasattr(self, 'pdf_validation_worker') and self.pdf_validation_worker:
            print("[DEBUG] 停止PDF验证线程...")
            try:
                if (hasattr(self, 'pdf_validation_thread') and 
                    self.pdf_validation_thread and 
                    self.pdf_validation_thread.isRunning()):
                    
                    self.pdf_validation_worker.stop()
                    self.pdf_validation_thread.quit()
                    active_threads.append(self.pdf_validation_thread)
            except Exception as e:
                print(f"[DEBUG] 停止PDF验证线程时出错: {e}")
            finally:
                self.pdf_validation_worker = None
                self.pdf_validation_thread = None

        # 停止批量封面处理线程
        if hasattr(self, 'batch_cover_worker') and self.batch_cover_worker:
            print("[DEBUG] 停止批量封面处理线程...")
            try:
                self.batch_cover_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止批量封面处理线程时出错: {e}")
        
        if hasattr(self, 'batch_cover_thread') and self.batch_cover_thread and self.batch_cover_thread.isRunning():
            print("[DEBUG] 等待批量封面线程结束...")
            self.batch_cover_thread.quit()
            active_threads.append(self.batch_cover_thread)
            self.batch_cover_worker = None
            self.batch_cover_thread = None

        # 停止PDF封面生成线程
        if hasattr(self, 'pdf_cover_worker') and self.pdf_cover_worker:
            print("[DEBUG] 停止PDF封面生成线程...")
            try:
                self.pdf_cover_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止PDF封面生成线程时出错: {e}")
        
        if hasattr(self, 'pdf_cover_thread') and self.pdf_cover_thread and self.pdf_cover_thread.isRunning():
            print("[DEBUG] 等待PDF封面线程结束...")
            self.pdf_cover_thread.quit()
            active_threads.append(self.pdf_cover_thread)
            self.pdf_cover_worker = None
            self.pdf_cover_thread = None

        # 停止备份线程
        if hasattr(self, 'backup_worker') and self.backup_worker:
            print("[DEBUG] 停止备份线程...")
            try:
                self.backup_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止备份线程时出错: {e}")
        
        if hasattr(self, 'backup_thread') and self.backup_thread and self.backup_thread.isRunning():
            print("[DEBUG] 等待备份线程结束...")
            self.backup_thread.quit()
            active_threads.append(self.backup_thread)
            self.backup_worker = None
            self.backup_thread = None
        
        # 停止恢复线程
        if hasattr(self, 'restore_worker') and self.restore_worker:
            print("[DEBUG] 停止恢复线程...")
            try:
                self.restore_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止恢复线程时出错: {e}")
        
        if hasattr(self, 'restore_thread') and self.restore_thread and self.restore_thread.isRunning():
            print("[DEBUG] 等待恢复线程结束...")
            self.restore_thread.quit()
            active_threads.append(self.restore_thread)
            self.restore_worker = None
            self.restore_thread = None
        
        # 停止下载线程
        if hasattr(self, 'download_worker') and self.download_worker:
            print("[DEBUG] 停止下载线程...")
            try:
                self.download_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止下载线程时出错: {e}")
        
        if hasattr(self, 'download_thread') and self.download_thread and self.download_thread.isRunning():
            print("[DEBUG] 等待下载线程结束...")
            self.download_thread.quit()
            active_threads.append(self.download_thread)
            self.download_worker = None
            self.download_thread = None
        
        # 停止单次扫描线程
        if hasattr(self, 'single_scan_worker') and self.single_scan_worker:
            print("[DEBUG] 停止单次扫描线程...")
            try:
                self.single_scan_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止单次扫描线程时出错: {e}")
        
        if hasattr(self, 'single_scan_thread') and self.single_scan_thread and self.single_scan_thread.isRunning():
            print("[DEBUG] 等待单次扫描线程结束...")
            self.single_scan_thread.quit()
            active_threads.append(self.single_scan_thread)
            self.single_scan_worker = None
            self.single_scan_thread = None
        
        # 停止MD5计算线程
        if hasattr(self, 'md5_worker') and self.md5_worker:
            print("[DEBUG] 停止MD5计算线程...")
            try:
                self.md5_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止MD5计算线程时出错: {e}")
        
        if hasattr(self, 'md5_thread') and self.md5_thread and self.md5_thread.isRunning():
            print("[DEBUG] 等待MD5线程结束...")
            self.md5_thread.quit()
            active_threads.append(self.md5_thread)
            self.md5_worker = None
            self.md5_thread = None
        
        # 停止线程池
        if hasattr(self, 'thread_pool'):
            print("[DEBUG] 关闭线程池...")
            try:
                self.thread_pool.shutdown(wait=False)
            except Exception as e:
                print(f"[DEBUG] 关闭线程池时出错: {e}")
        
        # 停止多目录扫描管理器
        if hasattr(self, 'scan_manager'):
            print("[DEBUG] 停止扫描管理器...")
            try:
                self.scan_manager.stop_all()
            except Exception as e:
                print(f"[DEBUG] 停止扫描管理器时出错: {e}")
        
        # === 停止封面处理线程 ===
        if hasattr(self, 'cover_worker') and self.cover_worker:
            print("[DEBUG] 停止封面处理线程...")
            try:
                self.cover_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止封面处理线程时出错: {e}")
        
        if hasattr(self, 'cover_thread') and self.cover_thread and self.cover_thread.isRunning():
            print("[DEBUG] 等待封面处理线程结束...")
            self.cover_thread.quit()
            active_threads.append(self.cover_thread)
            self.cover_worker = None
            self.cover_thread = None
        
        # === 停止数据库保存线程 ===
        if hasattr(self, 'db_save_worker') and self.db_save_worker:
            print("[DEBUG] 停止数据库保存线程...")
            try:
                self.db_save_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止数据库保存线程时出错: {e}")
        
        if hasattr(self, 'db_save_thread') and self.db_save_thread and self.db_save_thread.isRunning():
            print("[DEBUG] 等待数据库保存线程结束...")
            self.db_save_thread.quit()
            active_threads.append(self.db_save_thread)
            self.db_save_worker = None
            self.db_save_thread = None
        
        # === 停止目录扫描线程 ===
        if hasattr(self, 'directory_scan_worker') and self.directory_scan_worker:
            print("[DEBUG] 停止目录扫描线程...")
            try:
                self.directory_scan_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止目录扫描线程时出错: {e}")
        
        if hasattr(self, 'directory_scan_thread') and self.directory_scan_thread and self.directory_scan_thread.isRunning():
            print("[DEBUG] 等待目录扫描线程结束...")
            self.directory_scan_thread.quit()
            active_threads.append(self.directory_scan_thread)
            self.directory_scan_worker = None
            self.directory_scan_thread = None
        
        # === 停止静态文件下载线程 ===
        if hasattr(self, 'static_download_worker') and self.static_download_worker:
            print("[DEBUG] 停止静态文件下载线程...")
            try:
                self.static_download_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止静态文件下载线程时出错: {e}")
        
        if hasattr(self, 'static_download_thread') and self.static_download_thread and self.static_download_thread.isRunning():
            print("[DEBUG] 等待静态文件下载线程结束...")
            self.static_download_thread.quit()
            active_threads.append(self.static_download_thread)
            self.static_download_worker = None
            self.static_download_thread = None
        
        # 等待所有线程结束
        if active_threads:
            print(f"[DEBUG] 等待 {len(active_threads)} 个线程结束...")
            for thread in active_threads:
                if thread and thread.isRunning():
                    if not thread.wait(3000):  # 每个线程最多等待3秒
                        print(f"[WARNING] 线程 {thread} 未能在3秒内结束")
                        if hasattr(thread, 'terminate'):
                            thread.terminate()
                            thread.wait(1000)
        
        print("[DEBUG] 所有线程停止完成")




    def auto_start_web_server(self):
        """自动启动Web服务器"""
        auto_start = self.get_setting('auto_start_server', '1') == '1'
        
        if auto_start:
            print("[SERVER] 自动启动Web服务器...")
            self._auto_started = True
            if self.start_server():
                self.update_status_bar("Web服务器已自动启动", 3000)
            else:
                self.update_status_bar("Web服务器启动失败", 3000)
            self._auto_started = False

    def update_server_status_display(self):
        """更新服务器状态显示"""
        if self.server_status:
            # 服务器运行中
            self.server_status_indicator.setText("🟢 服务器运行中")
            self.server_status_indicator.setStyleSheet("""
                QLabel {
                    padding: 5px 10px;
                    border: 1px solid #4caf50;
                    border-radius: 10px;
                    background-color: #e8f5e8;
                    color: #2e7d32;
                    font-weight: bold;
                }
            """)
            
            server_url = self.server.get_server_url()
            self.status_server_info.setText(f"服务器: {server_url}")
            
            # 更新服务器动作文本
            self.server_action.setText("🚫停止Web服务器")
            self.server_action.setIcon(QIcon.fromTheme("network-server-disconnect"))
        else:
            # 服务器停止
            self.server_status_indicator.setText("🔴 服务器离线")
            self.server_status_indicator.setStyleSheet("""
                QLabel {
                    padding: 5px 10px;
                    border: 1px solid #ccc;
                    border-radius: 10px;
                    background-color: #ffebee;
                    color: #c62828;
                    font-weight: bold;
                }
            """)
            
            self.status_server_info.setText("服务器: 未启动")
            
            # 更新服务器动作文本
            self.server_action.setText("🌐启动Web服务器")
            self.server_action.setIcon(QIcon.fromTheme("network-server"))
        
        # 强制刷新显示
        self.server_status_indicator.update()
        self.status_server_info.update()

    def normalize_network_path(self, path):
        """规范化网络路径，统一使用反斜杠（Windows）"""
        if not path:
            return path
        
        print(f"[DEBUG] 原始路径: {path}")
        
        # Windows系统使用反斜杠
        if sys.platform == "win32":
            normalized_path = path.replace('/', '\\')
            # 确保网络路径以双反斜杠开头
            if normalized_path.startswith('\\\\'):
                # 清理路径中的多余反斜杠
                parts = [part for part in normalized_path.split('\\') if part]
                if parts:
                    normalized_path = '\\\\' + '\\'.join(parts)
        else:
            # Linux/macOS 使用正斜杠
            normalized_path = path.replace('\\', '/')
            if normalized_path.startswith('//'):
                parts = [part for part in normalized_path.split('/') if part]
                if parts:
                    normalized_path = '//' + '/'.join(parts)
        
        print(f"[DEBUG] 规范化后路径: {normalized_path}")
        return normalized_path



    def normalize_path_separators(self, path):
        """统一路径分隔符，将正斜杠转换为反斜杠（Windows系统）"""
        if not path:
            return path
        
        # Windows系统使用反斜杠
        if sys.platform == "win32":
            normalized_path = path.replace('/', '\\')
            # 确保网络路径格式正确
            if normalized_path.startswith('\\\\'):
                # 对于网络路径，确保格式正确
                normalized_path = '\\\\' + normalized_path[2:].replace('\\\\', '\\')
            return normalized_path
        else:
            # Linux/macOS 使用正斜杠
            return path.replace('\\', '/')


    def normalize_path_for_os(self, path):
        """根据当前操作系统规范化路径分隔符 - 修复SMB路径"""
        if not path:
            return path
        
        # 保存SMB路径标志
        is_smb = path.startswith('\\\\') or path.startswith('//')
        
        if sys.platform == "win32":
            # Windows 使用反斜杠
            normalized = path.replace('/', '\\')
            
            # 确保SMB路径格式正确
            if is_smb:
                # 确保以双反斜杠开头
                if normalized.startswith('\\\\'):
                    pass  # 已经正确
                elif normalized.startswith('\\'):
                    normalized = '\\\\' + normalized[1:]
                else:
                    # 检查是否应该是SMB路径
                    if '\\\\' in normalized:
                        normalized = '\\\\' + normalized.split('\\\\', 1)[1]
            else:
                # 本地路径，移除可能的双斜杠开头
                while normalized.startswith('\\\\') and not is_smb:
                    normalized = normalized[1:]
            
            return normalized
        else:
            # Linux/macOS 使用正斜杠
            normalized = path.replace('\\', '/')
            if is_smb:
                # 确保以双斜杠开头
                if normalized.startswith('//'):
                    pass  # 已经正确
                elif normalized.startswith('/'):
                    normalized = '//' + normalized[1:]
            return normalized

    def print_database_data_for_directory(self, directory_path):
        """打印数据库中对应目录的数据"""
        if not self.user_manager.current_db_path:
            print("[INFO] 未登录用户，无法查询数据库")
            return
        
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            
            # 查询数据库中该目录的信息
            cursor.execute("""
                SELECT name, path, directory_exists, created_time, last_modified, is_directory, last_scanned
                FROM directories 
                WHERE path = ?
            """, (directory_path,))
            
            result = cursor.fetchone()
            
            if result:
                name, path, exists, created_time, last_modified, is_directory, last_scanned = result
                print("=" * 50)
                print("数据库对应数据:")
                print(f"目录名称: {name}")
                print(f"完整路径: {path}")
                print(f"是否存在: {'是' if exists else '否'}")
                print(f"创建时间: {created_time}")
                print(f"最后修改: {last_modified}")
                print(f"是否目录: {'是' if is_directory else '否'}")
                print(f"最后扫描: {last_scanned}")
                print("=" * 50)
            else:
                print(f"[INFO] 数据库中未找到目录: {directory_path}")
            
            conn.close()
            
        except Exception as e:
            print(f"[ERROR] 查询数据库失败: {e}")

    def get_database_path_for_item(self, post_path):
        """根据POST路径查询数据库中的正确路径"""
        print(f"[DATABASE PATH] 查询数据库路径 for: {post_path}")
        if not self.user_manager.current_db_path:
            return None
        
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            
            # 多种查询策略
            basename = os.path.basename(post_path)
            print(f"[DATABASE PATH] 目录名称: {basename}")
            
            # 策略1: 精确匹配名称
            cursor.execute("SELECT path FROM directories WHERE name = ?", (basename,))
            results = cursor.fetchall()
            print(f"[DATABASE PATH] 策略1结果数: {len(results)}")
            
            # 策略2: 路径包含匹配
            if not results:
                cursor.execute("SELECT path FROM directories WHERE path LIKE ?", (f"%{basename}%",))
                results = cursor.fetchall()
                print(f"[DATABASE PATH] 策略2结果数: {len(results)}")   
            
            # 策略3: 路径结尾匹配
            if not results:
                cursor.execute("SELECT path FROM directories WHERE path LIKE ?", (f"%{basename}",))
                results = cursor.fetchall()
                print(f"[DATABASE PATH] 策略3结果数: {len(results)}")
            
            conn.close()
            
            if results:
                # 优先选择路径最匹配的结果
                for result in results:
                    db_path = result[0]
                    if db_path.endswith(basename):
                        print(f"[DATABASE PATH] 找到匹配的数据库路径: {db_path}")
                        return db_path
                
                # 返回第一个结果
                db_path = results[0][0]
                print(f"[DATABASE PATH] 使用第一个数据库路径: {db_path}")
                return db_path
            
            return None
            
        except Exception as e:
            print(f"[DATABASE ERROR] 查询数据库路径失败: {e}")
            return None

    def restart_server_if_needed(self, old_port, new_port):
        """如果需要，重新启动服务器（端口变更时）"""
        if hasattr(self, 'server') and self.server_status:
            if old_port != new_port:
                reply = QMessageBox.question(
                    self, "端口变更",
                    f"服务器端口已从 {old_port} 变更为 {new_port}，需要重启服务器才能生效。\n是否立即重启服务器？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    self.stop_server()
                    # 重新初始化服务器
                    self.init_server()
                    if self.get_setting('auto_start_server', '1') == '1':
                        self.start_server()

    def batch_save_all_covers_threaded(self):
        """多线程批量保存所有封面"""
        if not self.user_manager.current_db_path:
            QMessageBox.warning(self, "未登录", "请先登录用户")
            return
        
        # 获取所有目录
        directories = self.get_current_directories()
        if not directories:
            QMessageBox.information(self, "提示", "没有可处理的目录")
            return
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("准备批量保存封面...")
        
        # 创建工作线程
        self.batch_cover_worker = BatchCoverSaveWorker(self, directories, "save_all")
        self.batch_cover_thread = QThread()
        
        self.batch_cover_worker.moveToThread(self.batch_cover_thread)
        self.batch_cover_worker.progress_updated.connect(self.on_batch_cover_progress)
        self.batch_cover_worker.finished.connect(self.on_batch_cover_finished)
        self.batch_cover_worker.error_occurred.connect(self.on_batch_cover_error)
        
        self.batch_cover_thread.started.connect(self.batch_cover_worker.process_batch_covers)
        self.batch_cover_worker.finished.connect(self.batch_cover_thread.quit)
        self.batch_cover_worker.finished.connect(self.batch_cover_worker.deleteLater)
        self.batch_cover_thread.finished.connect(self.batch_cover_thread.deleteLater)
        
        self.batch_cover_thread.start()
    
    def batch_save_missing_covers_threaded(self):
        """多线程批量保存缺失封面"""
        if not self.user_manager.current_db_path:
            QMessageBox.warning(self, "未登录", "请先登录用户")
            return
        
        directories = self.get_current_directories()
        if not directories:
            QMessageBox.information(self, "提示", "没有可处理的目录")
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("准备保存缺失封面...")
        
        self.batch_cover_worker = BatchCoverSaveWorker(self, directories, "save_missing")
        self.batch_cover_thread = QThread()
        
        self.batch_cover_worker.moveToThread(self.batch_cover_thread)
        self.batch_cover_worker.progress_updated.connect(self.on_batch_cover_progress)
        self.batch_cover_worker.finished.connect(self.on_batch_cover_finished)
        self.batch_cover_worker.error_occurred.connect(self.on_batch_cover_error)
        
        self.batch_cover_thread.started.connect(self.batch_cover_worker.process_batch_covers)
        self.batch_cover_worker.finished.connect(self.batch_cover_thread.quit)
        self.batch_cover_worker.finished.connect(self.batch_cover_worker.deleteLater)
        self.batch_cover_thread.finished.connect(self.batch_cover_thread.deleteLater)
        
        self.batch_cover_thread.start()
    
    # PDF封面生成 - 多线程版本
    def batch_generate_pdf_covers_threaded(self):
        """多线程批量生成PDF封面 - 使用新的多线程处理"""
        self.batch_process_pdfs_threaded("generate_covers")

    
    def on_cover_progress_updated(self, progress, message):
        """封面处理进度更新"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(message)
        QApplication.processEvents()
    
    def on_cover_saved(self, dir_path, cover_path):
        """封面保存成功"""
        print(f"[COVER SUCCESS] 封面保存成功: {dir_path} -> {cover_path}")
    
    def on_cover_processing_finished(self):
        """封面处理完成"""
        self.progress_label.setText("封面处理完成")
        QTimer.singleShot(2000, self.hide_progress_bar)
        QMessageBox.information(self, "完成", "封面处理已完成")
    
    def on_pdf_cover_generated(self, pdf_path, cover_path):
        """PDF封面生成成功"""
        print(f"[PDF COVER SUCCESS] PDF封面生成成功: {pdf_path}")
    
    def on_pdf_cover_generation_finished(self):
        """PDF封面生成完成"""
        self.progress_label.setText("PDF封面生成完成")
        QTimer.singleShot(2000, self.hide_progress_bar)
        QMessageBox.information(self, "完成", "PDF封面生成已完成")
    
    def on_cover_error(self, error_msg, path):
        """封面处理错误"""
        print(f"[COVER ERROR] {path}: {error_msg}")
        # 可以选择记录到日志文件，而不是弹窗打扰用户
    
    def get_all_directories_from_db(self):
        """从数据库获取所有目录数据"""
        if not self.user_manager.current_db_path:
            return []
        
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, path, directory_exists, created_time, last_modified, is_directory 
                FROM directories 
                ORDER BY name
            """)
            directories = []
            for row in cursor.fetchall():
                name, path, exists, created_time, last_modified, is_directory = row
                directories.append({
                    "name": name,
                    "path": path,
                    "exists": bool(exists),
                    "created_time": created_time,
                    "last_modified": last_modified,
                    "is_directory": bool(is_directory)
                })
            conn.close()
            return directories
        except Exception as e:
            print(f"[ERROR] 获取目录数据失败: {e}")
            return []
    
    def find_all_pdf_files(self):
        """查找所有PDF文件 - 增强版本"""
        pdf_files = []
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT path FROM directories 
                WHERE is_directory = 0 AND path LIKE '%.pdf' AND directory_exists = 1
            """)
            results = cursor.fetchall()
            
            # 只返回存在的文件
            pdf_files = [row[0] for row in results if os.path.exists(row[0])]
            
            conn.close()
            print(f"[PDF FIND] 找到 {len(pdf_files)} 个存在的PDF文件")
        except Exception as e:
            print(f"[PDF FIND ERROR] 查找PDF文件失败: {e}")
        
        return pdf_files

    
    def stop_cover_processing(self):
        """停止封面处理"""
        if self.cover_worker:
            self.cover_worker.stop()
        if self.cover_thread and self.cover_thread.isRunning():
            self.cover_thread.quit()
            self.cover_thread.wait(5000)  # 等待5秒
        
        if self.pdf_cover_worker:
            self.pdf_cover_worker.stop()
        if self.pdf_cover_thread and self.pdf_cover_thread.isRunning():
            self.pdf_cover_thread.quit()
            self.pdf_cover_thread.wait(5000)
        
        # 停止线程池中的所有任务
        self.thread_pool.cancel_all()

    def save_covers_async(self, directories, cover_save_dir, cover_save_mode, skip_existing):
        """异步保存封面 - 完全多线程版本，包括MD5比对"""
        print(f"[COVER ASYNC] 开始异步保存 {len(directories)} 个目录的封面")
        
        def calculate_md5(file_path):
            """计算文件的MD5哈希值 - 线程安全"""
            try:
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.md5()
                    while chunk := f.read(8192):
                        file_hash.update(chunk)
                    return file_hash.hexdigest()
            except Exception as e:
                print(f"[MD5 ERROR] 计算MD5失败 {file_path}: {e}")
                return None
        
        def save_single_cover(dir_info):
            """保存单个目录的封面 - 完全多线程版本"""
            try:
                dir_path = dir_info["path"]
                if not os.path.exists(dir_path):
                    return {"status": "failed", "reason": "目录不存在", "path": dir_path}
                
                # 查找封面图片
                cover_path = self.find_cover_image(dir_path)
                if not cover_path or not os.path.exists(cover_path):
                    # 检查是否是PDF文件，尝试生成封面
                    if self.is_pdf_directory(dir_path):
                        pdf_file = self.find_pdf_file(dir_path)
                        if pdf_file:
                            # 使用线程池提交PDF封面生成任务
                            pdf_future = self.thread_pool.submit_task(self.generate_pdf_cover, pdf_file)
                            try:
                                # 等待PDF封面生成完成（带超时）
                                pdf_result = pdf_future.result(timeout=30)  # 30秒超时
                                if pdf_result:
                                    return {"status": "saved", "type": "pdf", "path": dir_path}
                            except Exception as e:
                                print(f"[PDF COVER GENERATION ERROR] {pdf_file}: {e}")
                                return {"status": "failed", "reason": f"PDF封面生成失败: {e}", "path": dir_path}
                    return {"status": "failed", "reason": "未找到封面图片", "path": dir_path}
                
                # 检查是否需要跳过已存在的封面 - 多线程MD5比对
                if skip_existing:
                    expected_save_path = self.get_expected_cover_path(dir_path, cover_save_dir, cover_save_mode)
                    if expected_save_path and os.path.exists(expected_save_path):
                        # 使用线程池并行计算MD5
                        md5_future1 = self.thread_pool.submit_task(calculate_md5, cover_path)
                        md5_future2 = self.thread_pool.submit_task(calculate_md5, expected_save_path)
                        
                        try:
                            # 等待两个MD5计算完成
                            md5_cover = md5_future1.result(timeout=10)  # 10秒超时
                            md5_existing = md5_future2.result(timeout=10)
                            
                            if md5_cover and md5_existing and md5_cover == md5_existing:
                                return {"status": "skipped", "reason": "封面已存在且相同", "path": dir_path}
                        except Exception as e:
                            print(f"[MD5 COMPARISON ERROR] {dir_path}: {e}")
                            # MD5计算失败时继续保存，不跳过
                
                # 保存封面图片 - 使用线程池处理图片保存
                save_future = self.thread_pool.submit_task(self.save_cover_image, dir_path, cover_path)
                try:
                    save_result = save_future.result(timeout=15)  # 15秒超时
                    if save_result:
                        return {"status": "saved", "type": "image", "path": dir_path}
                    else:
                        return {"status": "failed", "reason": "保存失败", "path": dir_path}
                except Exception as e:
                    return {"status": "error", "reason": f"保存超时或失败: {e}", "path": dir_path}
                    
            except Exception as e:
                return {"status": "error", "reason": str(e), "path": dir_info.get("path", "unknown")}
        
        # 批量提交封面保存任务
        print(f"[COVER ASYNC] 提交 {len(directories)} 个封面保存任务到线程池")
        
        # 分批处理，避免一次性提交太多任务
        batch_size = 20
        all_futures = []
        
        for i in range(0, len(directories), batch_size):
            batch = directories[i:i + batch_size]
            batch_futures = []
            
            for dir_info in batch:
                future = self.thread_pool.submit_task(save_single_cover, dir_info)
                batch_futures.append(future)
            
            all_futures.extend(batch_futures)
            
            # 小批量延迟，避免瞬间创建太多线程
            if i + batch_size < len(directories):
                time.sleep(0.1)  # 100ms延迟
        
        # 异步处理结果统计
        def process_cover_results():
            """处理封面保存结果 - 多线程版本"""
            try:
                saved_count = 0
                skipped_count = 0
                failed_count = 0
                error_count = 0
                pdf_count = 0
                
                # 使用线程池并行处理结果收集
                def check_future_status(future):
                    """检查单个future的状态"""
                    try:
                        result = future.result(timeout=1)  # 1秒超时获取结果
                        return result
                    except Exception as e:
                        return {"status": "error", "reason": f"获取结果失败: {e}", "path": "unknown"}
                
                # 分批处理结果，避免内存占用过大
                results = []
                for i in range(0, len(all_futures), batch_size):
                    batch_futures = all_futures[i:i + batch_size]
                    
                    # 并行检查future状态
                    batch_results = []
                    for future in batch_futures:
                        result_future = self.thread_pool.submit_task(check_future_status, future)
                        batch_results.append(result_future)
                    
                    # 收集批次结果
                    for result_future in batch_results:
                        try:
                            result = result_future.result(timeout=5)
                            results.append(result)
                        except Exception:
                            results.append({"status": "error", "reason": "结果收集超时", "path": "unknown"})
                
                # 统计结果
                for result in results:
                    if result["status"] == "saved":
                        saved_count += 1
                        if result.get("type") == "pdf":
                            pdf_count += 1
                        print(f"[COVER ASYNC SUCCESS] 封面保存成功: {result['path']}")
                    elif result["status"] == "skipped":
                        skipped_count += 1
                    elif result["status"] == "failed":
                        failed_count += 1
                        print(f"[COVER ASYNC FAILED] {result['path']}: {result['reason']}")
                    elif result["status"] == "error":
                        error_count += 1
                        print(f"[COVER ASYNC ERROR] {result['path']}: {result['reason']}")
                
                # 在主线程中更新状态栏
                def update_ui():
                    stats_msg = (f"封面保存完成: 保存 {saved_count} (PDF: {pdf_count}), "
                            f"跳过 {skipped_count}, 失败 {failed_count}, 错误 {error_count}")
                    self.update_status_bar(stats_msg, 5000)
                    print(f"[COVER ASYNC FINISH] {stats_msg}")
                
                # 使用单次定时器确保在主线程中更新UI
                QTimer.singleShot(0, update_ui)
                
            except Exception as e:
                print(f"[COVER ASYNC RESULT ERROR] 处理封面保存结果时出错: {e}")
                
                def show_error_ui():
                    self.update_status_bar(f"封面保存结果处理出错: {e}", 3000)
                
                QTimer.singleShot(0, show_error_ui)
        
        # 启动结果处理线程
        result_thread = threading.Thread(target=process_cover_results, daemon=True)
        result_thread.start()
        
        return len(directories)  # 返回任务数量

    def is_pdf_directory(self, dir_path):
        """检查目录是否包含PDF文件"""
        if not os.path.isdir(dir_path):
            return False
        
        try:
            for file in os.listdir(dir_path):
                if file.lower().endswith('.pdf'):
                    return True
            return False
        except Exception:
            return False

    def find_pdf_file(self, dir_path):
        """在目录中查找PDF文件"""
        if not os.path.isdir(dir_path):
            return None
        
        try:
            for file in os.listdir(dir_path):
                if file.lower().endswith('.pdf'):
                    return os.path.join(dir_path, file)
            return None
        except Exception:
            return None

    def on_batch_cover_progress(self, progress, message):
        """批量封面保存进度更新"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(message)
    
    def on_batch_cover_finished(self, success_count, skip_count, error_count):
        """批量封面保存完成"""
        self.progress_bar.setValue(100)
        self.progress_label.setText(f"封面保存完成: 成功{success_count}, 跳过{skip_count}, 失败{error_count}")
        
        # 3秒后隐藏进度条
        QTimer.singleShot(3000, self.hide_progress_bar)
        
        QMessageBox.information(self, "完成", 
                               f"封面保存完成:\n成功: {success_count}\n跳过: {skip_count}\n失败: {error_count}")
    
    def on_batch_cover_error(self, error_message):
        """批量封面保存错误"""
        self.progress_bar.setValue(0)
        self.progress_label.setText("封面保存失败")
        QMessageBox.critical(self, "错误", f"封面保存过程中出错:\n{error_message}")
        self.hide_progress_bar()
    
    

    
    def on_pdf_cover_progress(self, progress, message):
        """PDF封面生成进度更新"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(message)
    
    def on_pdf_cover_finished(self, success_count, error_count):
        """PDF封面生成完成"""
        self.progress_bar.setValue(100)
        self.progress_label.setText(f"PDF封面生成完成: 成功{success_count}, 失败{error_count}")
        
        QTimer.singleShot(3000, self.hide_progress_bar)
        
        QMessageBox.information(self, "完成", 
                               f"PDF封面生成完成:\n成功: {success_count}\n失败: {error_count}")
    
    def on_pdf_cover_error(self, error_message):
        """PDF封面生成错误"""
        self.progress_bar.setValue(0)
        self.progress_label.setText("PDF封面生成失败")
        QMessageBox.critical(self, "错误", f"PDF封面生成过程中出错:\n{error_message}")
        self.hide_progress_bar()
    
    # 数据库备份 - 多线程版本
    def manual_backup_threaded(self):
        """多线程手动备份数据库"""
        if not self.user_manager.current_db_path:
            QMessageBox.warning(self, "未登录", "请先登录用户")
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("准备数据库备份...")
        
        self.backup_worker = DatabaseBackupWorker(self.backup_manager, self.user_manager.current_db_path, "manual")
        self.backup_thread = QThread()
        
        self.backup_worker.moveToThread(self.backup_thread)
        self.backup_worker.progress_updated.connect(self.on_backup_progress)
        self.backup_worker.backup_finished.connect(self.on_backup_finished)
        
        self.backup_thread.started.connect(self.backup_worker.create_backup)
        self.backup_worker.finished.connect(self.backup_thread.quit)
        self.backup_worker.finished.connect(self.backup_worker.deleteLater)
        self.backup_thread.finished.connect(self.backup_thread.deleteLater)
        
        self.backup_thread.start()
    
    def on_backup_progress(self, progress, message):
        """备份进度更新"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(message)
    
    def on_backup_finished(self, backup_path, success, error_message):
        """备份完成"""
        if success:
            self.progress_bar.setValue(100)
            self.progress_label.setText("备份完成")
            QMessageBox.information(self, "成功", f"数据库已备份到:\n{backup_path}")
        else:
            self.progress_bar.setValue(0)
            self.progress_label.setText("备份失败")
            QMessageBox.critical(self, "失败", f"备份失败:\n{error_message}")
        
        QTimer.singleShot(3000, self.hide_progress_bar)
    
    # 数据库恢复 - 多线程版本
    def restore_database_threaded(self, backup_path):
        """多线程恢复数据库"""
        if not self.user_manager.current_db_path:
            QMessageBox.warning(self, "未登录", "请先登录用户")
            return
        
        reply = QMessageBox.question(
            self, "确认恢复",
            "确定要恢复此备份吗？当前数据库将被替换。\n建议先手动备份当前数据库。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("准备数据库恢复...")
        
        self.restore_worker = DatabaseRestoreWorker(self.backup_manager, backup_path, self.user_manager.current_db_path)
        self.restore_thread = QThread()
        
        self.restore_worker.moveToThread(self.restore_thread)
        self.restore_worker.progress_updated.connect(self.on_restore_progress)
        self.restore_worker.restore_finished.connect(self.on_restore_finished)
        
        self.restore_thread.started.connect(self.restore_worker.restore_backup)
        self.restore_worker.finished.connect(self.restore_thread.quit)
        self.restore_worker.finished.connect(self.restore_worker.deleteLater)
        self.restore_thread.finished.connect(self.restore_thread.deleteLater)
        
        self.restore_thread.start()
    
    def on_restore_progress(self, progress, message):
        """恢复进度更新"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(message)
    
    def on_restore_finished(self, success, error_message):
        """恢复完成"""
        if success:
            self.progress_bar.setValue(100)
            self.progress_label.setText("恢复完成")
            QMessageBox.information(self, "成功", "数据库已成功恢复")
            # 重新加载数据
            self.load_directories()
        else:
            self.progress_bar.setValue(0)
            self.progress_label.setText("恢复失败")
            QMessageBox.critical(self, "失败", f"恢复失败:\n{error_message}")
        
        QTimer.singleShot(3000, self.hide_progress_bar)
    
    # 静态文件下载 - 多线程版本
    def download_static_files_threaded(self):
        """多线程下载静态文件"""
        static_files = {
            'epub.js': {
                'url': 'https://cdn.jsdelivr.net/npm/epubjs/dist/epub.min.js',
                'description': 'EPUB.js库'
            },
            'jszip.min.js': {
                'url': 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js',
                'description': 'JSZip库'
            }
        }
        
        static_dir = os.path.join(self.app_dir, "static")
        os.makedirs(static_dir, exist_ok=True)
        
        # 过滤需要下载的文件
        download_files = []
        for filename, file_info in static_files.items():
            file_path = os.path.join(static_dir, filename)
            if not os.path.exists(file_path):
                download_files.append({
                    'filename': filename,
                    'url': file_info['url'],
                    'description': file_info['description']
                })
        
        if not download_files:
            print("[STATIC] 所有静态文件已存在")
            return
        
        print(f"[STATIC] 需要下载 {len(download_files)} 个文件")
        
        self.download_worker = StaticFileDownloadWorker(download_files, static_dir)
        self.download_thread = QThread()
        
        self.download_worker.moveToThread(self.download_thread)
        self.download_worker.progress_updated.connect(self.on_download_progress)
        self.download_worker.download_finished.connect(self.on_download_file_finished)
        self.download_worker.all_finished.connect(self.on_download_all_finished)
        
        self.download_thread.started.connect(self.download_worker.download_files_parallel)
        self.download_worker.all_finished.connect(self.download_thread.quit)
        self.download_worker.all_finished.connect(self.download_worker.deleteLater)
        self.download_thread.finished.connect(self.download_thread.deleteLater)
        
        self.download_thread.start()
    
    def on_download_progress(self, progress, message):
        """下载进度更新"""
        # 只在有实际下载时显示进度
        if progress > 0 and progress < 100:
            if not self.progress_bar.isVisible():
                self.progress_bar.setVisible(True)
            self.progress_bar.setValue(progress)
            self.progress_label.setText(message)
    
    def on_download_file_finished(self, filename, success, message):
        """单个文件下载完成"""
        if success:
            print(f"[STATIC] ✓ {filename} 下载成功")
        else:
            print(f"[STATIC] ❌ {filename} 下载失败: {message}")
    
    def on_download_all_finished(self):
        """所有文件下载完成"""
        self.hide_progress_bar()
        print("[STATIC] 静态文件下载任务完成")
    

    
    def stop_all_threads(self):
        """停止所有工作线程 - 增强版本"""
        print("[DEBUG] 开始停止所有线程...")
        
        # === 修改：PDF处理线程安全停止 ===
        if hasattr(self, 'pdf_processing_worker') and self.pdf_processing_worker:
            print("[DEBUG] 停止PDF处理线程...")
            try:
                # 检查线程是否仍然有效
                if (hasattr(self, 'pdf_processing_thread') and 
                    self.pdf_processing_thread and 
                    self.pdf_processing_thread.isRunning()):
                    
                    self.pdf_processing_worker.stop()
                    self.pdf_processing_thread.quit()
                    if not self.pdf_processing_thread.wait(2000):  # 等待2秒
                        print("[DEBUG] PDF处理线程等待超时，强制终止")
                        self.pdf_processing_thread.terminate()
                        self.pdf_processing_thread.wait(1000)
                else:
                    print("[DEBUG] PDF处理线程已停止或不存在，跳过")
                    
            except RuntimeError as e:
                if "wrapped C/C++ object has been deleted" in str(e):
                    print("[DEBUG] PDF处理线程对象已被删除，正常跳过")
                else:
                    print(f"[DEBUG] 停止PDF处理线程时出现RuntimeError: {e}")
            except Exception as e:
                print(f"[DEBUG] 停止PDF处理线程时出现意外错误: {e}")
            finally:
                # 清理引用
                if hasattr(self, 'pdf_processing_worker'):
                    self.pdf_processing_worker = None
                if hasattr(self, 'pdf_processing_thread'):
                    self.pdf_processing_thread = None

        # === 新增：PDF验证线程安全停止 ===
        if hasattr(self, 'pdf_validation_worker') and self.pdf_validation_worker:
            print("[DEBUG] 停止PDF验证线程...")
            try:
                # 检查线程是否仍然有效
                if (hasattr(self, 'pdf_validation_thread') and 
                    self.pdf_validation_thread and 
                    self.pdf_validation_thread.isRunning()):
                    
                    self.pdf_validation_worker.stop()
                    self.pdf_validation_thread.quit()
                    if not self.pdf_validation_thread.wait(2000):  # 等待2秒
                        print("[DEBUG] PDF验证线程等待超时，强制终止")
                        self.pdf_validation_thread.terminate()
                        self.pdf_validation_thread.wait(1000)
                else:
                    print("[DEBUG] PDF验证线程已停止或不存在，跳过")
                    
            except RuntimeError as e:
                if "wrapped C/C++ object has been deleted" in str(e):
                    print("[DEBUG] PDF验证线程对象已被删除，正常跳过")
                else:
                    print(f"[DEBUG] 停止PDF验证线程时出现RuntimeError: {e}")
            except Exception as e:
                print(f"[DEBUG] 停止PDF验证线程时出现意外错误: {e}")
            finally:
                # 清理引用
                if hasattr(self, 'pdf_validation_worker'):
                    self.pdf_validation_worker = None
                if hasattr(self, 'pdf_validation_thread'):
                    self.pdf_validation_thread = None

        # 停止批量封面处理线程
        if hasattr(self, 'batch_cover_worker') and self.batch_cover_worker:
            print("[DEBUG] 停止批量封面处理线程...")
            try:
                self.batch_cover_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止批量封面处理线程时出错: {e}")
        
        if hasattr(self, 'batch_cover_thread') and self.batch_cover_thread and self.batch_cover_thread.isRunning():
            print("[DEBUG] 等待批量封面线程结束...")
            try:
                self.batch_cover_thread.quit()
                if not self.batch_cover_thread.wait(2000):
                    print("[DEBUG] 批量封面线程等待超时，强制终止")
                    self.batch_cover_thread.terminate()
                    self.batch_cover_thread.wait(1000)
            except Exception as e:
                print(f"[DEBUG] 停止批量封面线程时出错: {e}")
            finally:
                self.batch_cover_worker = None
                self.batch_cover_thread = None

        # 停止PDF封面生成线程
        if hasattr(self, 'pdf_cover_worker') and self.pdf_cover_worker:
            print("[DEBUG] 停止PDF封面生成线程...")
            try:
                self.pdf_cover_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止PDF封面生成线程时出错: {e}")
        
        if hasattr(self, 'pdf_cover_thread') and self.pdf_cover_thread and self.pdf_cover_thread.isRunning():
            print("[DEBUG] 等待PDF封面线程结束...")
            try:
                self.pdf_cover_thread.quit()
                if not self.pdf_cover_thread.wait(2000):
                    print("[DEBUG] PDF封面线程等待超时，强制终止")
                    self.pdf_cover_thread.terminate()
                    self.pdf_cover_thread.wait(1000)
            except Exception as e:
                print(f"[DEBUG] 停止PDF封面线程时出错: {e}")
            finally:
                self.pdf_cover_worker = None
                self.pdf_cover_thread = None

        # 停止备份线程
        if hasattr(self, 'backup_worker') and self.backup_worker:
            print("[DEBUG] 停止备份线程...")
            try:
                self.backup_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止备份线程时出错: {e}")
        
        if hasattr(self, 'backup_thread') and self.backup_thread and self.backup_thread.isRunning():
            print("[DEBUG] 等待备份线程结束...")
            try:
                self.backup_thread.quit()
                if not self.backup_thread.wait(2000):
                    print("[DEBUG] 备份线程等待超时，强制终止")
                    self.backup_thread.terminate()
                    self.backup_thread.wait(1000)
            except Exception as e:
                print(f"[DEBUG] 停止备份线程时出错: {e}")
            finally:
                self.backup_worker = None
                self.backup_thread = None
        
        # 停止恢复线程
        if hasattr(self, 'restore_worker') and self.restore_worker:
            print("[DEBUG] 停止恢复线程...")
            try:
                self.restore_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止恢复线程时出错: {e}")
        
        if hasattr(self, 'restore_thread') and self.restore_thread and self.restore_thread.isRunning():
            print("[DEBUG] 等待恢复线程结束...")
            try:
                self.restore_thread.quit()
                if not self.restore_thread.wait(2000):
                    print("[DEBUG] 恢复线程等待超时，强制终止")
                    self.restore_thread.terminate()
                    self.restore_thread.wait(1000)
            except Exception as e:
                print(f"[DEBUG] 停止恢复线程时出错: {e}")
            finally:
                self.restore_worker = None
                self.restore_thread = None
        
        # 停止下载线程
        if hasattr(self, 'download_worker') and self.download_worker:
            print("[DEBUG] 停止下载线程...")
            try:
                self.download_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止下载线程时出错: {e}")
        
        if hasattr(self, 'download_thread') and self.download_thread and self.download_thread.isRunning():
            print("[DEBUG] 等待下载线程结束...")
            try:
                self.download_thread.quit()
                if not self.download_thread.wait(2000):
                    print("[DEBUG] 下载线程等待超时，强制终止")
                    self.download_thread.terminate()
                    self.download_thread.wait(1000)
            except Exception as e:
                print(f"[DEBUG] 停止下载线程时出错: {e}")
            finally:
                self.download_worker = None
                self.download_thread = None
        
        # 停止单次扫描线程
        if hasattr(self, 'single_scan_worker') and self.single_scan_worker:
            print("[DEBUG] 停止单次扫描线程...")
            try:
                self.single_scan_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止单次扫描线程时出错: {e}")
        
        if hasattr(self, 'single_scan_thread') and self.single_scan_thread and self.single_scan_thread.isRunning():
            print("[DEBUG] 等待单次扫描线程结束...")
            try:
                self.single_scan_thread.quit()
                if not self.single_scan_thread.wait(2000):
                    print("[DEBUG] 单次扫描线程等待超时，强制终止")
                    self.single_scan_thread.terminate()
                    self.single_scan_thread.wait(1000)
            except Exception as e:
                print(f"[DEBUG] 停止单次扫描线程时出错: {e}")
            finally:
                self.single_scan_worker = None
                self.single_scan_thread = None
        
        # 停止MD5计算线程
        if hasattr(self, 'md5_worker') and self.md5_worker:
            print("[DEBUG] 停止MD5计算线程...")
            try:
                self.md5_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止MD5计算线程时出错: {e}")
        
        if hasattr(self, 'md5_thread') and self.md5_thread and self.md5_thread.isRunning():
            print("[DEBUG] 等待MD5线程结束...")
            try:
                self.md5_thread.quit()
                if not self.md5_thread.wait(2000):
                    print("[DEBUG] MD5线程等待超时，强制终止")
                    self.md5_thread.terminate()
                    self.md5_thread.wait(1000)
            except Exception as e:
                print(f"[DEBUG] 停止MD5线程时出错: {e}")
            finally:
                self.md5_worker = None
                self.md5_thread = None
        
        # 停止线程池
        if hasattr(self, 'thread_pool'):
            print("[DEBUG] 关闭线程池...")
            try:
                self.thread_pool.shutdown(wait=False)
            except Exception as e:
                print(f"[DEBUG] 关闭线程池时出错: {e}")
        
        # 停止多目录扫描管理器
        if hasattr(self, 'scan_manager'):
            print("[DEBUG] 停止扫描管理器...")
            try:
                self.scan_manager.stop_all()
            except Exception as e:
                print(f"[DEBUG] 停止扫描管理器时出错: {e}")
        
        # === 新增：停止封面处理线程 ===
        if hasattr(self, 'cover_worker') and self.cover_worker:
            print("[DEBUG] 停止封面处理线程...")
            try:
                self.cover_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止封面处理线程时出错: {e}")
        
        if hasattr(self, 'cover_thread') and self.cover_thread and self.cover_thread.isRunning():
            print("[DEBUG] 等待封面处理线程结束...")
            try:
                self.cover_thread.quit()
                if not self.cover_thread.wait(2000):
                    print("[DEBUG] 封面处理线程等待超时，强制终止")
                    self.cover_thread.terminate()
                    self.cover_thread.wait(1000)
            except Exception as e:
                print(f"[DEBUG] 停止封面处理线程时出错: {e}")
            finally:
                self.cover_worker = None
                self.cover_thread = None
        
        # === 新增：停止数据库保存线程 ===
        if hasattr(self, 'db_save_worker') and self.db_save_worker:
            print("[DEBUG] 停止数据库保存线程...")
            try:
                self.db_save_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止数据库保存线程时出错: {e}")
        
        if hasattr(self, 'db_save_thread') and self.db_save_thread and self.db_save_thread.isRunning():
            print("[DEBUG] 等待数据库保存线程结束...")
            try:
                self.db_save_thread.quit()
                if not self.db_save_thread.wait(2000):
                    print("[DEBUG] 数据库保存线程等待超时，强制终止")
                    self.db_save_thread.terminate()
                    self.db_save_thread.wait(1000)
            except Exception as e:
                print(f"[DEBUG] 停止数据库保存线程时出错: {e}")
            finally:
                self.db_save_worker = None
                self.db_save_thread = None
        
        # === 新增：停止目录扫描线程 ===
        if hasattr(self, 'directory_scan_worker') and self.directory_scan_worker:
            print("[DEBUG] 停止目录扫描线程...")
            try:
                self.directory_scan_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止目录扫描线程时出错: {e}")
        
        if hasattr(self, 'directory_scan_thread') and self.directory_scan_thread and self.directory_scan_thread.isRunning():
            print("[DEBUG] 等待目录扫描线程结束...")
            try:
                self.directory_scan_thread.quit()
                if not self.directory_scan_thread.wait(2000):
                    print("[DEBUG] 目录扫描线程等待超时，强制终止")
                    self.directory_scan_thread.terminate()
                    self.directory_scan_thread.wait(1000)
            except Exception as e:
                print(f"[DEBUG] 停止目录扫描线程时出错: {e}")
            finally:
                self.directory_scan_worker = None
                self.directory_scan_thread = None
        
        # === 新增：停止静态文件下载线程 ===
        if hasattr(self, 'static_download_worker') and self.static_download_worker:
            print("[DEBUG] 停止静态文件下载线程...")
            try:
                self.static_download_worker.stop()
            except Exception as e:
                print(f"[DEBUG] 停止静态文件下载线程时出错: {e}")
        
        if hasattr(self, 'static_download_thread') and self.static_download_thread and self.static_download_thread.isRunning():
            print("[DEBUG] 等待静态文件下载线程结束...")
            try:
                self.static_download_thread.quit()
                if not self.static_download_thread.wait(2000):
                    print("[DEBUG] 静态文件下载线程等待超时，强制终止")
                    self.static_download_thread.terminate()
                    self.static_download_thread.wait(1000)
            except Exception as e:
                print(f"[DEBUG] 停止静态文件下载线程时出错: {e}")
            finally:
                self.static_download_worker = None
                self.static_download_thread = None
        
        print("[DEBUG] 所有线程停止完成")



    def get_current_directories(self):
        """获取当前目录数据"""
        if not hasattr(self, 'table_widget'):
            return []
        
        directories = []
        for row in range(self.table_widget.rowCount()):
            name_item = self.table_widget.item(row, 1)
            path_item = self.table_widget.item(row, 4)
            status_item = self.table_widget.item(row, 3)
            
            if name_item and path_item and status_item:
                directories.append({
                    "name": name_item.text(),
                    "path": path_item.text(),
                    "exists": status_item.text() == "上架",
                    "is_directory": True  # 假设都是目录
                })
        
        return directories

    def batch_process_pdfs_threaded(self, operation_type="generate_covers"):
        """多线程批量处理PDF文件 - 增强验证"""
        if not self.user_manager.current_db_path:
            QMessageBox.warning(self, "未登录", "请先登录用户")
            return
        
        # 获取所有PDF文件
        pdf_files = self.find_all_pdf_files()
        
        # === 新增：过滤无效文件 ===
        valid_pdf_files = []
        invalid_pdf_files = []
        
        for pdf_path in pdf_files:
            if self.is_valid_pdf(pdf_path):
                valid_pdf_files.append(pdf_path)
            else:
                invalid_pdf_files.append(pdf_path)
        
        print(f"[PDF PROCESSING] 找到 {len(pdf_files)} 个PDF文件")
        print(f"[PDF PROCESSING] 有效文件: {len(valid_pdf_files)} 个")
        print(f"[PDF PROCESSING] 无效文件: {len(invalid_pdf_files)} 个")
        
        if not valid_pdf_files:
            QMessageBox.information(self, "提示", "没有找到有效的PDF文件")
            return
        
        # 显示无效文件信息
        if invalid_pdf_files:
            invalid_count = len(invalid_pdf_files)
            invalid_names = [os.path.basename(p) for p in invalid_pdf_files[:5]]  # 只显示前5个
            info_msg = f"跳过了 {invalid_count} 个无效PDF文件"
            if invalid_names:
                info_msg += f"\n\n示例文件:\n" + "\n".join(invalid_names)
                if invalid_count > 5:
                    info_msg += f"\n... 还有 {invalid_count - 5} 个文件"
            
            QMessageBox.information(self, "文件验证结果", info_msg)
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        operation_name = self.get_pdf_operation_name(operation_type)
        self.progress_label.setText(f"准备{operation_name}...")
        QApplication.processEvents()  # 强制刷新界面
        
        # 创建工作线程（只处理有效文件）
        self.pdf_processing_worker = PDFProcessingWorker(self, valid_pdf_files, operation_type)
        self.pdf_processing_thread = QThread()
        
        self.pdf_processing_worker.moveToThread(self.pdf_processing_thread)
        self.pdf_processing_worker.progress_updated.connect(self.on_pdf_processing_progress)
        self.pdf_processing_worker.finished.connect(self.on_pdf_processing_finished)
        self.pdf_processing_worker.error_occurred.connect(self.on_pdf_processing_error)
        self.pdf_processing_worker.pdf_processed.connect(self.on_single_pdf_processed)
        
        self.pdf_processing_thread.started.connect(self.pdf_processing_worker.process_pdfs)
        self.pdf_processing_worker.finished.connect(self.pdf_processing_thread.quit)
        self.pdf_processing_worker.finished.connect(self.pdf_processing_worker.deleteLater)
        self.pdf_processing_thread.finished.connect(self.pdf_processing_thread.deleteLater)
        
        self.pdf_processing_thread.start()


    def get_pdf_operation_name(self, operation_type):
        """获取PDF操作名称"""
        operation_names = {
            "generate_covers": "生成PDF封面",
            "extract_text": "提取PDF文本",
            "analyze_metadata": "分析PDF元数据"
        }
        return operation_names.get(operation_type, "处理PDF文件")

    def on_pdf_processing_progress(self, progress, message):
        """PDF处理进度更新"""
        # 更新主界面进度条
        self.progress_bar.setValue(progress)
        self.progress_label.setText(message)
        
        # === 新增：同时更新PDF工具对话框的进度显示 ===
        self.update_pdf_tools_progress(progress, message)
        
        QApplication.processEvents()  # 强制刷新界面

    def on_pdf_processing_finished(self, success_count, skip_count, error_count):
        """PDF处理完成"""
        self.progress_bar.setValue(100)
        operation_name = self.get_pdf_operation_name(getattr(self.pdf_processing_worker, 'operation_type', 'generate_covers'))
        
        result_msg = f"{operation_name}完成:\n成功: {success_count}\n失败: {error_count}"
        if skip_count > 0:
            result_msg += f"\n跳过: {skip_count}"
        
        self.progress_label.setText(f"{operation_name}完成")
        
        # === 新增：更新PDF工具对话框状态 ===
        status_message = f"{operation_name}已完成 - 成功: {success_count}, 失败: {error_count}"
        self.update_pdf_tools_dialog_status(status_message)
        
        # 3秒后隐藏进度条
        QTimer.singleShot(3000, self.hide_progress_bar)
        
        # 显示完成消息框
        QMessageBox.information(self, "完成", result_msg)
        
        # === 可选：处理完成后自动关闭对话框 ===
        # self.close_pdf_tools_dialog_on_completion()

    def update_pdf_tools_dialog_status(self, status_message):
        """更新PDF工具对话框的状态显示"""
        try:
            # 方法1: 通过查找当前打开的对话框
            for widget in QApplication.topLevelWidgets():
                if (isinstance(widget, QDialog) and 
                    widget.windowTitle() == "PDF工具" and 
                    widget.isVisible()):
                    
                    # 查找对话框中的进度组
                    for i in range(widget.layout().count()):
                        group_box = widget.layout().itemAt(i).widget()
                        if (isinstance(group_box, QGroupBox) and 
                            group_box.title() == "处理进度"):
                            
                            # 更新进度标签
                            for j in range(group_box.layout().count()):
                                label = group_box.layout().itemAt(j).widget()
                                if isinstance(label, QLabel):
                                    label.setText(status_message)
                                    if "完成" in status_message or "成功" in status_message:
                                        label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                                    elif "失败" in status_message or "错误" in status_message:
                                        label.setStyleSheet("color: #F44336; font-weight: bold;")
                                    else:
                                        label.setStyleSheet("color: #007acc; font-weight: bold;")
                                    return True
                    break
                    
            # 方法2: 如果找不到对话框，记录日志
            print(f"[PDF TOOLS] 状态更新: {status_message} (未找到打开的对话框)")
            return False
            
        except Exception as e:
            print(f"[PDF TOOLS ERROR] 更新对话框状态失败: {e}")
            return False


    def on_pdf_processing_error(self, error_message, file_path):
        """PDF处理错误"""
        print(f"[PDF PROCESSING ERROR] {file_path}: {error_message}")
        # 在状态栏显示错误信息
        self.update_status_bar(f"PDF处理错误: {error_message}", 3000)

    def on_single_pdf_processed(self, pdf_path, operation_type, success):
        """单个PDF文件处理完成"""
        status = "成功" if success else "失败"
        print(f"[PDF PROCESS] {operation_type} {status}: {pdf_path}")

    def show_pdf_tools_dialog(self):
        """显示PDF工具对话框 - 添加验证功能"""
        dialog = QDialog(self)
        dialog.setWindowTitle("PDF工具")
        dialog.setMinimumSize(400, 350)  # 增加高度以容纳新按钮
        
        layout = QVBoxLayout()
        
        # PDF操作选择
        operation_group = QGroupBox("PDF操作")
        operation_layout = QVBoxLayout()
        
        self.pdf_operation_combo = QComboBox()
        self.pdf_operation_combo.addItem("生成封面图片", "generate_covers")
        self.pdf_operation_combo.addItem("提取文本内容", "extract_text")
        self.pdf_operation_combo.addItem("分析元数据", "analyze_metadata")
        self.pdf_operation_combo.addItem("验证文件完整性", "validate_files")  # 新增选项
        
        operation_layout.addWidget(QLabel("选择操作:"))
        operation_layout.addWidget(self.pdf_operation_combo)
        operation_group.setLayout(operation_layout)
        layout.addWidget(operation_group)
        
        # 设置选项
        settings_group = QGroupBox("设置")
        settings_layout = QVBoxLayout()
        
        self.pdf_thread_count = QSpinBox()
        self.pdf_thread_count.setMinimum(1)
        self.pdf_thread_count.setMaximum(8)
        self.pdf_thread_count.setValue(4)
        self.pdf_thread_count.setToolTip("同时处理的PDF文件数量")
        
        self.pdf_quality_combo = QComboBox()
        self.pdf_quality_combo.addItem("低质量 (快速)", "0")
        self.pdf_quality_combo.addItem("中等质量", "1")
        self.pdf_quality_combo.addItem("高质量 (较慢)", "2")
        
        settings_layout.addWidget(QLabel("并发线程数:"))
        settings_layout.addWidget(self.pdf_thread_count)
        settings_layout.addWidget(QLabel("生成质量:"))
        settings_layout.addWidget(self.pdf_quality_combo)
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # 统计信息
        stats_group = QGroupBox("统计信息")
        stats_layout = QVBoxLayout()
        
        pdf_count = len(self.find_all_pdf_files())
        stats_layout.addWidget(QLabel(f"找到 {pdf_count} 个PDF文件"))
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # === 新增：进度显示区域 ===
        progress_group = QGroupBox("处理进度")
        progress_layout = QVBoxLayout()
        
        progress_info_label = QLabel("点击'开始处理'后，此处将显示处理进度")
        progress_info_label.setStyleSheet("color: #666; font-size: 12px;")
        progress_layout.addWidget(progress_info_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        # === 修改这里：不关闭对话框，而是在主界面显示进度 ===
        start_btn = QPushButton("开始处理")
        start_btn.clicked.connect(lambda: self.start_pdf_processing_without_close(dialog))
        
        # 新增快速验证按钮
        quick_validate_btn = QPushButton("快速验证")
        quick_validate_btn.clicked.connect(lambda: self.quick_validate_pdfs_without_close(dialog))
        
        cancel_btn = QPushButton("关闭")
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(start_btn)
        button_layout.addWidget(quick_validate_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        dialog.exec()

    # === 新增方法：不关闭对话框开始PDF处理 ===
    def start_pdf_processing_without_close(self, dialog):
        """开始PDF处理但不关闭对话框"""
        operation_type = self.pdf_operation_combo.currentData()
        
        # 在主界面显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        operation_name = self.get_pdf_operation_name(operation_type)
        self.progress_label.setText(f"准备{operation_name}...")

        # === 新增：设置PDF工具对话框的初始状态 ===
        self.update_pdf_tools_dialog_status(f"正在{operation_name}...进度显示在主界面")

        # 更新对话框中的提示信息
        for i in range(dialog.layout().count()):
            widget = dialog.layout().itemAt(i).widget()
            if isinstance(widget, QGroupBox) and widget.title() == "处理进度":
                for j in range(widget.layout().count()):
                    label = widget.layout().itemAt(j).widget()
                    if isinstance(label, QLabel):
                        label.setText(f"正在{operation_name}...进度显示在主界面")
                        label.setStyleSheet("color: #007acc; font-weight: bold;")
                        break
                break
        
        # 开始处理
        self.batch_process_pdfs_threaded(operation_type)

    # === 新增方法：不关闭对话框快速验证PDF ===
    def quick_validate_pdfs_without_close(self, dialog):
        """快速验证PDF但不关闭对话框"""
        # 在主界面显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("准备验证PDF文件...")
        
        # 更新对话框中的提示信息
        for i in range(dialog.layout().count()):
            widget = dialog.layout().itemAt(i).widget()
            if isinstance(widget, QGroupBox) and widget.title() == "处理进度":
                for j in range(widget.layout().count()):
                    label = widget.layout().itemAt(j).widget()
                    if isinstance(label, QLabel):
                        label.setText("正在验证PDF文件...进度显示在主界面")
                        label.setStyleSheet("color: #007acc; font-weight: bold;")
                        break
                break
        
        # 开始验证
        self.validate_pdf_files_threaded()

    def start_pdf_processing(self, dialog):
        """开始PDF处理"""
        operation_type = self.pdf_operation_combo.currentData()
        dialog.accept()
        self.batch_process_pdfs_threaded(operation_type)

    def is_poppler_available(self):
        """检查poppler-utils是否可用"""
        try:
            import subprocess
            result = subprocess.run(['pdftoppm', '-v'], 
                                capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False

    def is_valid_pdf(self, pdf_path):
        """验证PDF文件是否有效"""
        try:
            # 检查文件是否存在
            if not os.path.exists(pdf_path):
                print(f"[PDF VALIDATION] 文件不存在: {pdf_path}")
                return False
                
            # 检查文件大小
            file_size = os.path.getsize(pdf_path)
            if file_size == 0:
                print(f"[PDF VALIDATION] 文件为空: {pdf_path}")
                return False
                
            if file_size < 100:  # PDF文件通常至少几百字节
                print(f"[PDF VALIDATION] 文件过小可能损坏: {pdf_path} ({file_size} bytes)")
                return False
            
            # 检查PDF文件头
            with open(pdf_path, 'rb') as f:
                header = f.read(8)
                if not header.startswith(b'%PDF'):
                    print(f"[PDF VALIDATION] 不是有效的PDF文件: {pdf_path}")
                    return False
            
            # 检查文件扩展名
            if not pdf_path.lower().endswith('.pdf'):
                print(f"[PDF VALIDATION] 不是PDF文件扩展名: {pdf_path}")
                return False
                
            print(f"[PDF VALIDATION] ✓ 文件验证通过: {os.path.basename(pdf_path)}")
            return True
            
        except Exception as e:
            print(f"[PDF VALIDATION ERROR] 验证PDF文件失败 {pdf_path}: {e}")
            return False



    def check_pdf_integrity(self, pdf_path):
        """深度检查PDF文件完整性"""
        try:
            # 使用poppler工具检查PDF完整性
            import subprocess
            
            # 尝试获取PDF信息（不生成图片，只检查结构）
            result = subprocess.run(
                ['pdfinfo', pdf_path],
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                errors='ignore',  # 忽略编码错误
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"[PDF INTEGRITY] ✅ 文件完整性检查通过: {os.path.basename(pdf_path)}")
                return True
            else:
                print(f"[PDF INTEGRITY] ❌ 文件可能损坏: {os.path.basename(pdf_path)}")
                print(f"[PDF INTEGRITY] 错误信息: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print(f"[PDF INTEGRITY] pdfinfo工具不可用，跳过深度检查")
            return self.is_valid_pdf(pdf_path)  # 回退到基础验证
        except Exception as e:
            print(f"[PDF INTEGRITY ERROR] 深度检查失败: {e}")
            return self.is_valid_pdf(pdf_path)  # 回退到基础验证

    def quick_validate_pdfs(self, dialog):
        """快速验证PDF文件"""
        dialog.accept()
        self.validate_pdf_files_threaded()

    def validate_pdf_files_threaded(self):
        """多线程验证PDF文件"""
        pdf_files = self.find_all_pdf_files()
        
        if not pdf_files:
            QMessageBox.information(self, "提示", "没有找到PDF文件")
            return
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("准备验证PDF文件...")
        
        # 创建工作线程
        self.pdf_validation_worker = PDFValidationWorker(pdf_files)
        self.pdf_validation_thread = QThread()
        
        self.pdf_validation_worker.moveToThread(self.pdf_validation_thread)
        self.pdf_validation_worker.progress_updated.connect(self.on_pdf_validation_progress)
        self.pdf_validation_worker.validation_finished.connect(self.on_pdf_validation_finished)
        self.pdf_validation_worker.file_validated.connect(self.on_single_pdf_validated)
        
        self.pdf_validation_thread.started.connect(self.pdf_validation_worker.validate_pdfs)
        self.pdf_validation_worker.finished.connect(self.pdf_validation_thread.quit)
        self.pdf_validation_worker.finished.connect(self.pdf_validation_worker.deleteLater)
        self.pdf_validation_thread.finished.connect(self.pdf_validation_thread.deleteLater)
        
        self.pdf_validation_thread.start()

    def on_pdf_validation_progress(self, progress, message):
        """PDF验证进度更新"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(message)
        
        # === 新增：同时更新PDF工具对话框的进度显示 ===
        self.update_pdf_tools_progress(progress, message)

    def on_pdf_validation_finished(self, validation_results):
        """PDF验证完成"""
        self.progress_bar.setValue(100)
        self.progress_label.setText("PDF验证完成")
        
        # 统计结果
        total_files = len(validation_results)
        valid_files = sum(1 for result in validation_results.values() if result['valid'])
        invalid_files = total_files - valid_files
        
        # === 新增：更新PDF工具对话框状态 ===
        status_message = f"PDF验证完成 - 有效: {valid_files}, 无效: {invalid_files}"
        self.update_pdf_tools_dialog_status(status_message)
        
        # 显示结果
        result_msg = f"PDF验证完成:\n总文件数: {total_files}\n有效文件: {valid_files}\n无效文件: {invalid_files}"
        
        if invalid_files > 0:
            invalid_list = []
            for pdf_path, result in validation_results.items():
                if not result['valid']:
                    invalid_list.append(f"{os.path.basename(pdf_path)}: {result['message']}")
            
            if invalid_list:
                result_msg += f"\n\n无效文件详情:\n" + "\n".join(invalid_list[:10])  # 只显示前10个
                if len(invalid_list) > 10:
                    result_msg += f"\n... 还有 {len(invalid_list) - 10} 个无效文件"
        
        QMessageBox.information(self, "PDF验证结果", result_msg)
        
        # 3秒后隐藏进度条
        QTimer.singleShot(3000, self.hide_progress_bar)

    def on_single_pdf_validated(self, pdf_path, is_valid, message):
        """单个PDF文件验证完成"""
        status_icon = "✓" if is_valid else "❌"
        print(f"[PDF VALIDATION] {status_icon} {os.path.basename(pdf_path)}: {message}")

    def get_pdf_tools_dialog(self):
        """获取当前打开的PDF工具对话框"""
        for widget in QApplication.topLevelWidgets():
            if (isinstance(widget, QDialog) and 
                widget.windowTitle() == "PDF工具" and 
                widget.isVisible()):
                return widget
        return None

    def update_pdf_tools_progress(self, progress, message):
        """更新PDF工具对话框的进度显示"""
        dialog = self.get_pdf_tools_dialog()
        if not dialog:
            return False
        
        try:
            # 查找进度组
            for i in range(dialog.layout().count()):
                group_box = dialog.layout().itemAt(i).widget()
                if (isinstance(group_box, QGroupBox) and 
                    group_box.title() == "处理进度"):
                    
                    # 更新进度标签
                    for j in range(group_box.layout().count()):
                        label = group_box.layout().itemAt(j).widget()
                        if isinstance(label, QLabel):
                            full_message = f"{message} (进度: {progress}%)"
                            label.setText(full_message)
                            
                            # 根据进度设置颜色
                            if progress == 100:
                                label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                            elif progress >= 70:
                                label.setStyleSheet("color: #2196F3; font-weight: bold;")
                            elif progress >= 30:
                                label.setStyleSheet("color: #FF9800; font-weight: bold;")
                            else:
                                label.setStyleSheet("color: #007acc; font-weight: bold;")
                            return True
            return False
            
        except Exception as e:
            print(f"[PDF TOOLS ERROR] 更新进度失败: {e}")
            return False

    def close_pdf_tools_dialog_on_completion(self):
        """处理完成后自动关闭PDF工具对话框"""
        QTimer.singleShot(2000, self.auto_close_pdf_tools_dialog)  # 2秒后关闭

    def auto_close_pdf_tools_dialog(self):
        """自动关闭PDF工具对话框"""
        dialog = self.get_pdf_tools_dialog()
        if dialog:
            dialog.accept()
            print("[PDF TOOLS] 处理完成，对话框已自动关闭")

    def clear_search(self):
        """清除搜索内容并重置显示"""
        self.search_input.clear()  # 清空搜索输入框
        self.filter_directories()  # 重新加载所有目录（相当于重置显示）
        self.update_status_bar("搜索内容已清除", 2000)  # 在状态栏显示提示信息

    def load_thumbnail_simple(self, row, path, is_directory):
        """简化的缩略图加载方法"""
        try:
            if is_directory == 1:
                # 查找目录中的前几张图片
                image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
                images = []
                
                try:
                    for file in os.listdir(path):
                        if any(file.lower().endswith(ext) for ext in image_extensions):
                            images.append(os.path.join(path, file))
                            if len(images) >= 4:  # 只取前4张
                                break
                except:
                    pass
                
                # 创建容器
                container = QWidget()
                layout = QHBoxLayout()
                layout.setContentsMargins(2, 2, 2, 2)
                layout.setSpacing(2)
                container.setLayout(layout)
                
                if images:
                    for img_path in images[:4]:
                        thumb_label = QLabel()
                        thumb_label.setFixedSize(60, 45)
                        thumb_label.setAlignment(Qt.AlignCenter)
                        thumb_label.setCursor(Qt.PointingHandCursor)
                        thumb_label.setStyleSheet("border: 1px solid #ddd;")
                        
                        # 设置预览图片
                        pixmap = QPixmap(img_path)
                        if not pixmap.isNull():
                            scaled_pixmap = pixmap.scaled(60, 45, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            thumb_label.setPixmap(scaled_pixmap)
                            thumb_label.mousePressEvent = self.create_thumbnail_click_handler(img_path)
                        else:
                            thumb_label.setText("❌")
                        
                        layout.addWidget(thumb_label)
                else:
                    # 没有图片
                    no_image_label = QLabel("📁")
                    no_image_label.setAlignment(Qt.AlignCenter)
                    no_image_label.setFixedSize(60, 45)
                    no_image_label.setStyleSheet("font-size: 20px; color: #999;")
                    layout.addWidget(no_image_label)
                
                self.table_widget.setCellWidget(row, 2, container)
            else:
                # 文件类型
                file_label = QLabel("📄")
                file_label.setAlignment(Qt.AlignCenter)
                file_label.setFixedSize(280, 120)
                file_label.setStyleSheet("font-size: 48px; color: #999;")
                self.table_widget.setCellWidget(row, 2, file_label)
                
        except Exception as e:
            print(f"[THUMBNAIL SIMPLE ERROR] 加载缩略图失败: {e}")

    def create_file_list_widget(self, directory_path, display_mode):
        """创建文件列表组件，显示其他文件（图片、视频等）"""
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)
        container.setLayout(layout)
        
        if not os.path.isdir(directory_path):
            no_file_label = QLabel("📁 目录不存在")
            no_file_label.setStyleSheet("color: #999; font-size: 11px;")
            layout.addWidget(no_file_label)
            return container
        
        try:
            # 获取所有文件
            all_files = []
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                if os.path.isfile(item_path):
                    all_files.append(item)
            
            # 根据显示模式筛选文件
            image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.ico']
            video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg']
            document_extensions = ['.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
                                '.epub', '.mobi', '.azw', '.rtf', '.odt', '.ods', '.odp']
            
            display_files = []
            
            if display_mode == 'images':
                display_files = [f for f in all_files if any(f.lower().endswith(ext) for ext in image_extensions)]
            elif display_mode == 'videos':
                display_files = [f for f in all_files if any(f.lower().endswith(ext) for ext in video_extensions)]
            elif display_mode == 'documents':
                display_files = [f for f in all_files if any(f.lower().endswith(ext) for ext in document_extensions)]
            elif display_mode == 'none':
                display_files = []
            else:  # 'all' - 显示所有非图片文件（因为图片已经在缩略图列显示了）
                # 排除图片文件，显示其他所有文件
                display_files = [f for f in all_files if not any(f.lower().endswith(ext) for ext in image_extensions)]
            
            if not display_files:
                no_file_label = QLabel("📭 无文件")
                no_file_label.setStyleSheet("color: #999; font-size: 11px;")
                layout.addWidget(no_file_label)
                return container
            
            # 限制显示数量，避免界面过于拥挤
            max_display = 8
            display_files = display_files[:max_display]
            
            # 创建可滚动的文件列表
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setFixedHeight(120)
            scroll_area.setStyleSheet("""
                QScrollArea {
                    border: 1px solid #dee2e6;
                    border-radius: 3px;
                    background-color: #f8f9fa;
                }
            """)
            
            files_container = QWidget()
            files_layout = QVBoxLayout()
            files_layout.setContentsMargins(4, 4, 4, 4)
            files_layout.setSpacing(2)
            
            for file_name in display_files:
                file_path = os.path.join(directory_path, file_name)
                file_widget = self.create_file_item_widget(file_name, file_path)
                files_layout.addWidget(file_widget)
            
            files_container.setLayout(files_layout)
            scroll_area.setWidget(files_container)
            layout.addWidget(scroll_area)
            
            # 如果还有更多文件，显示数量提示
            remaining_count = len([f for f in all_files if f not in display_files])
            if remaining_count > 0:
                more_label = QLabel(f"... 还有 {remaining_count} 个文件")
                more_label.setStyleSheet("color: #666; font-size: 10px;")
                layout.addWidget(more_label)
            
        except PermissionError:
            no_access_label = QLabel("🔒 无访问权限")
            no_access_label.setStyleSheet("color: #dc3545; font-size: 11px;")
            layout.addWidget(no_access_label)
        except Exception as e:
            error_label = QLabel(f"❌ 加载失败")
            error_label.setStyleSheet("color: #dc3545; font-size: 11px;")
            layout.addWidget(error_label)
            print(f"[FILE LIST ERROR] {directory_path}: {e}")
        
        return container

    def create_file_item_widget(self, file_name, file_path):
        """创建单个文件项组件 - 修复路径编码"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # 根据文件类型显示图标
        ext = os.path.splitext(file_name)[1].lower()
        icon_map = {
            '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬', '.mov': '🎬', '.wmv': '🎬', '.flv': '🎬', '.webm': '🎬', '.m4v': '🎬', '.mpg': '🎬', '.mpeg': '🎬',
            '.pdf': '📄', '.doc': '📝', '.docx': '📝', '.txt': '📃',
            '.xls': '📊', '.xlsx': '📊', '.ppt': '📽️', '.pptx': '📽️',
            '.zip': '📦', '.rar': '📦', '.7z': '📦',
            '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵',
            '.exe': '⚙️', '.msi': '⚙️',
            '.epub': '📚', '.mobi': '📚', '.azw': '📚',
            '.html': '🌐', '.htm': '🌐', '.css': '🎨', '.js': '📜',
            '.json': '🔧', '.xml': '🔧', '.ini': '⚙️'
        }
        icon = icon_map.get(ext, '📄')
        
        # 文件图标
        icon_label = QLabel(icon)
        icon_label.setFixedSize(20, 20)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setToolTip(f"文件类型: {ext.upper() if ext else '未知'}")
        
        # 文件名（可点击）- 修复路径编码
        name_label = QLabel(file_name)
        name_label.setStyleSheet("""
            QLabel {
                color: #0066cc;
                font-size: 11px;
                text-decoration: underline;
            }
            QLabel:hover {
                color: #004499;
            }
        """)
        name_label.setCursor(Qt.PointingHandCursor)
        name_label.setToolTip(f"点击打开: {file_path}")
        name_label.setWordWrap(True)
        
        # 修复：确保文件路径使用正确的编码和格式
        def on_click(event):
            if event.button() == Qt.LeftButton:
                # 使用当前的全局打开方法，它会正确处理路径
                self.open_file_direct(file_path)
        
        name_label.mousePressEvent = on_click
        
        layout.addWidget(icon_label)
        layout.addWidget(name_label, 1)
        
        widget.setLayout(layout)
        return widget

    def open_file_direct(self, file_path):
        """直接打开文件 - 修复SMB网络路径问题"""
        try:
            # 首先规范化路径
            normalized_path = self.normalize_path_for_os(file_path)
            
            # 检查是否为SMB网络路径
            is_smb_path = normalized_path.startswith('\\\\') or normalized_path.startswith('//')
            
            if is_smb_path:
                print(f"[DEBUG] 检测到SMB网络路径: {normalized_path}")
                # 使用Windows网络路径格式打开
                success = self.open_smb_file(normalized_path)
                if success:
                    self.update_status_bar(f"已打开文件: {os.path.basename(file_path)}", 3000)
                    return True
                else:
                    raise Exception("无法打开SMB网络文件")
            
            # 本地文件处理
            if sys.platform == "win32":
                # Windows - 使用正确的路径格式
                windows_path = normalized_path.replace('/', '\\')
                # 确保路径存在
                if not os.path.exists(windows_path):
                    raise FileNotFoundError(f"文件不存在: {windows_path}")
                os.startfile(windows_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", normalized_path], check=True)
            else:
                subprocess.run(["xdg-open", normalized_path], check=True)
            
            self.update_status_bar(f"已打开文件: {os.path.basename(file_path)}", 3000)
            return True
            
        except FileNotFoundError as e:
            self.update_status_bar(f"文件不存在: {e}", 5000)
            print(f"[OPEN FILE ERROR] 文件不存在: {file_path}")
            QMessageBox.warning(self, "文件不存在", f"无法找到文件:\n{file_path}")
            return False
        except Exception as e:
            self.update_status_bar(f"打开文件失败: {e}", 5000)
            print(f"[OPEN FILE ERROR] 无法打开文件 {file_path}: {e}")
            QMessageBox.critical(self, "打开失败", f"无法打开文件:\n{file_path}\n错误: {e}")
            return False

    def open_smb_file(self, smb_path):
        """专门处理SMB网络路径的文件打开 - 增强版本"""
        try:
            if sys.platform != "win32":
                print(f"[SMB WARNING] SMB路径仅在Windows上完全支持: {smb_path}")
                return False
            
            # 规范化SMB路径
            # 确保使用正确的Windows网络路径格式: \\server\share\file
            normalized = smb_path.replace('/', '\\')
            
            # 确保以双反斜杠开头
            if normalized.startswith('\\\\'):
                pass  # 已经正确
            elif normalized.startswith('//'):
                normalized = '\\\\' + normalized[2:]
            elif normalized.startswith('\\'):
                normalized = '\\\\' + normalized[1:]
            else:
                # 普通路径，直接处理
                return self.open_local_file(smb_path)
            
            print(f"[SMB DEBUG] 规范化后的SMB路径: {normalized}")
            
            # 检查文件是否存在
            if not os.path.exists(normalized):
                print(f"[SMB ERROR] 文件不存在: {normalized}")
                return False
            
            # 方案1: 直接使用os.startfile
            try:
                os.startfile(normalized)
                print(f"[SMB SUCCESS] 使用os.startfile打开: {normalized}")
                return True
            except Exception as e1:
                print(f"[SMB] os.startfile失败: {e1}")
            
            # 方案2: 使用subprocess.Popen
            try:
                import subprocess
                subprocess.Popen(['explorer', normalized], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
                print(f"[SMB SUCCESS] 使用explorer打开: {normalized}")
                return True
            except Exception as e2:
                print(f"[SMB] explorer打开失败: {e2}")
            
            # 方案3: 使用start命令
            try:
                import subprocess
                subprocess.Popen(f'start "" "{normalized}"', shell=True,
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
                print(f"[SMB SUCCESS] 使用start命令打开: {normalized}")
                return True
            except Exception as e3:
                print(f"[SMB] start命令失败: {e3}")
            
            # 方案4: 尝试映射网络驱动器的方式
            return self.open_smb_with_mapping(normalized)
            
        except Exception as e:
            print(f"[SMB ERROR] 打开SMB文件失败: {e}")
            return False

    def open_smb_with_mapping(self, smb_path):
        """尝试通过映射网络驱动器的方式打开SMB文件"""
        try:
            import subprocess
            import re
            
            # 提取服务器和共享名
            # 格式: \\server\share\path\to\file
            parts = smb_path.lstrip('\\').split('\\')
            if len(parts) < 2:
                return False
            
            server = parts[0]
            share = parts[1]
            file_relative = '\\'.join(parts[2:]) if len(parts) > 2 else ''
            
            # 查找可用的驱动器号
            drive_letter = self.find_available_drive_letter()
            if not drive_letter:
                return False
            
            # 映射网络驱动器
            map_cmd = f'net use {drive_letter}: "\\\\{server}\\{share}" /persistent:no'
            result = subprocess.run(map_cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # 构建映射后的路径
                mapped_path = f"{drive_letter}:\\{file_relative}" if file_relative else f"{drive_letter}:\\"
                
                # 打开文件
                if os.path.exists(mapped_path):
                    os.startfile(mapped_path)
                    
                    # 延迟断开映射
                    def disconnect_mapping():
                        QTimer.singleShot(5000, lambda: subprocess.run(f'net use {drive_letter}: /delete', shell=True))
                    
                    disconnect_mapping()
                    return True
            
            return False
            
        except Exception as e:
            print(f"[SMB MAPPING ERROR] {e}")
            return False

    def open_local_file(self, file_path):
        """打开本地文件"""
        try:
            if sys.platform == "win32":
                # 确保使用正确的Windows路径格式
                windows_path = file_path.replace('/', '\\')
                if not os.path.exists(windows_path):
                    return False
                os.startfile(windows_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", file_path], check=True)
            else:
                subprocess.run(["xdg-open", file_path], check=True)
            return True
        except Exception as e:
            print(f"[LOCAL FILE ERROR] {e}")
            return False



    def apply_path_filter(self):
        """应用路径过滤"""
        filter_value = self.path_filter_input.text().strip()
        self.current_path_filter = filter_value
        
        if filter_value:
            self.update_status_bar(f"应用路径过滤: {filter_value}")
            self.path_filter_input.setStyleSheet("border: 1px solid #6c5ce7; background-color: #f3f0ff;")
            self.show_filter_badge(filter_value)
        else:
            self.clear_path_filter()
            return
        
        # 重新加载过滤后的数据
        self.filter_directories()

    def clear_path_filter(self):
        """清除路径过滤"""
        self.current_path_filter = ""
        self.path_filter_input.clear()
        self.path_filter_input.setStyleSheet("")
        self.hide_filter_badge()
        self.update_status_bar("已清除路径过滤")
        
        # 清除搜索框内容并重新加载
        self.search_input.clear()
        self.filter_directories()

    def show_filter_badge(self, filter_value):
        """显示过滤徽章"""
        short_filter = filter_value[:30] + "..." if len(filter_value) > 30 else filter_value
        self.filter_status_label.setText(f"🔍 当前过滤: {short_filter}")
        self.filter_status_label.setVisible(True)

    def hide_filter_badge(self):
        """隐藏过滤徽章"""
        self.filter_status_label.setVisible(False)

    def show_path_filter_dialog(self):
        """显示目录选择器对话框"""
        if not self.user_manager.current_db_path:
            QMessageBox.warning(self, "未登录", "请先登录用户")
            return
        
        try:
            # 从数据库获取所有目录路径
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT path FROM directories WHERE is_directory = 1 ORDER BY path")
            all_paths = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if not all_paths:
                QMessageBox.information(self, "提示", "没有可用的目录数据")
                return
            
            # 构建目录树
            path_tree = self.build_path_tree(all_paths)
            
            # 创建选择对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("选择要显示的目录")
            dialog.setMinimumSize(500, 400)
            
            layout = QVBoxLayout()
            
            # 说明标签
            info_label = QLabel("选择要显示的目录（可多选），点击确定后将只显示这些目录及其子目录")
            info_label.setWordWrap(True)
            info_label.setStyleSheet("color: #666; padding: 5px;")
            layout.addWidget(info_label)
            
            # 目录树区域
            tree_widget = QTreeWidget()
            tree_widget.setHeaderLabel("目录结构")
            tree_widget.setSelectionMode(QTreeWidget.MultiSelection)
            
            self.populate_tree_widget(tree_widget, path_tree)
            
            layout.addWidget(tree_widget)
            
            # 快捷操作栏
            quick_layout = QHBoxLayout()
            
            select_all_btn = QPushButton("全选")
            select_all_btn.clicked.connect(lambda: self.select_all_tree_items(tree_widget, True))
            
            clear_all_btn = QPushButton("全不选")
            clear_all_btn.clicked.connect(lambda: self.select_all_tree_items(tree_widget, False))
            
            select_parents_btn = QPushButton("选择父级目录")
            select_parents_btn.clicked.connect(lambda: self.select_parent_directories(tree_widget))
            
            expand_all_btn = QPushButton("展开全部")
            expand_all_btn.clicked.connect(lambda: tree_widget.expandAll())
            
            collapse_all_btn = QPushButton("折叠全部")
            collapse_all_btn.clicked.connect(lambda: tree_widget.collapseAll())
            
            quick_layout.addWidget(select_all_btn)
            quick_layout.addWidget(clear_all_btn)
            quick_layout.addWidget(select_parents_btn)
            quick_layout.addWidget(expand_all_btn)
            quick_layout.addWidget(collapse_all_btn)
            
            layout.addLayout(quick_layout)
            
            # 按钮区域
            btn_layout = QHBoxLayout()
            
            apply_btn = QPushButton("确定")
            apply_btn.setStyleSheet("background-color: #6c5ce7; color: white; padding: 8px 20px;")
            apply_btn.clicked.connect(lambda: self.apply_tree_selection(dialog, tree_widget))
            
            cancel_btn = QPushButton("取消")
            cancel_btn.clicked.connect(dialog.reject)
            
            btn_layout.addStretch()
            btn_layout.addWidget(apply_btn)
            btn_layout.addWidget(cancel_btn)
            
            layout.addLayout(btn_layout)
            
            dialog.setLayout(layout)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载目录树失败:\n{e}")

    def build_path_tree(self, paths):
        """构建路径树形结构"""
        tree = []
        
        for path in paths:
            # 统一分隔符为正斜杠
            normalized_path = path.replace('\\', '/')
            parts = normalized_path.split('/')
            
            current_level = tree
            
            for i, part in enumerate(parts):
                if not part:
                    continue
                
                # 构建完整路径
                full_path = '/'.join(parts[:i+1])
                
                # 查找是否已存在
                existing = None
                for node in current_level:
                    if node.get('name') == part:
                        existing = node
                        break
                
                if existing:
                    if 'children' not in existing:
                        existing['children'] = []
                    current_level = existing['children']
                else:
                    new_node = {
                        'name': part,
                        'full_path': full_path,
                        'children': []
                    }
                    current_level.append(new_node)
                    current_level = new_node['children']
        
        return tree

    def populate_tree_widget(self, tree_widget, tree_nodes, parent=None):
        """填充树形控件"""
        if parent is None:
            tree_widget.clear()
        
        for node in tree_nodes:
            item = QTreeWidgetItem(parent if parent else tree_widget)
            item.setText(0, node['name'])
            item.setData(0, Qt.UserRole, node['full_path'])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Unchecked)
            
            if node.get('children'):
                self.populate_tree_widget(tree_widget, node['children'], item)

    def select_all_tree_items(self, tree_widget, select):
        """全选/全不选树形控件项"""
        def set_check_state(item, state):
            item.setCheckState(0, Qt.Checked if state else Qt.Unchecked)
            for i in range(item.childCount()):
                set_check_state(item.child(i), state)
        
        for i in range(tree_widget.topLevelItemCount()):
            set_check_state(tree_widget.topLevelItem(i), select)

    def select_parent_directories(self, tree_widget):
        """只选择父级目录（顶层目录）"""
        self.select_all_tree_items(tree_widget, False)
        for i in range(tree_widget.topLevelItemCount()):
            tree_widget.topLevelItem(i).setCheckState(0, Qt.Checked)

    def apply_tree_selection(self, dialog, tree_widget):
        """应用树形选择"""
        selected_paths = []
        
        def collect_selected(item):
            if item.checkState(0) == Qt.Checked:
                path = item.data(0, Qt.UserRole)
                if path:
                    selected_paths.append(path)
            for i in range(item.childCount()):
                collect_selected(item.child(i))
        
        for i in range(tree_widget.topLevelItemCount()):
            collect_selected(tree_widget.topLevelItem(i))
        
        if selected_paths:
            # 用 | 分隔多个路径
            filter_value = '|'.join(selected_paths)
            self.path_filter_input.setText(filter_value)
            self.apply_path_filter()
        
        dialog.accept()

    def get_path_filter_condition(self):
        """获取路径过滤的SQL条件"""
        if not hasattr(self, 'current_path_filter') or not self.current_path_filter:
            return None, []
        
        filter_paths = [p.strip() for p in self.current_path_filter.split('|') if p.strip()]
        if not filter_paths:
            return None, []
        
        conditions = []
        params = []
        
        for fp in filter_paths:
            # 规范化路径用于匹配
            normalized_fp = fp.replace('\\', '/').lower()
            # 匹配以该路径开头或包含该路径的情况
            conditions.append("LOWER(path) LIKE ?")
            params.append(f"%{normalized_fp}%")
        
        return " OR ".join(conditions), params



    def update_table_with_data(self, rows):
        """用数据更新表格（优化版：延迟加载封面/缩略图/文件列表）"""
        self._ensure_table_exists()
        
        total_rows = len(rows)
        if total_rows == 0:
            self.table_widget.setRowCount(0)
            self._is_loading = False
            self.statusBar().showMessage("没有匹配的目录")
            return
        
        # 获取文件显示模式设置
        file_display_mode = self.get_setting('file_display_mode', 'all')
        
        # 清除旧的延迟加载定时器
        if hasattr(self, '_thumbnail_timers'):
            for timer in self._thumbnail_timers:
                if timer.isActive():
                    timer.stop()
        self._thumbnail_timers = []
        
        # 清空表格并设置行数
        self.table_widget.setRowCount(total_rows)
        
        # 禁用更新以提升批量填充性能
        self.table_widget.setUpdatesEnabled(False)
        
        # 初始化延迟加载信息
        self._thumbnail_load_info = {}
        self._is_loading = True
        
        # ===== 流式分批填充（与 load_directories 一致） =====
        stream_batch = 200
        tw = self.table_widget
        thumb_info = self._thumbnail_load_info
        
        # 局部变量缓存
        bg_green = self._BRUSH_GREEN
        bg_red = self._BRUSH_RED
        bg_white = self._BRUSH_WHITE
        bg_blue = self._BRUSH_BLUE
        # 【性能优化】表格级共用 QSS 只设一次（循环外），循环内用 setObjectName 区分
        self._apply_table_qss()
        align_center = Qt.AlignCenter
        pointing_hand = Qt.PointingHandCursor
        item_not_editable = ~Qt.ItemIsEditable
        
        for batch_start in range(0, total_rows, stream_batch):
            batch_end = min(batch_start + stream_batch, total_rows)
            
            for row_idx in range(batch_start, batch_end):
                name, path, exists, _ct, _lm, is_directory = rows[row_idx]
                
                tw.setRowHeight(row_idx, 150)
                
                cw = QLabel("📁" if is_directory == 1 else "📄")
                cw.setFixedSize(180, 120)
                cw.setAlignment(align_center)
                cw.setCursor(pointing_hand)
                # 【性能优化】改表格级共用 QSS，循环内只设 objectName（等价样式）
                cw.setObjectName("coverPlaceholder")
                tw.setCellWidget(row_idx, 0, cw)
                
                ni = QTableWidgetItem(name)
                ni.setFlags(ni.flags() & item_not_editable)
                tw.setItem(row_idx, 1, ni)
                
                tw_ph = QLabel("📷 加载中...")
                tw_ph.setFixedSize(280, 120)
                tw_ph.setAlignment(align_center)
                tw_ph.setObjectName("thumbPlaceholder")
                tw.setCellWidget(row_idx, 2, tw_ph)
                
                si = QTableWidgetItem("上架" if exists else "下架")
                si.setFlags(si.flags() & item_not_editable)
                if exists:
                    si.setBackground(bg_green)
                    si.setForeground(bg_white)
                else:
                    si.setBackground(bg_red)
                    si.setForeground(bg_white)
                tw.setItem(row_idx, 3, si)
                
                pi = QTableWidgetItem(path)
                pi.setFlags(pi.flags() & item_not_editable)
                pi.setForeground(bg_blue)
                tw.setItem(row_idx, 4, pi)
                
                fp = QLabel("📂 加载中...")
                fp.setAlignment(align_center)
                fp.setObjectName("filePlaceholder")
                fp.setCursor(pointing_hand)
                tw.setCellWidget(row_idx, 5, fp)
                
                thumb_info[row_idx] = {
                    'path': path, 'is_directory': is_directory,
                    'file_display_mode': file_display_mode,
                    'loaded_cover': False, 'loaded_thumbnails': False, 'loaded_files': False
                }
            
            # 每5批刷新UI
            if (batch_start // stream_batch) % 5 == 0:
                self.progress_bar.setValue(10 + int((batch_end / total_rows) * 82))
                self.progress_label.setText(f"过滤加载中... {batch_end}/{total_rows}")
                QApplication.processEvents()
        
        # 重新启用表格更新
        self.table_widget.setUpdatesEnabled(True)
        
        # 设置表格属性（cellClicked 已在 _stream_load_finished 中连接，不重复连接）
        
        # 设置表格属性
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.setAlternatingRowColors(True)
        
        if total_rows < 5000:
            self.table_widget.setSortingEnabled(True)
        
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        
        # 批量启动延迟加载（封面/缩略图/文件列表）
        self.start_thumbnail_loading()
        
        self._is_loading = False
        self.statusBar().showMessage(f"显示 {total_rows} 个目录")

    def load_thumbnails_async(self):
        """异步加载缩略图 - 优先使用多线程并行分块加载"""
        if not hasattr(self, 'table_widget'):
            return
        
        # 如果有 _thumbnail_load_info，使用新的并行加载方式
        if hasattr(self, '_thumbnail_load_info') and self._thumbnail_load_info:
            print(f"[LOAD] 使用多线程并行异步加载")
            self.start_thumbnail_loading()
            return
        
        # 回退到旧的逐行加载方式
        for row in range(self.table_widget.rowCount()):
            path_item = self.table_widget.item(row, 4)
            if path_item:
                path = path_item.text()
                status_item = self.table_widget.item(row, 3)
                is_directory = status_item and status_item.text() == "上架"
                QTimer.singleShot(row * 50, lambda r=row, p=path, d=is_directory: self.load_thumbnail_for_row(r, p, d))


    def toggle_view_mode(self):
        """在列表视图和网格视图之间切换"""
        current_mode = getattr(self, '_view_mode', 'list')
        
        if current_mode == 'list':
            self.switch_to_grid_view()
        else:
            self.switch_to_list_view()

    def switch_to_grid_view(self):
        """切换到网格视图"""
        # 1. 隐藏表格
        if hasattr(self, 'table_widget') and self.table_widget:
            self.table_widget.hide()
        
        # 2. 创建或重新创建滚动区域
        if not hasattr(self, 'scroll_area') or self.scroll_area is None or not self.is_widget_valid(self.scroll_area):
            # 清理旧的滚动区域引用
            if hasattr(self, 'scroll_area'):
                self.scroll_area = None
            
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            
            # 获取主布局并添加滚动区域
            main_layout = self.centralWidget().layout()
            if main_layout:
                main_layout.addWidget(self.scroll_area)
        
        # 3. 创建网格容器
        if hasattr(self, 'grid_container') and self.grid_container:
            self.grid_container.deleteLater()
        
        self.grid_container = QWidget()
        self.grid_layout = FlowLayout(self.grid_container, margin=10, spacing=15)
        self.grid_container.setLayout(self.grid_layout)
        
        # 4. 设置滚动区域内容
        if self.is_widget_valid(self.scroll_area):
            self.scroll_area.setWidget(self.grid_container)
            self.scroll_area.show()
        
        # 5. 填充网格内容
        self.refresh_grid_display()
        
        # 6. 更新状态
        self._view_mode = 'grid'
        self.view_action.setText("📋切换到列表视图")

    def switch_to_list_view(self):
        """切换回列表视图"""
        # 1. 重新显示表格
        if hasattr(self, 'table_widget') and self.table_widget:
            self.table_widget.show()
        
        # 2. 隐藏滚动区域
        if hasattr(self, 'scroll_area') and self.is_widget_valid(self.scroll_area):
            self.scroll_area.hide()
        
        # 3. 确保表格存在且有正确的列布局
        if not hasattr(self, 'table_widget') or not self.table_widget:
            self.table_widget = QTableWidget()
            main_layout = self.centralWidget().layout()
            if main_layout:
                main_layout.addWidget(self.table_widget)
        
        # 4. 恢复6列布局
        self.table_widget.setColumnCount(6)
        self.table_widget.setHorizontalHeaderLabels(["封面", "目录名称", "其他缩略图", "状态", "目录地址", "文件列表"])
        self.table_widget.horizontalHeader().setVisible(True)
        self.table_widget.setColumnWidth(0, 200)
        self.table_widget.setColumnWidth(1, 200)
        self.table_widget.setColumnWidth(2, 300)
        self.table_widget.setColumnWidth(3, 80)
        self.table_widget.setColumnWidth(4, 250)
        self.table_widget.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        
        # 5. 重新加载数据为默认列表样式
        self.load_directories()
        self.filter_directories()
        
        # 6. 更新状态
        self._view_mode = 'list'
        self.view_action.setText("📋切换到网格视图")

    def refresh_grid_display(self):
        """刷新网格视图显示"""
        if not hasattr(self, 'grid_layout') or not self.user_manager.current_db_path:
            return
        
        # 清空现有网格
        self.clear_grid_layout()
        
        # 获取数据
        directories = self.get_all_directories_from_db()
        
        if not directories:
            # 显示空状态
            empty_label = QLabel("📭 没有找到匹配的目录")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #999; font-size: 16px; padding: 40px;")
            self.grid_layout.addWidget(empty_label)
            return
        
        # 应用过滤条件
        filtered_dirs = self.apply_filters_to_directories(directories)
        
        # 创建卡片
        for dir_info in filtered_dirs:
            card_widget = self.create_grid_card(dir_info)
            self.grid_layout.addWidget(card_widget)

    def clear_grid_layout(self):
        """清空网格布局"""
        if hasattr(self, 'grid_layout') and self.grid_layout:
            while self.grid_layout.count():
                item = self.grid_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

    def apply_filters_to_directories(self, directories):
        """应用过滤条件到目录列表"""
        search_text = self.search_input.text().lower().strip() if hasattr(self, 'search_input') else ""
        
        filtered = []
        for dir_info in directories:
            name = dir_info.get("name", "").lower()
            path = dir_info.get("path", "").lower()
            
            # 搜索过滤
            if search_text:
                if (search_text not in name and 
                    search_text not in path and
                    not PinyinSearchHelper.contains_pinyin_initials(name, search_text)):
                    continue
            
            # 路径过滤
            if self.current_path_filter:
                if not self.is_path_matching_filter(path, self.current_path_filter):
                    continue
            
            filtered.append(dir_info)
        
        return filtered

    def is_path_matching_filter(self, path, path_filter):
        """检查路径是否匹配过滤条件"""
        filter_paths = [p.strip().lower() for p in path_filter.split('|') if p.strip()]
        path_lower = path.lower()
        return any(fp in path_lower for fp in filter_paths)
    
    def create_grid_card(self, dir_info):
        """创建网格卡片 - 类似Web客户端的样式"""
        name = dir_info.get("name", "")
        path = dir_info.get("path", "")
        exists = dir_info.get("exists", True)
        is_directory = dir_info.get("is_directory", True)
        
        # 创建卡片容器
        card = QFrame()
        card.setFixedSize(280, 320)  # 固定卡片大小，类似Web的minmax
        card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 10px;
                border: 1px solid #eee;
                margin: 2px;
            }
            QFrame:hover {
                border: 2px solid #9DB0DA;
                margin: 0px;
            }
        """)
        
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)
        
        # === 封面图片区域 ===
        cover_container = QWidget()
        cover_container.setFixedHeight(200)
        cover_container.setStyleSheet("background: transparent;")
        
        cover_layout = QVBoxLayout()
        cover_layout.setContentsMargins(0, 0, 0, 0)
        
        cover_label = QLabel()
        cover_label.setAlignment(Qt.AlignCenter)
        cover_label.setCursor(Qt.PointingHandCursor)
        cover_label.setStyleSheet("background-color: #f0f0f0; border-radius: 10px 10px 0 0;")
        cover_label.setFixedSize(280, 200)
        
        # 设置封面图片
        cover_path = self.find_cover_image(path)
        if cover_path and os.path.exists(cover_path):
            # 使用安全方法缩放图片
            scaled_pixmap = self.safe_load_and_scale_image(cover_path, 280, 200)
            if scaled_pixmap and not scaled_pixmap.isNull():
                cover_label.setPixmap(scaled_pixmap)
                cover_label.setScaledContents(True)
        else:
            cover_label.setText("📁\n无封面图片")
            cover_label.setStyleSheet("""
                QLabel {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 10px 10px 0 0;
                    color: #6c757d;
                    font-size: 14px;
                }
            """)
        
        # 点击封面打开预览
        if cover_path and os.path.exists(cover_path):
            cover_label.mousePressEvent = self.create_thumbnail_click_handler(cover_path)
        else:
            cover_label.mousePressEvent = self.create_thumbnail_click_handler(path)
        
        cover_layout.addWidget(cover_label)
        cover_container.setLayout(cover_layout)
        card_layout.addWidget(cover_container)
        
        # === 内容区域 ===
        content_widget = QWidget()
        content_widget.setStyleSheet("padding: 10px;")
        content_layout = QVBoxLayout()
        content_layout.setSpacing(5)
        
        # 目录名称
        name_label = QLabel(name)
        name_label.setWordWrap(True)
        name_label.setMaximumHeight(40)
        name_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
                margin-bottom: 5px;
            }
        """)
        name_label.setToolTip(name)
        content_layout.addWidget(name_label)
        
        # 路径信息（截断显示）
        short_path = path[:60] + "..." if len(path) > 60 else path
        path_label = QLabel(short_path)
        path_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #666;
                margin-bottom: 5px;
            }
        """)
        path_label.setToolTip(path)
        content_layout.addWidget(path_label)
        
        # 状态和文件类型标签
        info_layout = QHBoxLayout()
        
        # 类型标签
        type_badge = QLabel("📁 目录" if is_directory else "📄 文件")
        type_badge.setStyleSheet("""
            QLabel {
                background: #9DB0DA;
                color: white;
                padding: 3px 8px;
                border-radius: 10px;
                font-size: 10px;
            }
        """)
        
        # 状态标签
        status_badge = QLabel("✅ 上架" if exists else "❌ 下架")
        status_badge.setStyleSheet(f"""
            QLabel {{
                background: {'#4CAF50' if exists else '#F44336'};
                color: white;
                padding: 3px 8px;
                border-radius: 10px;
                font-size: 10px;
            }}
        """)
        
        info_layout.addWidget(type_badge)
        info_layout.addWidget(status_badge)
        info_layout.addStretch()
        content_layout.addLayout(info_layout)
        
        content_widget.setLayout(content_layout)
        card_layout.addWidget(content_widget)
        
        # === 按钮区域 ===
        button_widget = QWidget()
        button_widget.setStyleSheet("padding: 5px 10px;")
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        # 打开按钮
        open_btn = QPushButton("📂 打开")
        open_btn.setStyleSheet("""
            QPushButton {
                background: #9DB0DA;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 15px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #8A9DC8;
            }
        """)
        
        # 修复lambda闭包问题
        def make_open_callback(dir_path):
            return lambda: self.open_directory(dir_path)
        
        def make_info_callback(dir_info):
            return lambda: self.show_grid_card_info(dir_info)
        
        open_btn.clicked.connect(make_open_callback(path))
        
        # 信息按钮
        info_btn = QPushButton("ℹ️ 详情")
        info_btn.setStyleSheet("""
            QPushButton {
                background: #B1C16B;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 15px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #9AAA58;
            }
        """)
        info_btn.clicked.connect(make_info_callback(dir_info))
        
        button_layout.addWidget(open_btn)
        button_layout.addWidget(info_btn)
        button_widget.setLayout(button_layout)
        card_layout.addWidget(button_widget)
        
        card.setLayout(card_layout)
        return card

    def show_grid_card_info(self, dir_info):
        """显示网格卡片的详细信息"""
        name = dir_info.get("name", "")
        path = dir_info.get("path", "")
        exists = dir_info.get("exists", True)
        created_time = dir_info.get("created_time", "")
        last_modified = dir_info.get("last_modified", "")
        is_directory = dir_info.get("is_directory", True)
        
        info_text = f"""
    <b>详细信息</b><br>
    <br>
    <b>名称:</b> {name}<br>
    <b>路径:</b> {path}<br>
    <b>类型:</b> {'📁 目录' if is_directory else '📄 文件'}<br>
    <b>状态:</b> {'✅ 上架' if exists else '❌ 下架'}<br>
    <b>创建时间:</b> {created_time}<br>
    <b>最后修改:</b> {last_modified}<br>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("目录详情")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(info_text)
        msg_box.addButton("打开目录", QMessageBox.ActionRole)
        msg_box.addButton("复制路径", QMessageBox.ActionRole)
        msg_box.addButton("关闭", QMessageBox.RejectRole)
        
        result = msg_box.exec()
        
        if result == 0:  # 打开目录
            self.open_directory(path)
        elif result == 1:  # 复制路径
            QApplication.clipboard().setText(path)
            self.update_status_bar("路径已复制到剪贴板", 3000)

    def is_widget_valid(self, widget):
        """检查Qt控件是否仍然有效"""
        if widget is None:
            return False
        try:
            # 尝试访问控件的属性来验证它是否仍然有效
            _ = widget.isVisible()
            return True
        except RuntimeError as e:
            if "Internal C++ object" in str(e):
                return False
            raise

    def scan_directory_incremental(self, path, depth):
        """增量扫描目录 - 只处理变化的文件和目录"""
        directories = []
        changes_detected = False
        
        # 获取上次扫描记录
        last_scan_info = self.get_last_scan_info(path)
        
        try:
            current_items = {}
            for entry in os.scandir(path):
                if not self.is_running:
                    break
                try:
                    stat = entry.stat()
                    current_items[entry.name] = {
                        'path': entry.path,
                        'mtime': stat.st_mtime,
                        'size': stat.st_size,
                        'is_dir': entry.is_dir(follow_symlinks=False)
                    }
                except (PermissionError, OSError):
                    continue
            
            # 对比变化
            if last_scan_info:
                # 检查新增和修改
                for name, info in current_items.items():
                    if name not in last_scan_info:
                        changes_detected = True
                        dir_info = self.get_item_info(info['path'], info['is_dir'])
                        if dir_info:
                            directories.append(dir_info)
                    else:
                        last_info = last_scan_info[name]
                        if (abs(info['mtime'] - last_info['mtime']) > 0.1 or
                            info['size'] != last_info['size']):
                            changes_detected = True
                            dir_info = self.get_item_info(info['path'], info['is_dir'])
                            if dir_info:
                                directories.append(dir_info)
                
                # 检查删除（可选：标记为不存在而非删除）
                for name in last_scan_info:
                    if name not in current_items:
                        changes_detected = True
                        # 标记目录为不存在
                        directories.append({
                            "name": name,
                            "path": last_scan_info[name]['path'],
                            "directory_exists": 0,
                            "is_directory": last_scan_info[name]['is_dir'],
                            "created_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "last_modified": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
            else:
                # 首次扫描，添加所有项
                changes_detected = True
                for name, info in current_items.items():
                    dir_info = self.get_item_info(info['path'], info['is_dir'])
                    if dir_info:
                        directories.append(dir_info)
            
            # 递归扫描子目录（仅当有变化或深度允许时）
            if depth > 0 and changes_detected:
                for entry in os.scandir(path):
                    if not self.is_running:
                        break
                    if entry.is_dir(follow_symlinks=False):
                        try:
                            sub_dirs = self.scan_directory_incremental(entry.path, depth - 1)
                            directories.extend(sub_dirs)
                        except (PermissionError, OSError):
                            continue
            
            # 保存扫描状态供下次使用
            self.save_scan_state(path, current_items)
            
            return directories
            
        except Exception as e:
            self.error_occurred.emit(f"增量扫描失败 {path}: {str(e)}")
            return directories

    def get_last_scan_info(self, path):
        """获取上次扫描信息"""
        if not hasattr(self, 'main_app') or not self.main_app:
            return None
        
        try:
            conn = sqlite3.connect(self.main_app.user_manager.current_db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, path, last_modified, is_directory 
                FROM directories 
                WHERE path LIKE ? AND directory_exists = 1
            """, (f"{path}%",))
            
            last_info = {}
            for row in cursor.fetchall():
                name, item_path, last_modified, is_directory = row
                try:
                    mtime = datetime.datetime.strptime(last_modified, "%Y-%m-%d %H:%M:%S").timestamp()
                except:
                    mtime = 0
                last_info[name] = {
                    'path': item_path,
                    'mtime': mtime,
                    'is_dir': is_directory
                }
            conn.close()
            return last_info
        except Exception as e:
            print(f"[INCREMENTAL] 获取上次扫描信息失败: {e}")
            return None

    def save_scan_state(self, path, current_items):
        """保存扫描状态（可选，用于快速比较）"""
        # 可以保存到单独的状态文件或数据库表
        pass

    def get_item_info(self, item_path, is_directory):
        """获取项目信息"""
        try:
            stat = os.stat(item_path)
            name = os.path.basename(item_path)
            
            return {
                "name": name,
                "path": item_path,
                "created_time": datetime.datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                "last_modified": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "directory_exists": 1,
                "is_main_dir": 0,
                "is_directory": 1 if is_directory else 0
            }
        except Exception as e:
            print(f"获取项目信息失败 {item_path}: {e}")
            return None

# 主程序
if __name__ == "__main__":
    # 处理打包后的资源路径
    if getattr(sys, 'frozen', False):
        # 如果是打包后的环境，切换到exe所在目录
        os.chdir(os.path.dirname(sys.executable))
    
    app = QApplication(sys.argv)
    
    # 设置应用程序名称和样式
    app.setApplicationName("目录扫描管理系统")
    app.setStyle("Fusion")
    
    # 创建主窗口
    window = DirectoryScannerApp()
    window.show()

    # 【性能优化】此处原先重复调用了一次 window.init_server()。
    # DirectoryScannerApp.__init__ 已经调用过（约 9770），本次调用会
    # 再建一个 DirectoryScannerServer 实例把前一个丢弃，并把 server_status
    # 重置为 False，同时白跑一轮 get_available_port 端口探测。
    #
    # 安全移除的依据：__init__ 里依赖服务器的两个动作都是 QTimer
    # （100ms 的 update_server_status_display、500ms 的 auto_start_web_server），
    # 它们要等 app.exec() 事件循环启动后才触发，必然发生在窗口构造之后，
    # 因此拿到的始终是 __init__ 中创建的那个 server 实例。
    # 移除后行为不变：服务器仍由 auto_start_web_server 按设置自动启动。

    sys.exit(app.exec())