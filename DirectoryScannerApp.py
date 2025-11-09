import os
import sys
import shutil
import sqlite3
import datetime
# from datetime import datetime
# import datetime as dt
import time
import re
import glob
import hashlib
import subprocess
import http.server
import socketserver
import threading
import json
import urllib.parse
from http import HTTPStatus
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QDialog, QComboBox, QSpinBox, 
                             QCheckBox, QFileDialog, QTabWidget, QGridLayout, QGroupBox,
                             QDateEdit, QToolButton, QSizePolicy, QStackedWidget, QAction,
                             QMenu, QSystemTrayIcon, QScrollArea, QInputDialog, QFrame, 
                             QTextEdit, QProgressDialog, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, QDateTime, QSize, QSettings, pyqtSignal, QThread
from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
from PyQt5.QtGui import (QIcon, QColor, QFont, QPixmap, QBrush, QColor, QPixmap)
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel
# 添加拼音转换库
try:
    from pypinyin import pinyin, Style
except ImportError:
    # 如果没有安装pypinyin，使用简单的拼音映射
    pinyin_available = False
else:
    pinyin_available = True

if pinyin_available:
    pass    



class ProjectInfo:
    """项目信息元数据（集中管理所有项目相关信息）"""
    VERSION = "2.91.0"
    BUILD_DATE = "2025-11-09"
    # from datetime import datetime
    # BUILD_DATE = datetime.now().strftime("%Y-%m-%d")  # 修改为动态获取当前日期
    AUTHOR = "杜玛"
    LICENSE = "MIT"
    COPYRIGHT = "© 永久 杜玛"
    URL = "https://github.com/duma520"
    MAINTAINER_EMAIL = "不提供"
    NAME = "目录扫描管理系统"
    DESCRIPTION = "目录扫描管理系统是一个用于扫描和管理文件系统目录的应用程序，支持多用户和自动备份功能。"

    # 补充完整的版本历史
    VERSION_HISTORY = {
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
        "gui_framework": "PyQt5",
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
        "PyQt5 >= 5.15.0",
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
        """检查文本是否包含拼音首字母"""
        text_initials = PinyinSearchHelper.get_pinyin_initials(text)
        return search_initials in text_initials




class DirectoryScannerHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """目录扫描系统的HTTP请求处理器"""

    def __init__(self, *args, main_app=None, open_directory_callback=None, **kwargs):
        self.main_app = main_app
        self.open_directory_callback = open_directory_callback
        super().__init__(*args, **kwargs)

    
    def do_GET(self):
        """处理GET请求"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path

            print(f"[HTTP DEBUG] 请求路径: {path}")

            # 静态文件服务
            if path.startswith('/static/'):
                self.handle_static_file(path)
            elif path == '/':
                self.send_html_response(self.get_index_html())
            elif path == '/api/directories':
                self.send_json_response(self.get_directories_data())
            elif path == '/api/directories/search':
                self.handle_search_request(parsed_path.query)
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
                        console.error(`✗ ${{lib.description}} 加载失败`);
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
        """处理POST请求"""
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
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "API endpoint not found")
                
        except Exception as e:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))



    def get_index_html(self):
        """返回主页面HTML - 增强版，支持PDF、视频、文档播放和优化界面"""
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
            
            .directories-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
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
                background: white;
                border-radius: 10px;
                max-width: 95%;
                max-height: 95%;
                overflow: auto;
                position: relative;
            }
            
            .modal-image {
                max-width: 100%;
                max-height: 95vh;
                display: block;
                margin: 0 auto;
            }
            
            .modal-video {
                width: 90%;
                height: auto;
                max-height: 90vh;
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
            
            .media-controls {
                position: absolute;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                display: none !important;
                gap: 10px;
                background: rgba(0, 0, 0, 0.7);
                padding: 10px;
                border-radius: 5px;
                visibility: hidden !important;
                opacity: 0 !important;
                pointer-events: none !important;
            }
            
            .pdf-controls {
                position: absolute;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                display: flex;
                gap: 10px;
                background: rgba(0, 0, 0, 0.8);
                padding: 10px 15px;
                border-radius: 25px;
                z-index: 1002;
            }
            
            .media-btn {
                background: none;
                border: none;
                color: white;
                cursor: pointer;
                padding: 5px 10px;
                display: none !important;
                visibility: hidden !important;
                opacity: 0 !important;
            }

            .pdf-btn {
                background: none;
                border: none;
                color: white;
                cursor: pointer;
                padding: 8px 12px;
                border-radius: 5px;
                transition: background-color 0.3s;
            }
            
            .pdf-btn:hover {
                background: rgba(255, 255, 255, 0.2);
            }
            
            .pdf-page-info {
                color: white;
                padding: 8px 12px;
                font-size: 14px;
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
            
            .filter-controls {
                display: flex;
                gap: 10px;
                align-items: center;
                margin-left: auto;
            }
            
            .filter-select {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background: white;
            }
            
            .file-size {
                font-size: 0.8em;
                color: #888;
                margin-top: 5px;
            }

            /* PDF模态框专用样式 */
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
                    <button class="btn btn-warning" onclick="showSystemInfo()">ℹ️ 系统信息</button>
                    <button class="btn btn-info" onclick="toggleViewMode()">📋 列表视图</button>
                </div>
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
        
        <!-- 图片/视频预览模态框 -->
        <div id="mediaModal" class="modal" onclick="closeMediaModal()">
            <div class="modal-content">
                <button class="close-modal" onclick="closeMediaModal()">×</button>
                <img id="modalImage" class="modal-image" src="" onclick="event.stopPropagation()" style="display: none;">
                <video id="modalVideo" class="modal-video" controls autoplay onclick="event.stopPropagation()" style="display: none;">
                    您的浏览器不支持视频播放
                </video>
                <div class="media-controls" style="display: none;">
                    <button class="media-btn" onclick="playPauseVideo()">⏯️</button>
                    <button class="media-btn" onclick="muteUnmuteVideo()">🔇</button>
                    <button class="media-btn" onclick="fullscreenVideo()">⛶</button>
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
            let currentPdfZoom = 1.0;
            let currentDocumentZoom = 1.0;
            
            // 页面加载完成后初始化
            document.addEventListener('DOMContentLoaded', function() {
                loadDirectories();
                updateSystemStatus();
                setInterval(updateSystemStatus, 30000);
            });
            
            // 加载目录数据
            async function loadDirectories(searchTerm = '') {
                try {
                    showLoading();
                    const url = searchTerm ? '/api/directories/search?q=' + encodeURIComponent(searchTerm) : '/api/directories';
                    const response = await fetch(url);
                    const data = await response.json();
                    
                    currentData = data.directories || [];
                    applyFiltersAndSort();
                    updateItemCount(currentData.length);
                    updateStatus('数据加载成功');
                    
                } catch (error) {
                    console.error('加载目录失败:', error);
                    updateStatus('加载失败: ' + error.message, 'error');
                    showError('无法加载目录数据');
                }
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
                            return a.name.localeCompare(b.name);
                        case 'date':
                            return new Date(b.last_modified) - new Date(a.last_modified);
                        case 'size':
                            return 0;
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
            
            // 显示目录列表
            function displayDirectories(directories) {
                const container = document.getElementById('directoriesContainer');
                container.className = currentViewMode === 'grid' ? 'directories-grid' : 'directories-list';
                
                if (directories.length === 0) {
                    container.innerHTML = '<div class="no-results">📭 没有找到匹配的目录</div>';
                    return;
                }
                
                let html = '';
                
                directories.forEach(dir => {
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
                            <div class="directory-card" data-type="${fileType}">
                                <div style="position: relative;">
                                    ${!dir.is_directory ? `<div class="file-type-badge">${getFileTypeBadge(dir.name)}</div>` : ''}
                                    <img class="cover-image" 
                                        src="/api/cover?path=${encodedPath}" 
                                        alt="${dir.name}"
                                        onclick="showMedia('${encodedPath}', '${fileType}')"
                                        onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2Y4ZjlmYSIvPjx0ZXh0IHg9IjEwMCIgeT0iMTAwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM2Yzc1N2QiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIwLjM1ZW0iPuiNieeUqOaAp+aEn+WbvueJhzwvdGV4dD48L3N2Zz4='">
                                    ${isVideo ? '<div class="video-indicator">🎬 视频</div>' : ''}
                                    ${isPdf ? '<div class="pdf-indicator">📄 PDF</div>' : ''}
                                    ${isDocument ? '<div class="document-indicator">📝 文档</div>' : ''}
                                </div>
                                <div class="card-content">
                                    <div class="directory-name">${dir.name}</div>
                                    <div class="directory-path" title="${dir.path}">${dir.path}</div>
                                    <div class="directory-info">
                                        <span>修改: ${formatDate(dir.last_modified)}</span>
                                        <span>ID: ${dir.id}</span>
                                        <span class="${dir.exists ? 'status-online' : 'status-offline'}">
                                            ${dir.exists ? '✅ 上架' : '❌ 下架'}
                                        </span>
                                    </div>
                                    <div class="card-actions">
                                        <button class="btn btn-primary btn-small" onclick="openDirectory('${dir.path}', ${dir.id})">📂 打开</button>
                                        <button class="btn btn-success btn-small" onclick="showMedia('${encodedPath}', '${fileType}')">
                                            ${isVideo ? '🎬 播放' : isImage ? '🖼️ 查看' : isPdf ? '📄 查看PDF' : isDocument ? '📝 查看文档' : '📄 查看'}
                                        </button>
                                        <button class="btn btn-info btn-small" onclick="showDatabaseInfo(${dir.id})">ℹ️ 信息</button>
                                    </div>
                                </div>
                            </div>
                        `;
                    } else {
                        html += `
                            <div class="directory-list-item" data-type="${fileType}">
                                <img class="list-cover" 
                                    src="/api/cover?path=${encodedPath}" 
                                    alt="${dir.name}"
                                    onclick="showMedia('${encodedPath}', '${fileType}')"
                                    onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjgwIiBoZWlnaHQ9IjYwIiBmaWxsPSIjZjhmOWZhIi8+PHRleHQgeD0iNDAiIHk9IjMwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTIiIGZpbGw9IiM2Yzc1N2QiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIwLjNlbSI+5Y2V5L2N5Zu+54mHPC90ZXh0Pjwvc3ZnPg==='">
                                <div class="list-content">
                                    <div class="directory-name">${dir.name} ${isVideo ? '🎬' : isImage ? '🖼️' : isPdf ? '📄' : isDocument ? '📝' : ''}</div>
                                    <div class="directory-path" title="${dir.path}">${dir.path}</div>
                                    <div class="list-info">
                                        <span>修改: ${formatDate(dir.last_modified)}</span>
                                        <span>ID: ${dir.id}</span>
                                        <span class="${dir.exists ? 'status-online' : 'status-offline'}">
                                            ${dir.exists ? '✅ 上架' : '❌ 下架'}
                                        </span>
                                    </div>
                                </div>
                                <div class="list-actions">
                                    <button class="btn btn-primary btn-small" onclick="openDirectory('${dir.path}', ${dir.id})">打开</button>
                                    <button class="btn btn-success btn-small" onclick="showMedia('${encodedPath}', '${fileType}')">
                                        ${isVideo ? '播放' : isImage ? '查看' : isPdf ? '查看PDF' : isDocument ? '查看文档' : '查看'}
                                    </button>
                                    <button class="btn btn-info btn-small" onclick="showDatabaseInfo(${dir.id})">信息</button>
                                </div>
                            </div>
                        `;
                    }
                });
                
                container.innerHTML = html;
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
                const date = new Date(dateString);
                return date.toLocaleDateString('zh-CN');
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

            // 显示媒体（图片、视频、PDF或文档）
            async function showMedia(path, mediaType) {
                try {
                    const decodedPath = decodeURIComponent(path);
                    
                    if (mediaType === 'video') {
                        // 视频播放
                        const videoUrl = '/api/video?path=' + encodeURIComponent(decodedPath);
                        const modalVideo = document.getElementById('modalVideo');
                        const modalImage = document.getElementById('modalImage');
                        const modal = document.getElementById('mediaModal');
                        
                        modalVideo.src = videoUrl;
                        modalVideo.style.display = 'block';
                        modalImage.style.display = 'none';
                        modal.style.display = 'flex';
                        
                    } else if (mediaType === 'pdf') {
                        // PDF显示
                        showPdfModal(decodedPath);
                        
                    } else if (mediaType === 'document') {
                        // 检查是否是EPUB文件
                        if (decodedPath.toLowerCase().endsWith('.epub')) {
                            // EPUB文件在新窗口中打开高级阅读器
                            const epubUrl = '/api/document?path=' + encodeURIComponent(decodedPath) + '&preview=true';
                            const windowFeatures = 'width=1200,height=800,resizable=yes,scrollbars=yes';
                            window.open(epubUrl, '_blank', windowFeatures);
                        } else {
                            // 其他文档显示
                            showDocumentModal(decodedPath);
                        }
                        
                    } else {
                        // 图片显示
                        const coverUrl = '/api/cover?path=' + encodeURIComponent(decodedPath);
                        const modalImage = document.getElementById('modalImage');
                        const modalVideo = document.getElementById('modalVideo');
                        const modal = document.getElementById('mediaModal');
                        
                        modalImage.src = coverUrl;
                        modalImage.style.display = 'block';
                        modalVideo.style.display = 'none';
                        modal.style.display = 'flex';
                    }
                } catch (error) {
                    console.error('显示媒体失败:', error);
                    alert('无法加载媒体文件: ' + error.message);
                }
            }
            
            // 显示PDF模态框
            function showPdfModal(pdfPath) {
                const pdfModal = document.getElementById('pdfModal');
                const pdfIframe = document.getElementById('modalPdf');
                const pdfTitle = document.getElementById('pdfModalTitle');
                
                // 设置PDF标题
                const fileName = pdfPath.split('/').pop() || 'PDF文档';
                pdfTitle.textContent = `PDF预览 - ${fileName}`;
                
                // 构建PDF URL
                const pdfUrl = '/api/pdf?path=' + encodeURIComponent(pdfPath);
                pdfIframe.src = pdfUrl;
                
                // 重置缩放
                currentPdfZoom = 1.0;
                updatePdfZoomInfo();
                
                // 显示模态框
                pdfModal.style.display = 'flex';
                
                // 添加键盘事件监听
                document.addEventListener('keydown', handlePdfKeydown);
            }
            
            // PDF键盘控制
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
            
            // PDF控制函数
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
            
            // 关闭PDF模态框
            function closePdfModal() {
                const pdfModal = document.getElementById('pdfModal');
                const pdfIframe = document.getElementById('modalPdf');
                
                pdfIframe.src = '';
                pdfIframe.style.transform = '';
                pdfModal.style.display = 'none';
                
                document.removeEventListener('keydown', handlePdfKeydown);
            }

            // 显示文档模态框
            function showDocumentModal(docPath) {
                const docModal = document.getElementById('documentModal');
                const docIframe = document.getElementById('modalDocument');
                const docTitle = document.getElementById('documentModalTitle');
                
                // 设置文档标题
                const fileName = docPath.split('/').pop() || '文档';
                docTitle.textContent = `文档预览 - ${fileName}`;
                
                // 构建文档URL
                const docUrl = '/api/document?path=' + encodeURIComponent(docPath);
                docIframe.src = docUrl;
                
                // 重置缩放
                currentDocumentZoom = 1.0;
                updateDocumentZoomInfo();
                
                // 显示模态框
                docModal.style.display = 'flex';
                
                // 添加键盘事件监听
                document.addEventListener('keydown', handleDocumentKeydown);
            }

            // 文档键盘控制
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

            // 文档控制函数
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

            // 关闭文档模态框
            function closeDocumentModal() {
                const docModal = document.getElementById('documentModal');
                const docIframe = document.getElementById('modalDocument');
                
                docIframe.src = '';
                docIframe.style.zoom = '';
                docModal.style.display = 'none';
                
                document.removeEventListener('keydown', handleDocumentKeydown);
            }
            
            // 视频控制函数
            function playPauseVideo() {
                const video = document.getElementById('modalVideo');
                if (video.paused) {
                    video.play();
                } else {
                    video.pause();
                }
            }
            
            function muteUnmuteVideo() {
                const video = document.getElementById('modalVideo');
                video.muted = !video.muted;
            }
            
            function fullscreenVideo() {
                const video = document.getElementById('modalVideo');
                if (video.requestFullscreen) {
                    video.requestFullscreen();
                } else if (video.webkitRequestFullscreen) {
                    video.webkitRequestFullscreen();
                } else if (video.mozRequestFullScreen) {
                    video.mozRequestFullScreen();
                }
            }
            
            // 关闭模态框
            function closeMediaModal() {
                const modal = document.getElementById('mediaModal');
                const video = document.getElementById('modalVideo');
                
                if (video && !video.paused) {
                    video.pause();
                }
                
                modal.style.display = 'none';
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
                    } else if (event.key === ' ') {
                        event.preventDefault();
                        playPauseVideo();
                    }
                }
                
                if ((event.ctrlKey || event.metaKey) && event.key === 'f') {
                    event.preventDefault();
                    document.getElementById('searchInput').focus();
                }
            });

            // 显示数据库信息
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
            
            // 开始扫描
            async function startScan() {
                try {
                    updateStatus('开始扫描目录...');
                    const response = await fetch('/api/scan', { method: 'POST' });
                    const result = await response.json();
                    
                    if (result.success) {
                        updateStatus('扫描完成');
                        setTimeout(() => loadDirectories(), 1000);
                    } else {
                        updateStatus('扫描失败: ' + result.error, 'error');
                    }
                } catch (error) {
                    updateStatus('扫描失败: ' + error.message, 'error');
                }
            }
            
            // 显示系统信息
            function showSystemInfo() {
                alert('系统信息:\\n' +
                    '名称: ''' + ProjectInfo.NAME + '''\\n' +
                    '版本: ''' + ProjectInfo.VERSION + '''\\n' +
                    '作者: ''' + ProjectInfo.AUTHOR + '''\\n' +
                    '描述: ''' + ProjectInfo.DESCRIPTION + '''\\n' +
                    '技术支持: ''' + ProjectInfo.URL + '''');
            }
            
            // 更新系统状态
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
            
            // 更新项目计数
            function updateItemCount(count) {
                document.getElementById('itemCount').textContent = '共 ' + count + ' 个项目';
            }
            
            // 更新状态信息
            function updateStatus(message, type = 'info') {
                const statusInfo = document.getElementById('statusInfo');
                statusInfo.textContent = message;
                statusInfo.style.color = type === 'error' ? '#ff4444' : '#666';
            }
            
            // 显示加载状态
            function showLoading() {
                const container = document.getElementById('directoriesContainer');
                container.innerHTML = '<div class="loading">正在加载...</div>';
                updateStatus('正在加载数据...');
            }
            
            // 显示错误
            function showError(message) {
                const container = document.getElementById('directoriesContainer');
                container.innerHTML = '<div class="no-results">❌ ' + message + '</div>';
            }
        </script>
    </body>
    </html>
    '''

    def get_directories_data(self):
        """获取目录数据 - 添加数据库ID"""
        if not self.main_app or not self.main_app.user_manager.current_db_path:
            return {"directories": [], "count": 0}
        
        try:
            conn = sqlite3.connect(self.main_app.user_manager.current_db_path)
            cursor = conn.cursor()
            
            # 修改查询语句，包含id字段
            cursor.execute("""
                SELECT id, name, path, directory_exists, created_time, last_modified, is_directory 
                FROM directories 
                ORDER BY name
            """)
            
            directories = []
            results = cursor.fetchall()
            
            # 添加调试信息
            print(f"[DEBUG] 数据库查询结果数量: {len(results)}")
            if results:
                print(f"[DEBUG] 第一条结果: {results[0]}")
                print(f"[DEBUG] 结果列数: {len(results[0])}")
            
            for row in results:
                try:
                    # 安全解包，确保有7个字段
                    if len(row) == 7:
                        db_id, name, path, exists, created_time, last_modified, is_directory = row
                    else:
                        print(f"[WARNING] 数据库行字段数量不正确: {len(row)}")
                        continue
                        
                    try:
                        # 添加路径分析信息用于调试
                        path_parts = path.split('/') if '/' in path else path.split('\\')
                        debug_info = {
                            "total_parts": len(path_parts),
                            "last_part": path_parts[-1] if path_parts else "",
                            "parent_part": path_parts[-2] if len(path_parts) >= 2 else "",
                            "has_separator_issue": len(path_parts) >= 4 and 
                                                path_parts[-1].startswith(path_parts[-2]) and 
                                                len(path_parts[-1]) > len(path_parts[-2])
                        }
                    except Exception as e:
                        # 如果路径分析出错，使用默认的调试信息
                        debug_info = {
                            "total_parts": 0,
                            "last_part": "",
                            "parent_part": "",
                            "has_separator_issue": False,
                            "error": str(e)
                        }
                    
                    directories.append({
                        "id": db_id,  # 新增：数据库ID
                        "name": name,
                        "path": path,
                        "exists": bool(exists),
                        "created_time": created_time,
                        "last_modified": last_modified,
                        "is_directory": bool(is_directory),
                        "debug": debug_info
                    })

                    print(f"[SERVER DEBUG] 目录: {name}, 路径: {path}, ID: {db_id}")
                    
                except Exception as e:
                    print(f"[ERROR] 处理数据库行时出错: {e}, 行数据: {row}")
                    continue
            
            print(f"[SERVER DEBUG] 成功获取 {len(directories)} 条目录数据")
            conn.close()
        
            # 打印有问题的路径
            problematic_paths = [d for d in directories if d["debug"]["has_separator_issue"]]
            if problematic_paths:
                print(f"[SERVER DEBUG] 发现 {len(problematic_paths)} 个可能有分隔符问题的路径:")
                for d in problematic_paths:
                    print(f"  - {d['path']} -> 应该为: .../{d['debug']['parent_part']}/{d['debug']['last_part'][len(d['debug']['parent_part']):]}")
            
            return {"directories": directories, "count": len(directories)}
            
        except Exception as e:
            print(f"[SERVER ERROR] 获取目录数据失败: {e}")
            import traceback
            traceback.print_exc()
            return {"directories": [], "count": 0, "error": str(e)}

    
    def handle_search_request(self, query_string):
        """处理搜索请求"""
        query_params = urllib.parse.parse_qs(query_string)
        search_term = query_params.get('q', [''])[0].lower()
        
        if not search_term:
            self.send_json_response(self.get_directories_data())
            return
        
        data = self.get_directories_data()
        directories = data["directories"]
        
        # 过滤匹配的目录
        filtered_directories = []
        for dir_info in directories:
            name = dir_info["name"].lower()
            path = dir_info["path"].lower()
            
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
            "search_term": search_term
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
                success = QMetaObject.invokeMethod(
                    self.main_app, 
                    "open_directory", 
                    Qt.QueuedConnection,
                    Q_ARG(str, final_path)
                )
                
                if not success:
                    error_msg = "无法调用打开目录方法"
                else:
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
                    success = QMetaObject.invokeMethod(
                        self.main_app, 
                        "open_directory", 
                        Qt.QueuedConnection,  # 使用队列连接确保线程安全
                        Q_ARG(str, final_path)
                    )
                    
                    if not success:
                        error_msg = "无法调用打开目录方法"
                    else:
                        # 假设调用成功，实际结果需要主应用程序处理
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
            print(f"[HTTP SERVER] {message}")



    def handle_pdf_request(self, query_string):
        """处理PDF文件请求"""
        query_params = urllib.parse.parse_qs(query_string)
        path = query_params.get('path', [''])[0]
        
        if not path:
            self.send_error(HTTPStatus.BAD_REQUEST, "Missing path parameter")
            return
        
        try:
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
            
            # 发送PDF文件
            self.send_pdf_file(pdf_path)
            
        except Exception as e:
            print(f"[SERVER ERROR] 处理PDF请求失败: {e}")
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



class DirectoryScannerServer:
    """目录扫描系统服务器"""
    
    def __init__(self, main_app, host='localhost', port=8080):
        self.main_app = main_app
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        self.is_running = False
        self.lock = threading.Lock()
    
    def start(self):
        """启动服务器"""
        with self.lock:
            if self.is_running:
                print("[SERVER] 服务器已经在运行")
                return True
                
        try:
            # 创建自定义请求处理器，确保传递main_app参数和回调函数
            def handler_factory(*args, **kwargs):
                return DirectoryScannerHTTPRequestHandler(
                    *args, 
                    main_app=self.main_app,
                    open_directory_callback=self.main_app.open_directory,  # 新增回调
                    **kwargs
                )
            
            self.server = socketserver.TCPServer((self.host, self.port), handler_factory)
            self.server.allow_reuse_address = True
            
            # 在后台线程中启动服务器
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            self.is_running = True
            print(f"[SERVER] 目录扫描系统服务器已启动: http://{self.host}:{self.port}")
            print(f"[SERVER] 可以通过浏览器访问Web客户端")
            
            return True
            
        except Exception as e:
            print(f"[SERVER ERROR] 启动服务器失败: {e}")
            if "Address already in use" in str(e):
                print(f"[SERVER TIP] 端口 {self.port} 已被占用，请尝试其他端口或关闭占用程序")
            return False


    
    def stop(self):
        """停止服务器"""
        # === 新增：线程安全停止 ===
        with self.lock:
            if self.server:
                try:
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
        self.current_user = None
        self.current_db_path = None
        self.init_users_db()
    
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

    
    def add_user(self, username):
        conn = sqlite3.connect(self.users_db_path)
        cursor = conn.cursor()
        
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO users (username, created_at) VALUES (?, ?)", 
                          (username, now))
            conn.commit()
            
            # 创建用户数据库
            user_db_path = os.path.join(self.app_dir, f"user_{username}.db")
            self.init_user_db(user_db_path)
            
            return True, None
        except sqlite3.IntegrityError:
            return False, "用户名已存在"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    
    def init_user_db(self, db_path):
        try:
            # 确保目录存在
            if not os.path.exists(os.path.dirname(db_path)):
                os.makedirs(os.path.dirname(db_path))

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 创建目录表
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
            
            # 插入默认设置
            default_settings = [
                ("scan_interval", "3600"),  # 1小时
                ("include_filter", ""),
                ("exclude_filter", ""),
                ("display_columns", "name,path,exists,created_time"),
                ("auto_scan", "1"),
                ("scan_mode", "directories")
            ]
            
            for key, value in default_settings:
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
            return True, None
        except Exception as e:
            print(f"[ERROR] 用户登录失败: {e}")
            return False, str(e)
        finally:
            conn.close()

    def clear_user_data(self, username):
        """清除指定用户的所有目录数据"""
        user_db_path = os.path.join(self.app_dir, f"user_{username}.db")
        if not os.path.exists(user_db_path):
            return False, "用户数据库不存在"
        
        try:
            # 使用 WAL 模式连接数据库
            conn = sqlite3.connect(user_db_path)
            cursor = conn.cursor()
            
            # 删除所有目录记录
            cursor.execute("DELETE FROM directories")
            
            # 重置设置
            cursor.execute("DELETE FROM settings")
            
            # 重新插入默认设置
            default_settings = [
                ("scan_interval", "3600"),
                ("include_filter", ""),
                ("exclude_filter", ""),
                ("display_columns", "name,path,exists,created_time"),
                ("auto_scan", "1")
            ]
            
            for key, value in default_settings:
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
        reply = QMessageBox.question(
            self, "确认恢复",
            "确定要恢复此备份吗？当前数据库将被替换。\n建议先手动备份当前数据库。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, error = self.backup_manager.restore_backup(backup_path, self.db_path)
            if success:
                QMessageBox.information(self, "恢复成功", "数据库已成功恢复")
                self.accept()
            else:
                QMessageBox.critical(self, "恢复失败", f"恢复数据库时出错:\n{error}")

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
        
        add_button = QPushButton("添加用户")
        add_button.clicked.connect(self.add_user)
        
        add_layout.addWidget(self.new_username)
        add_layout.addWidget(add_button)
        add_group.setLayout(add_layout)
        
        layout.addWidget(add_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.login_button = QPushButton("登录选中用户")
        self.login_button.clicked.connect(self.login_selected_user)
        self.login_button.setEnabled(False)
        
        self.close_button = QPushButton("关闭")
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
            
            login_btn = QPushButton("登录")
            login_btn.clicked.connect(lambda _, u=username: self.login_user(u))
            login_btn.setFixedWidth(60)
            
            rename_btn = QPushButton("重命名")
            rename_btn.clicked.connect(lambda _, u=username: self.rename_user(u))
            rename_btn.setFixedWidth(60)
            
            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda _, u=username: self.delete_user(u))
            delete_btn.setFixedWidth(60)

            clear_btn = QPushButton("清除数据")
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

    
    def add_user(self):
        username = self.new_username.text().strip()
        if not username:
            QMessageBox.warning(self, "无效输入", "用户名不能为空")
            return
        
        success, error = self.user_manager.add_user(username)
        if success:
            self.new_username.clear()
            self.load_users()
            QMessageBox.information(self, "添加成功", f"用户 {username} 已成功添加")
        else:
            print(f"[DEBUG] 添加用户时出错:{error}")
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
        reply = QMessageBox.question(
            self, "确认清除数据",
            f"确定要清除用户 {username} 的所有目录数据吗？\n此操作将删除所有扫描记录但保留用户账户。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, error = self.user_manager.clear_user_data(username)
            if success:
                QMessageBox.information(self, "清除成功", f"用户 {username} 的数据已清除")
                # 如果当前用户是正在清除的用户，刷新主界面
                if self.user_manager.current_user == username:
                    self.parent().load_directories()
            else:
                QMessageBox.critical(self, "清除失败", f"清除数据时出错:\n{error}")



# 设置对话框 （每个用户独立保存所有设置）
class SettingsDialog(QDialog):
    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.setWindowTitle("设置")
        self.setMinimumSize(500, 400)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 选项卡
        tabs = QTabWidget()
        
        # 扫描设置
        scan_tab = QWidget()
        scan_layout = QVBoxLayout()
        
        # 扫描间隔
        scan_interval_group = QGroupBox("扫描间隔设置")
        scan_interval_layout = QHBoxLayout()
        
        self.scan_interval = QSpinBox()
        self.scan_interval.setMinimum(1)
        self.scan_interval.setMaximum(24 * 60)  # 24小时
        self.scan_interval.setSuffix(" 分钟")
        
        scan_interval_layout.addWidget(QLabel("自动扫描间隔:"))
        scan_interval_layout.addWidget(self.scan_interval)
        scan_interval_layout.addStretch()
        
        scan_interval_group.setLayout(scan_interval_layout)
        scan_layout.addWidget(scan_interval_group)
        
        # 自动扫描
        self.auto_scan = QCheckBox("启用自动扫描")
        scan_layout.addWidget(self.auto_scan)

        # 扫描模式设置
        mode_group = QGroupBox("扫描模式")
        mode_layout = QHBoxLayout()

        self.scan_mode = QComboBox()
        self.scan_mode.addItem("仅扫描目录", "directories")
        self.scan_mode.addItem("仅扫描文件", "files")
        self.scan_mode.addItem("扫描目录和文件", "both")

        mode_layout.addWidget(QLabel("扫描模式:"))
        mode_layout.addWidget(self.scan_mode)
        mode_layout.addStretch()

        mode_group.setLayout(mode_layout)
        scan_layout.addWidget(mode_group)

        # 目录过滤
        filter_group = QGroupBox("目录过滤设置")
        filter_layout = QVBoxLayout()
        
        # 包含过滤
        include_layout = QHBoxLayout()
        self.include_filter = QLineEdit()
        self.include_filter.setPlaceholderText("例如: project,work (逗号分隔)")
        
        include_layout.addWidget(QLabel("包含的目录:"))
        include_layout.addWidget(self.include_filter)
        filter_layout.addLayout(include_layout)
        
        # 排除过滤
        exclude_layout = QHBoxLayout()
        self.exclude_filter = QLineEdit()
        self.exclude_filter.setPlaceholderText("例如: temp,backup (逗号分隔)")
        
        exclude_layout.addWidget(QLabel("排除的目录:"))
        exclude_layout.addWidget(self.exclude_filter)
        filter_layout.addLayout(exclude_layout)
        
        filter_group.setLayout(filter_layout)
        scan_layout.addWidget(filter_group)

        # === 新增：服务器设置 ===
        server_group = QGroupBox("Web服务器设置")
        server_layout = QVBoxLayout()

        # 自动启动Web服务器
        self.auto_start_server = QCheckBox("自动启动Web服务器")
        self.auto_start_server.setToolTip("程序启动时自动启动Web服务器")

        server_layout.addWidget(self.auto_start_server)

        server_group.setLayout(server_layout)
        scan_layout.addWidget(server_group)

        scan_layout.addStretch()
        scan_tab.setLayout(scan_layout)
        tabs.addTab(scan_tab, "扫描设置")
        
        # 其他设置（每个用户独立保存所有设置）
        display_tab = QWidget()
        display_layout = QVBoxLayout()
        
        # 封面相关设置
        columns_group = QGroupBox("封面相关设置")
        columns_layout = QVBoxLayout()

        # === 新增：扫描时保存封面设置 ===
        scan_save_layout = QHBoxLayout()
        scan_save_layout.addWidget(QLabel("扫描时保存封面:"))

        self.scan_save_cover = QCheckBox("开启时每次扫描自动保存封面")
        self.scan_save_cover.setToolTip("开启后，每次扫描目录时会自动保存封面图片")
        scan_save_layout.addWidget(self.scan_save_cover)
        scan_save_layout.addStretch()

        columns_layout.addLayout(scan_save_layout)

        # === 新增：封面备份存在则跳过 ===
        cover_skip_layout = QHBoxLayout()
        cover_skip_layout.addWidget(QLabel("封面备份存在则跳过:"))

        self.skip_existing_covers = QCheckBox("开启时如果封面备份已存在则跳过保存")
        self.skip_existing_covers.setToolTip("开启后，扫描时如果封面备份已经存在，则跳过保存该封面")
        self.skip_existing_covers.setChecked(True)  # 默认开启
        cover_skip_layout.addWidget(self.skip_existing_covers)
        cover_skip_layout.addStretch()

        columns_layout.addLayout(cover_skip_layout)

        # === 新增：封面保存模式设置 ===
        cover_mode_layout = QHBoxLayout()
        cover_mode_layout.addWidget(QLabel("封面保存模式:"))
        
        self.cover_save_mode = QComboBox()
        self.cover_save_mode.addItem("智能模式", "smart")
        self.cover_save_mode.addItem("系列模式", "series")  
        self.cover_save_mode.addItem("首字模式", "first_char")
        cover_mode_layout.addWidget(self.cover_save_mode)
        cover_mode_layout.addStretch()
        
        columns_layout.addLayout(cover_mode_layout)
        
        # === 新增：封面保存目录设置 ===
        cover_dir_layout = QHBoxLayout()
        cover_dir_layout.addWidget(QLabel("封面保存目录:"))
        
        self.cover_save_dir = QLineEdit()
        self.cover_save_dir.setPlaceholderText("留空则使用默认目录: ~/目录封面")
        
        cover_browse_btn = QPushButton("浏览...")
        cover_browse_btn.clicked.connect(self.browse_cover_save_dir)
        cover_dir_layout.addWidget(self.cover_save_dir)
        cover_dir_layout.addWidget(cover_browse_btn)
        
        columns_layout.addLayout(cover_dir_layout)
        
        # === 新增：封面保存说明 ===
        cover_info_label = QLabel(
            "封面保存说明:\n"
            "• 智能模式: 自动识别AV格式使用系列模式，其他使用首字模式\n"
            "• 系列模式: 按XXXX-####格式建立系列目录\n"  
            "• 首字模式: 按名称首字母建立目录"
        )
        cover_info_label.setStyleSheet("color: #666; font-size: 11px;")
        columns_layout.addWidget(cover_info_label)

        # === 新增：批量操作按钮 ===
        batch_buttons_layout = QHBoxLayout()

        batch_save_all_btn = QPushButton("批量保存所有封面")
        batch_save_all_btn.clicked.connect(self.batch_save_all_covers)
        batch_save_all_btn.setToolTip("为所有已扫描目录保存封面图片")

        batch_save_missing_btn = QPushButton("只保存缺失封面")
        batch_save_missing_btn.clicked.connect(self.batch_save_missing_covers)
        batch_save_missing_btn.setToolTip("只为缺少封面的目录保存封面")

        batch_buttons_layout.addWidget(batch_save_all_btn)
        batch_buttons_layout.addWidget(batch_save_missing_btn)
        batch_buttons_layout.addStretch()

        columns_layout.addLayout(batch_buttons_layout)



        columns_group.setLayout(columns_layout)
        display_layout.addWidget(columns_group)
        display_layout.addStretch()
        display_tab.setLayout(display_layout)
        tabs.addTab(display_tab, "其他设置")
        
        layout.addWidget(tabs)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存设置")
        self.save_button.clicked.connect(self.save_settings)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def batch_save_all_covers(self):
        """调用主窗口的批量保存所有封面方法"""
        if hasattr(self, 'parent') and self.parent():
            self.parent().batch_save_all_covers()

    def batch_save_missing_covers(self):
        """只为缺少封面的目录保存封面"""
        if not self.user_manager.current_db_path:
            QMessageBox.warning(self, "未登录", "请先登录用户")
            return
        
        # 使用新的目录获取方法
        cover_save_dir = self.get_cover_save_directory()
        cover_save_mode = self.cover_save_mode.currentData()

        # 防御性编程：确保父窗口存在且有相应方法
        if hasattr(self, 'parent') and self.parent() and hasattr(self.parent(), 'batch_save_missing_covers'):
            self.parent().batch_save_missing_covers()
        else:
            QMessageBox.warning(self, "操作失败", "无法执行批量保存操作")



    def load_settings(self):
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

        # === 新增：加载封面保存模式 ===
        cursor.execute("SELECT value FROM settings WHERE key = 'cover_save_mode'")
        result = cursor.fetchone()
        if result:
            mode = result[0]
            index = self.cover_save_mode.findData(mode)
            if index >= 0:
                self.cover_save_mode.setCurrentIndex(index)
        else:
            # 默认使用智能模式
            self.cover_save_mode.setCurrentIndex(0)
        
        # === 新增：加载封面保存目录 ===
        cursor.execute("SELECT value FROM settings WHERE key = 'cover_save_dir'")
        result = cursor.fetchone()
        if result:
            self.cover_save_dir.setText(result[0])

        # === 新增：加载扫描时保存封面设置 ===
        cursor.execute("SELECT value FROM settings WHERE key = 'scan_save_cover'")
        result = cursor.fetchone()
        if result:
            self.scan_save_cover.setChecked(result[0] == "1")
        else:
            # 默认关闭
            self.scan_save_cover.setChecked(False)

        # === 新增：加载封面备份存在则跳过设置 ===
        cursor.execute("SELECT value FROM settings WHERE key = 'skip_existing_covers'")
        result = cursor.fetchone()
        if result:
            self.skip_existing_covers.setChecked(result[0] == "1")
        else:
            # 默认开启
            self.skip_existing_covers.setChecked(True)

        # === 新增：加载自动启动服务器设置 ===
        cursor.execute("SELECT value FROM settings WHERE key = 'auto_start_server'")
        result = cursor.fetchone()
        if result:
            self.auto_start_server.setChecked(result[0] == "1")
        else:
            # 默认开启
            self.auto_start_server.setChecked(True)

        conn.close()
    
    def save_settings(self):
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


            # === 新增：保存封面保存模式 ===
            cover_save_mode = self.cover_save_mode.currentData()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("cover_save_mode", cover_save_mode)
            )
            
            # === 新增：保存封面保存目录 ===
            cover_save_dir = self.cover_save_dir.text().strip()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("cover_save_dir", cover_save_dir)
            )

            # === 新增：保存扫描时保存封面设置 ===
            scan_save_cover = "1" if self.scan_save_cover.isChecked() else "0"
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("scan_save_cover", scan_save_cover)
            )

            # === 新增：保存封面备份存在则跳过设置 ===
            skip_existing_covers = "1" if self.skip_existing_covers.isChecked() else "0"
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("skip_existing_covers", skip_existing_covers)
            )

            # === 新增：保存自动启动服务器设置 ===
            auto_start_server = "1" if self.auto_start_server.isChecked() else "0"
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("auto_start_server", auto_start_server)
            )

            conn.commit()

            # 保存后验证设置
            self.verify_settings_saved()

            QMessageBox.information(self, "保存成功", "设置已成功保存")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存设置时出错:\n{e}")
        finally:
            conn.close()

    def verify_settings_saved(self):
        """验证设置是否真正保存成功 - 简化版本"""
        print("[DEBUG] 开始验证设置保存状态...")
        
        verification_results = {
            'success': [],
            'warning': [],
            'error': []
        }
        
        conn = None
        try:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            
            # 验证的关键设置列表 - 新增封面保存设置
            critical_settings = [
                'scan_interval', 
                'auto_scan', 
                'scan_mode',
                'include_filter',
                'exclude_filter',
                'cover_save_mode',  
                'cover_save_dir'    
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
                    
        except Exception as e:
            print(f"[CRITICAL] 验证设置时发生严重错误: {e}")
        finally:
            if conn:
                conn.close()
        
        # 输出验证结果
        if verification_results['success']:
            print(f"[SUCCESS] {len(verification_results['success'])} 个设置验证通过")
        else:
            print("[ERROR] 所有设置验证失败")
        
        return verification_results


    def browse_cover_save_dir(self):
        """浏览选择封面保存目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择封面保存目录", 
            self.cover_save_dir.text() or os.path.expanduser("~")
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




# 主窗口
class DirectoryScannerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
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
        
        # 初始化UI
        self.init_ui()
        
        # 检查是否需要显示用户管理对话框
        if not self.user_manager.current_user:
            self.show_user_manager()

        # 初始化服务器
        self.init_server()

        # === 新增：设置初始服务器状态显示 ===
        # 延迟设置初始状态，确保UI已完全初始化
        QTimer.singleShot(100, self.update_server_status_display)
    
        # 延迟启动服务器，避免影响界面加载
        QTimer.singleShot(2000, self.auto_start_web_server)

        # 初始化静态文件
        self.init_static_files()

        # 初始化静态文件（在后台线程中执行）
        self.init_static_files_async()        

    def init_static_files_async(self):
        """在后台线程中初始化静态文件"""
        import threading
        thread = threading.Thread(target=self.download_static_files)
        thread.daemon = True
        thread.start()


    def init_ui(self):
        # self.setWindowTitle("目录扫描管理系统")
        # self.setWindowTitle(f"{ProjectInfo.NAME} {ProjectInfo.VERSION} (Build: {ProjectInfo.BUILD_DATE})")
        # 初始设置标题（不包含用户名，因为此时用户可能还未登录）
        self.update_window_title()
        self.setMinimumSize(800, 600)
        self.resize(1000, 600)
        
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

        # === 新增：服务器状态指示器 ===
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
        self.server_action = QAction(QIcon.fromTheme("network-server"), "启动Web服务器", self)
        self.server_action.triggered.connect(self.toggle_server)
        toolbar.addAction(self.server_action)
        
        # 修改为"主目录管理"按钮
        main_dir_action = QAction(QIcon.fromTheme("folder-open"), "主目录管理", self)
        main_dir_action.triggered.connect(self.manage_main_directories)
        toolbar.addAction(main_dir_action)
        
        # 扫描按钮
        scan_action = QAction(QIcon.fromTheme("view-refresh"), "扫描目录", self)
        scan_action.triggered.connect(self.scan_directories)
        toolbar.addAction(scan_action)
        
        # 分隔线
        toolbar.addSeparator()

        # 批量保存封面按钮
        batch_cover_action = QAction(QIcon.fromTheme("document-save-all"), "批量保存封面", self)
        batch_cover_action.triggered.connect(self.batch_save_all_covers)
        toolbar.addAction(batch_cover_action)

        # 设置按钮
        settings_action = QAction(QIcon.fromTheme("preferences-system"), "设置", self)
        settings_action.triggered.connect(self.show_settings)
        toolbar.addAction(settings_action)
        
        # 用户管理按钮
        user_action = QAction(QIcon.fromTheme("system-users"), "用户管理", self)
        user_action.triggered.connect(self.show_user_manager)
        toolbar.addAction(user_action)
        
        # 数据库备份按钮
        backup_action = QAction(QIcon.fromTheme("document-save-as"), "数据库备份", self)
        backup_action.triggered.connect(self.manual_backup)
        toolbar.addAction(backup_action)
        
        # 恢复按钮
        restore_action = QAction(QIcon.fromTheme("document-revert"), "恢复数据库", self)
        restore_action.triggered.connect(self.show_restore_dialog)
        toolbar.addAction(restore_action)

        # 分隔线
        toolbar.addSeparator()

        # 关于按钮
        about_action = QAction(QIcon.fromTheme("help-about"), "关于", self)
        about_action.triggered.connect(self.show_about_dialog)
        toolbar.addAction(about_action)
        
        # 主目录显示
        self.dir_label = QLabel("主目录: 未设置")
        self.dir_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(self.dir_label)
        
        # 搜索栏
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索目录...按回车或点击搜索按钮")

        self.search_button = QPushButton("搜索")
        self.search_button.clicked.connect(self.filter_directories)
        self.search_input.returnPressed.connect(self.filter_directories)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        
        main_layout.addLayout(search_layout)

        # === 新增：进度条 ===
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
        self.grid_container = QWidget()
        self.scroll_area.setWidget(self.grid_container)
        main_layout.addWidget(self.scroll_area)

        # 状态栏
        self.statusBar().showMessage("就绪")

        # === 新增：状态栏服务器信息 ===
        self.status_server_info = QLabel("服务器: 未启动")
        self.statusBar().addPermanentWidget(self.status_server_info)

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
            print(f"[STATIC] ✗ {description} 下载失败: {e}")
    
    def format_file_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"

    def show_user_manager(self):
        dialog = UserManagerDialog(self.user_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            # 用户已登录，加载用户数据
            self.load_user_settings()
            self.load_directories()
            # 更新窗口标题显示用户名
            self.update_window_title()

            # === 修改这里：使用线程安全的状态栏更新 ===
            self.update_status_bar(f"用户 {self.user_manager.current_user} 登录成功", 3000)
            
            print(f"[DEBUG] 用户 {self.user_manager.current_user} 已登录，加载用户数据完成")    
            
            # 延迟启动自动扫描，避免登录后立即扫描造成卡顿
            QTimer.singleShot(3000, self.start_auto_scan)

        
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
        
        conn.close()

        # 确保启动自动扫描
        self.start_auto_scan()

    def scan_single_main_directory(self, path, depth):
        """扫描单个主目录"""
        # === 新增：线程安全检查 ===
        if QThread.currentThread() != self.thread():
            print(f"[ERROR] 扫描操作必须在主线程中执行: {path}")
            # 使用单次定时器在主线程中重新执行
            QTimer.singleShot(0, lambda: self.scan_single_main_directory(path, depth))
            return
    
        self.main_directory = path
        self.dir_label.setText(f"主目录: {path}")
        
        # 获取当前用户的扫描模式设置
        scan_mode = "directories"
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
    
        # === 修改这里：使用线程安全的状态栏更新 ===
        self.update_status_bar(f"正在扫描目录: {path}...")
    
        # === 确保进度条显示 ===
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"正在扫描目录: {path}...")
        QApplication.processEvents()
        
        try:
            # 传入扫描模式参数
            dirs = self.scan_directory_with_depth(path, depth, scan_mode)
    
            # === 修改这里：使用线程安全的状态栏更新 ===
            self.update_status_bar("正在保存到数据库...")
        
            # === 更新进度条 - 扫描完成 ===
            self.progress_bar.setValue(50)
            self.progress_label.setText("正在保存到数据库...")
            QApplication.processEvents()
        
            # 保存到数据库
            if self.user_manager.current_db_path:
                conn = sqlite3.connect(self.user_manager.current_db_path)
                cursor = conn.cursor()
                
                # 更彻底的清理：删除所有与该主目录相关的记录
                cursor.execute("DELETE FROM directories WHERE path LIKE ?", (f"{path}%",))
                
                # 插入或更新目录 - 加强数据验证
                valid_dirs_count = 0
                invalid_dirs_count = 0
                duplicate_paths = set()
                
                # === 新增：数据库保存进度 ===
                total_dirs = len(dirs)
                for j, dir_info in enumerate(dirs):
                    # 更新数据库保存进度
                    if j % 10 == 0:  # 每10个项目更新一次进度
                        db_progress = 50 + int((j / total_dirs) * 20)  # 数据库保存占20%
                        self.progress_bar.setValue(db_progress)
                        self.progress_label.setText(f"正在保存到数据库... ({j}/{total_dirs})")
                        QApplication.processEvents()
                    
                    # 更严格的数据验证
                    name = dir_info.get("name", "").strip() if dir_info.get("name") else ""
                    dir_path = dir_info.get("path", "").strip() if dir_info.get("path") else ""
                    
                    # 如果没有目录名称或没有路径，跳过不添加到列表
                    if not name or not dir_path:
                        invalid_dirs_count += 1
                        continue
                    
                    # 其他验证条件
                    if (name and dir_path and
                        dir_info.get("created_time") and dir_info.get("last_modified") and
                        dir_path not in duplicate_paths):  # 防止重复路径
                        
                        # 检查路径是否实际存在
                        if os.path.exists(dir_path):
                            cursor.execute("""
                                INSERT INTO directories 
                                (name, path, created_time, last_modified, directory_exists, last_scanned, is_main_dir, is_directory)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                name,
                                dir_path,
                                dir_info["created_time"],
                                dir_info["last_modified"],
                                1,
                                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                dir_info["is_main_dir"],
                                dir_info["is_directory"]
                            ))
                            valid_dirs_count += 1
                            duplicate_paths.add(dir_path)  # 记录已处理的路径
                        else:
                            invalid_dirs_count += 1
                    else:
                        invalid_dirs_count += 1
                
                conn.commit()
                
                # === 更新进度条 - 数据库保存完成 ===
                self.progress_bar.setValue(70)
                self.progress_label.setText("正在创建备份...")
                QApplication.processEvents()
                
                # 创建备份
                self.backup_manager.create_backup(self.user_manager.current_db_path)

                # 保存主目录设置
                self.save_main_directory_settings()
            
                # === 更新进度条 - 备份完成 ===
                self.progress_bar.setValue(80)
                self.progress_label.setText("正在保存封面图片...")
                QApplication.processEvents()

                # === 改进：每次扫描都保存/更新封面图片 ===
                # 检查是否开启了"扫描时保存封面"选项
                scan_save_cover = self.get_setting('scan_save_cover', '0') == '1'
                cover_save_mode, cover_save_dir = self.get_cover_save_settings()
                skip_existing = self.get_setting('skip_existing_covers', '1') == '1'
                
                if scan_save_cover and cover_save_dir:  # 只有在开启了选项且设置了保存目录时才保存封面
                    saved_count = 0
                    total_dirs_for_cover = len([d for d in dirs if d.get("is_directory", 1) == 1])

                    for k, dir_info in enumerate(dirs):                    
                        if dir_info.get("is_directory", 1) == 1:  # 只处理目录
                            dir_path = dir_info["path"]
                            if os.path.exists(dir_path):
                                cover_path = self.find_cover_image(dir_path)
                                if cover_path:
                                    # 新增：检查是否需要跳过
                                    expected_save_path = self.get_expected_cover_path(dir_path, cover_save_dir, cover_save_mode)
                                    if skip_existing and expected_save_path and os.path.exists(expected_save_path):
                                        # 检查MD5是否相同
                                        if self.is_same_image_by_md5(cover_path, expected_save_path):
                                            continue  # 跳过保存
                
                                    if self.save_cover_image(dir_path, cover_path):
                                        saved_count += 1

                            # === 更新封面保存进度 ===
                            if total_dirs_for_cover > 0:
                                cover_progress = 80 + int((k + 1) / total_dirs_for_cover * 20)
                                self.progress_bar.setValue(cover_progress)
                                self.progress_label.setText(f"正在保存封面图片... ({k+1}/{total_dirs_for_cover})")
                                QApplication.processEvents()
                
                    if saved_count > 0:
                        self.statusBar().showMessage(f"扫描完成，保存了 {saved_count} 个封面")
            
                # === 完成进度 ===
                self.progress_bar.setValue(100)
                self.progress_label.setText("扫描完成")
                
                # 显示扫描统计信息
                stats_msg = f"扫描完成: {valid_dirs_count} 个有效目录"
                if invalid_dirs_count > 0:
                    stats_msg += f", {invalid_dirs_count} 个无效目录被跳过"

                # === 新增：记录扫描完成时间 ===
                completion_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                stats_msg += f" | 完成时间: {completion_time}"

                self.statusBar().showMessage(stats_msg)

            # === 扫描失败时更新状态栏 ===
        except Exception as e:
            # === 修改这里：使用线程安全的状态栏更新 ===
            self.update_status_bar("扫描失败", 5000)
            
            self.progress_bar.setValue(0)
            self.progress_label.setText("扫描失败")
            QMessageBox.critical(self, "扫描错误", f"扫描目录时出错:\n{e}")
            print(f"[ERROR] 扫描错误: {e}")
        finally:
            # === 新增：确保数据库连接正确关闭 ===
            if 'conn' in locals() and conn:
                try:
                    conn.close()
                except Exception as e:
                    print(f"[WARNING] 关闭数据库连接时出错: {e}")
        
            # === 新增：扫描完成后隐藏进度条 ===
            QTimer.singleShot(2000, self.hide_progress_bar)  # 2秒后隐藏

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
        
        if not os.path.exists(path):
            QMessageBox.warning(self, "无效路径", "指定的目录不存在")
            return
        
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
        browse_btn.clicked.connect(lambda: self.new_main_dir_path.setText(QFileDialog.getExistingDirectory()))
        
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
        
        dialog.exec_()

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
        browse_btn.clicked.connect(lambda: self.edit_path_input.setText(QFileDialog.getExistingDirectory()))
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
        dialog.exec_()


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
        
        if not os.path.exists(new_path):
            QMessageBox.warning(dialog, "无效路径", "指定的目录不存在")
            return
        
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
        # === 新增：线程安全检查 ===
        if QThread.currentThread() != self.thread():
            print("[ERROR] 扫描操作必须在主线程中执行")
            QMessageBox.warning(self, "线程错误", "扫描操作必须在主线程中执行")
            # 使用单次定时器在主线程中重新执行
            QTimer.singleShot(0, self.scan_directories)
            return

        # 检查是否有主目录设置
        if not self.user_manager.current_db_path:
            QMessageBox.warning(self, "未登录", "请先登录用户")
            return
        
        # 查询数据库获取主目录列表
        conn = sqlite3.connect(self.user_manager.current_db_path)
        cursor = conn.cursor()
        # 同时查询扫描深度
        cursor.execute("SELECT id, path, scan_depth FROM main_directories")
        main_dirs = cursor.fetchall()
        conn.close()
        
        if not main_dirs:
            QMessageBox.warning(self, "无主目录", "请先添加主目录")
            return
    
        # === 修改这里：使用线程安全的状态栏更新 ===
        self.update_status_bar(f"准备扫描 {len(main_dirs)} 个主目录...")
        
        # === 确保进度条显示 ===
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"准备扫描 {len(main_dirs)} 个主目录...")
        QApplication.processEvents()
        
        # 扫描每个主目录
        for i, dir_info in enumerate(main_dirs):
            dir_id, path, depth = dir_info
        
            # === 修改这里：使用线程安全的状态栏更新 ===
            self.update_status_bar(f"正在扫描: {os.path.basename(path)}... ({i+1}/{len(main_dirs)})")
            
            # 更新进度
            progress_value = int((i) / len(main_dirs) * 100)
            self.progress_bar.setValue(progress_value)
            self.progress_label.setText(f"正在扫描: {os.path.basename(path)}... ({i+1}/{len(main_dirs)})")
            QApplication.processEvents()
            
            # 调用扫描单个主目录的方法
            self.scan_single_main_directory(path, depth)
        
        # 加载最新的目录列表
        self.load_directories()
        
        # === 完成扫描 ===
        self.progress_bar.setValue(100)
        self.progress_label.setText("所有主目录扫描完成")
    
        # === 新增：记录扫描完成时间 ===
        completion_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.update_status_bar(f"所有主目录扫描完成 | 完成时间: {completion_time}", 5000)
        
        # 3秒后隐藏进度条，给用户足够时间看到完成状态
        QTimer.singleShot(3000, self.hide_progress_bar)
        

    




    def load_directories(self):
        if not self.user_manager.current_db_path:
            return
        
        conn = sqlite3.connect(self.user_manager.current_db_path)
        cursor = conn.cursor()
        
        try:
            # === 添加更严格的数据库清理 ===
            # 1. 删除空名称或空路径的记录
            cursor.execute("""
                DELETE FROM directories 
                WHERE name IS NULL OR name = '' OR path IS NULL OR path = '' 
                OR TRIM(name) = '' OR TRIM(path) = ''
            """)
            
            # 2. 删除重复的记录（保留最新的记录）
            cursor.execute("""
                DELETE FROM directories 
                WHERE rowid NOT IN (
                    SELECT MIN(rowid) 
                    FROM directories 
                    GROUP BY path
                )
            """)
            
            # 3. 删除路径不存在的记录
            cursor.execute("SELECT rowid, path FROM directories")
            all_records = cursor.fetchall()
            for rowid, path in all_records:
                if not os.path.exists(path):
                    cursor.execute("DELETE FROM directories WHERE rowid = ?", (rowid,))
            
            conn.commit()
            # === 清理结束 ===
            
            # 然后查询清理后的数据
            cursor.execute("""
                SELECT name, path, directory_exists, created_time, last_modified, is_directory 
                FROM directories 
                ORDER BY name
            """)
            directories = cursor.fetchall()
            
            # 清除现有的表格内容
            if hasattr(self, 'table_widget'):
                self.table_widget.setRowCount(0)
            else:
                # 创建表格部件
                self.table_widget = QTableWidget()
                # 替换滚动区域为表格
                layout = self.centralWidget().layout()
                for i in reversed(range(layout.count())): 
                    widget = layout.itemAt(i).widget()
                    if widget == self.scroll_area:
                        layout.replaceWidget(self.scroll_area, self.table_widget)
                        self.scroll_area.deleteLater()
                        break
            
            # 设置表格列
            self.table_widget.setColumnCount(5)
            self.table_widget.setHorizontalHeaderLabels(["封面", "目录名称", "其他缩略图", "状态", "目录地址"])
            
            # 设置列宽
            self.table_widget.setColumnWidth(0, 200)   # 封面列
            self.table_widget.setColumnWidth(1, 200)   # 目录名称
            self.table_widget.setColumnWidth(2, 300)   # 其他缩略图
            self.table_widget.setColumnWidth(3, 80)    # 状态列
            self.table_widget.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)  # 目录地址自适应

            # 设置行高
            self.table_widget.verticalHeader().setDefaultSectionSize(150)
            
            # === 新增：更严格的数据验证和去重 ===
            valid_directories = []
            seen_paths = set()  # 用于去重
            
            for dir_info in directories:
                name, path, exists, created_time, last_modified, is_directory = dir_info
                
                # 严格的数据验证
                if (name and name.strip() and 
                    path and path.strip() and 
                    os.path.exists(path) and
                    path not in seen_paths):  # 防止重复路径
                    
                    valid_directories.append(dir_info)
                    seen_paths.add(path)  # 记录已处理的路径
                else:
                    print(f"[DEBUG] 跳过无效目录记录: 名称='{name}', 路径='{path}'")

            # 设置表格行数为实际有效数据数量
            self.table_widget.setRowCount(len(valid_directories))
            
            # 填充表格数据
            for row_idx, (name, path, exists, created_time, last_modified, is_directory) in enumerate(valid_directories):
                
            
                # 为每行设置固定高度
                self.table_widget.setRowHeight(row_idx, 150)
            
                # 第一列：封面图片
                cover_widget = QLabel()
                cover_widget.setFixedSize(180, 120)
                cover_widget.setAlignment(Qt.AlignCenter)
                cover_widget.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6;")
                cover_widget.setCursor(Qt.PointingHandCursor)  # 添加手型光标

                if is_directory == 1:  # 如果是目录
                    # 查找封面图片（目录中的第一张图片）
                    cover_path = self.find_cover_image(path)
                    if cover_path and os.path.exists(cover_path):
                        self.set_preview_image(cover_widget, cover_path)
                        # 为封面图片设置点击事件
                        cover_widget.mousePressEvent = lambda event, img_path=cover_path: self.on_image_clicked(event, img_path)
                    else:
                        # 没有图片则显示文件夹图标和提示文字
                        cover_widget.setText("📁\n无图片")
                        cover_widget.setStyleSheet("""
                            QLabel {
                                background-color: #f8f9fa; 
                                border: 1px solid #dee2e6;
                                color: #6c757d;
                                font-size: 12px;
                            }
                        """)
                else:
                    # 如果是文件，直接显示文件预览
                    if path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')) and os.path.exists(path):
                        self.set_preview_image(cover_widget, path)
                        # 为文件图片设置点击事件
                        cover_widget.mousePressEvent = lambda event, img_path=path: self.on_image_clicked(event, img_path)
                    else:
                        cover_widget.setText("📄\n非图片文件")
                        cover_widget.setStyleSheet("""
                            QLabel {
                                background-color: #f8f9fa; 
                                border: 1px solid #dee2e6;
                                color: #6c757d;
                                font-size: 12px;
                            }
                        """)
                
                self.table_widget.setCellWidget(row_idx, 0, cover_widget)
                
                # 第二列：目录名称
                name_item = QTableWidgetItem(name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                self.table_widget.setItem(row_idx, 1, name_item)
                
                # 第三列：其他缩略图
                thumbnails_widget = self.create_thumbnails_widget(path, is_directory)
                self.table_widget.setCellWidget(row_idx, 2, thumbnails_widget)
                
                # 第四列：上架/下架状态
                status_text = "上架" if exists else "下架"
                status_item = QTableWidgetItem(status_text)
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                
                # 根据状态设置颜色
                if exists:
                    status_item.setBackground(QBrush(QColor("#4CAF50")))  # 绿色
                    status_item.setForeground(QBrush(QColor("#FFFFFF")))  # 白色文字
                else:
                    status_item.setBackground(QBrush(QColor("#F44336")))  # 红色
                    status_item.setForeground(QBrush(QColor("#FFFFFF")))  # 白色文字
                
                self.table_widget.setItem(row_idx, 3, status_item)
                
                # 第五列：目录地址 - 添加点击功能
                path_item = QTableWidgetItem(path)
                path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
            
                # === 新增：为目录地址设置特殊样式和工具提示 ===
                path_item.setForeground(QBrush(QColor("#0066cc")))  # 蓝色文字
                path_item.setToolTip(f"点击打开目录: {path}")
            
                self.table_widget.setItem(row_idx, 4, path_item)
        
            # === 新增：连接单元格点击信号 ===
            self.table_widget.cellClicked.connect(self.on_table_cell_clicked)
        
            # 设置表格属性
            self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
            self.table_widget.setAlternatingRowColors(True)
            self.table_widget.setSortingEnabled(True)
            self.table_widget.horizontalHeader().setStretchLastSection(True)
            
            # 显示状态信息
            self.statusBar().showMessage(f"加载了 {len(valid_directories)} 个有效目录")

            # 设置图片点击事件
            self.setup_image_click_events()

        except Exception as e:
            print(f"[DEBUG] 加载目录出错: {e}")
            QMessageBox.critical(self, "加载目录出错", f"加载目录时发生错误:\n{e}")
        finally:
            conn.close()








    def create_thumbnails_widget(self, path, is_directory):
        """创建其他缩略图组件"""
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        container.setLayout(layout)

        if is_directory == 1:  # 如果是目录
            # 查找目录中的所有图片
            all_images = self.find_all_images(path)
            
            # 按文件名排序，确保顺序一致
            all_images.sort()
            
            # 获取封面图片路径
            cover_path = self.find_cover_image(path)
            
            # === 新增：MD5指纹去重逻辑 ===
            unique_images = []
            seen_md5s = set()
            
            # 首先计算封面图片的MD5（如果存在）
            cover_md5 = None
            if cover_path and os.path.exists(cover_path):
                try:
                    with open(cover_path, 'rb') as f:
                        file_hash = hashlib.md5()
                        while chunk := f.read(8192):
                            file_hash.update(chunk)
                        cover_md5 = file_hash.hexdigest()
                except Exception as e:
                    print(f"[WARNING] 计算封面图片MD5失败 {cover_path}: {e}")
            
            for img in all_images:
                # 使用绝对路径比较，确保封面图片不会被包含在其他缩略图中
                if cover_path and os.path.abspath(img) == os.path.abspath(cover_path):
                    continue  # 跳过封面图片
                
                # 计算图片的MD5指纹
                try:
                    with open(img, 'rb') as f:
                        file_hash = hashlib.md5()
                        while chunk := f.read(8192):
                            file_hash.update(chunk)
                        md5_value = file_hash.hexdigest()
                    
                    # 如果这个MD5值与封面图片相同，跳过
                    if cover_md5 and md5_value == cover_md5:
                        print(f"[DEBUG] 跳过与封面相同的图片: {img} (MD5指纹相同)")
                        continue
                    
                    # 如果这个MD5值还没出现过，添加到唯一列表
                    if md5_value not in seen_md5s:
                        seen_md5s.add(md5_value)
                        unique_images.append(img)
                    else:
                        print(f"[DEBUG] 跳过重复图片: {img} (MD5指纹相同)")
                        
                except Exception as e:
                    # 如果计算MD5失败，仍然保留该图片
                    print(f"[WARNING] 计算MD5失败 {img}: {e}")
                    unique_images.append(img)
            
            # 限制最大显示缩略图数量为8个
            max_thumbnails = min(len(unique_images), 8)  # 最多显示8个其他缩略图
            
            # === 修复：存储图片路径到widget属性中 ===
            container.thumbnail_paths = unique_images[:max_thumbnails]  # 存储缩略图路径
            
            for i in range(max_thumbnails):
                thumb_label = QLabel()
                thumb_label.setFixedSize(180, 120)  # 跟封面一样的尺寸
                thumb_label.setAlignment(Qt.AlignCenter)
                thumb_label.setCursor(Qt.PointingHandCursor)  # 添加手型光标
            
                if i < len(unique_images):
                    self.set_preview_image(thumb_label, unique_images[i])
                    # 为缩略图设置点击事件 - 使用正确的方法
                    thumb_label.mousePressEvent = self.create_thumbnail_click_handler(unique_images[i])
                else:
                    thumb_label.setText("")
                
                layout.addWidget(thumb_label)
        
            # 如果还有其他图片但被限制了显示，显示提示信息
            if len(unique_images) > max_thumbnails:
                more_label = QLabel(f"+{len(unique_images) - max_thumbnails}更多")
                more_label.setAlignment(Qt.AlignCenter)
                more_label.setStyleSheet("color: #666; font-size: 12px;")
                layout.addWidget(more_label)

        else:  # 如果是文件
            # 单个文件不需要其他缩略图
            pass
        
        return container





    def find_all_images(self, directory):
        """查找目录中的所有图片文件（按文件名排序）"""
        if not os.path.isdir(directory):
            return []
        
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
        images = []
        
        try:
            # 只查找当前目录下的图片文件，不递归子目录
            for file in os.listdir(directory):
                full_path = os.path.join(directory, file)
                if os.path.isfile(full_path) and any(file.lower().endswith(ext) for ext in image_extensions):
                    images.append(full_path)
            
            # 按文件名排序，确保封面和缩略图顺序一致
            images.sort()
            
            
        except PermissionError:
            pass
        
        return images







    def copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.update_status_bar("路径已复制到剪贴板", 2000)

    def filter_directories(self):
        if not hasattr(self, 'table_widget'):
            return
        
        search_text = self.search_input.text().lower().strip()
        
        if not search_text:
            # 如果没有搜索文本，显示所有行
            for row in range(self.table_widget.rowCount()):
                self.table_widget.setRowHidden(row, False)
            self.statusBar().showMessage(f"显示 {self.table_widget.rowCount()} 个项目")
            return
        
        visible_count = 0
        for row in range(self.table_widget.rowCount()):
            # 获取名称和路径进行比较
            name_item = self.table_widget.item(row, 1)  # 第二列是目录名称
            path_item = self.table_widget.item(row, 4)  # 第五列是目录地址
            
            name = name_item.text() if name_item else ""
            path = path_item.text() if path_item else ""
            
            # 新的搜索逻辑：支持拼音首字母搜索
            match = False
            
            # 1. 首先检查普通文本匹配
            if search_text in name.lower() or search_text in path.lower():
                match = True
            else:
                # 2. 如果普通文本不匹配，尝试拼音首字母匹配
                if PinyinSearchHelper.contains_pinyin_initials(name, search_text):
                    match = True
                else:
                    # 3. 检查路径的拼音首字母匹配
                    if PinyinSearchHelper.contains_pinyin_initials(path, search_text):
                        match = True
            
            self.table_widget.setRowHidden(row, not match)
            
            if match:
                visible_count += 1
        
        self.statusBar().showMessage(f"显示 {visible_count} 个匹配项目")





    
    def show_settings(self):
        if not self.user_manager.current_user:
            QMessageBox.warning(self, "未登录", "请先登录用户")
            return
        
        dialog = SettingsDialog(self.user_manager, self)
        if dialog.exec_() == QDialog.Accepted:
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

        return issues


    def get_setting(self, key, default=None):
        """安全获取设置值"""
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


    
    def manual_backup(self):
        if not self.user_manager.current_db_path:
            QMessageBox.warning(self, "未登录", "请先登录用户")
            return
        
        success, result = self.backup_manager.create_backup(self.user_manager.current_db_path, "manual")
        if success:
            QMessageBox.information(self, "备份成功", f"数据库已成功备份到:\n{result}")
        else:
            QMessageBox.critical(self, "备份失败", f"备份数据库时出错:\n{result}")
    
    def show_restore_dialog(self):
        if not self.user_manager.current_db_path:
            QMessageBox.warning(self, "未登录", "请先登录用户")
            return
        
        dialog = RestoreDatabaseDialog(self.backup_manager, self.user_manager.current_db_path, self)
        if dialog.exec_() == QDialog.Accepted:
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
        print(f"[DEBUG] 使用扫描模式: {scan_mode}")

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
                        
                        # 如果是空目录，跳过不添加到列表
                        if not visible_contents:
                            print(f"[DEBUG] 跳过空白目录: {current_path}")
                            should_add = False
                    except (PermissionError, FileNotFoundError):
                        # 如果无法访问目录内容，也跳过
                        print(f"[DEBUG] 跳过无法访问的目录: {current_path}")
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
                    else:
                        print(f"[DEBUG] 跳过空名称或空路径的项: 名称='{name}', 路径='{current_path}'")
                
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

    def safe_load_and_scale_image(self, image_path, target_width=180, target_height=120):
        """安全加载和缩放图片，确保参数类型正确"""
        try:
            # 参数验证
            if not image_path or not os.path.exists(image_path):
                return None
                
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
            
            # 缩放图片，保持宽高比
            scaled_pixmap = pixmap.scaled(
                target_size, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
        
            # === 新增：确保图片数据正确释放 ===
            # 强制垃圾回收以释放图片资源
            del pixmap
            import gc
            gc.collect()
        
            return scaled_pixmap
            
        except Exception as e:
            print(f"[ERROR] 安全加载图片失败: {e}")
            return None

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







    
    def find_cover_image(self, directory):
        """查找目录中的封面图片：优先使用保存的封面，然后使用目录中的图片"""
        if not os.path.isdir(directory):
            return None

        # === 新增：首先检查是否有保存的封面 ===
        saved_cover_path = self.get_saved_cover_path(directory)
        if saved_cover_path and os.path.exists(saved_cover_path):
            return saved_cover_path
            
        # 1. 首先查找 cover.* 文件
        cover_patterns = ['cover.*', '封面.*', 'Cover.*', 'COVER.*']
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
        
        for pattern in cover_patterns:
            for ext in image_extensions:
                # 查找匹配模式的文件
                search_pattern = pattern.replace('*', ext)
                for file in glob.glob(os.path.join(directory, search_pattern)):
                    if os.path.isfile(file):
                        return file  # 找到 cover.* 文件，直接返回
        
        # 2. 如果没有找到 cover.* 文件，则使用目录中的第一张图片
        try:
            # 获取目录中的所有图片文件，按文件名排序
            files = []
            for file in os.listdir(directory):
                full_path = os.path.join(directory, file)
                if os.path.isfile(full_path) and any(file.lower().endswith(ext) for ext in image_extensions):
                    files.append(full_path)
            
            # 按文件名排序，确保顺序一致
            files.sort()
            
            # 返回第一张图片作为封面
            if files:
                return files[0]
            else:
                return None
                
        except (PermissionError, FileNotFoundError):
            return None


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
        dialog.exec_()

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
        dialog.exec_()

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
            screen_geometry = QApplication.desktop().availableGeometry()
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
            dialog.exec_()
            
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

    def save_cover_image(self, directory_path, cover_image_path):
        """增强的封面图片保存方法"""
        if not cover_image_path or not os.path.exists(cover_image_path):
            print(f"[DEBUG] 封面图片不存在: {cover_image_path}")
            return False

        # === 新增：检查目录是否为空或没有图片 ===
        if not self.has_images_in_directory(directory_path):
            print(f"[DEBUG] 跳过空白目录或没有图片的目录: {directory_path}")
            return False

        # 检查并确保保存目录
        success, cover_save_dir = self.ensure_cover_save_directory()
        if not success:
            print(f"[DEBUG] 封面保存目录准备失败: {cover_save_dir}")
            return False
        
        cover_save_mode = self.get_setting('cover_save_mode', 'smart')

        # === 新增：检查是否开启"封面备份存在则跳过" ===
        skip_existing = self.get_setting('skip_existing_covers', '1') == '1'

        # 获取目录名称
        dir_name = os.path.basename(directory_path)
        
        try:
            # 根据模式确定保存路径
            if cover_save_mode == 'smart':
                # 智能模式：检查是否符合AV格式
                if self.is_av_format(dir_name):
                    save_path = self.get_series_save_path(dir_name, cover_save_dir, cover_image_path)
                else:
                    save_path = self.get_first_char_save_path(dir_name, cover_save_dir, cover_image_path)
            
            elif cover_save_mode == 'series':
                save_path = self.get_series_save_path(dir_name, cover_save_dir, cover_image_path)
            
            elif cover_save_mode == 'first_char':
                save_path = self.get_first_char_save_path(dir_name, cover_save_dir, cover_image_path)
            
            else:
                # 默认使用智能模式
                if self.is_av_format(dir_name):
                    save_path = self.get_series_save_path(dir_name, cover_save_dir, cover_image_path)
                else:
                    save_path = self.get_first_char_save_path(dir_name, cover_save_dir, cover_image_path)
            
            if not save_path:
                print(f"[DEBUG] 无法生成保存路径: {dir_name}")
                return False

            # === 新增：检查封面是否已存在，如果存在且开启跳过选项，则直接返回 ===
            if skip_existing and os.path.exists(save_path):
                # === 新增：检查MD5是否相同 ===
                if self.is_same_image_by_md5(cover_image_path, save_path):
                    print(f"[DEBUG] 封面已存在且MD5相同，跳过保存: {save_path}")
                    return True  # 返回True表示"跳过"是预期行为
                else:
                    print(f"[DEBUG] 封面已存在但MD5不同，继续保存: {save_path}")
                    # MD5不同，继续保存流程
            
            # 确保目标目录存在
            target_dir = os.path.dirname(save_path)
            os.makedirs(target_dir, exist_ok=True)
            
            # 复制封面图片
            if not os.path.exists(save_path):
                shutil.copy2(cover_image_path, save_path)
                print(f"[DEBUG] 封面保存成功: {save_path}")
                return True
            else:
                # 如果文件已存在但MD5不同，覆盖保存
                shutil.copy2(cover_image_path, save_path)
                print(f"[DEBUG] 封面已存在但MD5不同，已覆盖保存: {save_path}")
                return True
                    
        except Exception as e:
            print(f"[ERROR] 保存封面图片失败: {e}")
            print(f"[DEBUG] 目录: {directory_path}")
            print(f"[DEBUG] 封面源: {cover_image_path}")
            print(f"[DEBUG] 目标路径: {save_path if 'save_path' in locals() else 'N/A'}")
        
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

    def batch_save_all_covers(self):
        """为所有已扫描目录批量保存封面图片 - 增强版本"""
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
                                Qt.QueuedConnection,
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
        if QThread.currentThread() != self.thread():
            QMetaObject.invokeMethod(self.statusBar(), "showMessage",
                                Qt.QueuedConnection,
                                Q_ARG(str, message),
                                Q_ARG(int, timeout))
        else:
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

    from PyQt5.QtCore import pyqtSlot
    
    # 在 DirectoryScannerApp 类中的 open_directory 方法前添加：
    @pyqtSlot(str)
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
        """初始化服务器"""
        self.server = DirectoryScannerServer(self, host='0.0.0.0', port=8080)
        self.server_status = False

    def toggle_server(self):
        """切换服务器状态"""
        if not hasattr(self, 'server'):
            self.init_server()
        
        if self.server_status:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        """启动服务器"""
        if hasattr(self, 'server') and self.server.start():
            self.server_status = True

            self.update_server_status_display()

            self.server_action.setText("停止Web服务器")
            self.server_action.setIcon(QIcon.fromTheme("network-server"))
            
            server_url = self.server.get_server_url()
            self.update_status_bar(f"Web服务器已启动: {server_url}", 5000)
            
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
            self.server_action.setText("启动Web服务器")
            self.server_action.setIcon(QIcon.fromTheme("network-server"))
            self.statusBar().showMessage("Web服务器已停止")
            self.update_server_status_display()
            self.update_status_bar("Web服务器已停止", 3000)

    def show_server_info(self):
        """显示服务器信息"""
        if not self.server_status:
            return
        
        server_url = self.server.get_server_url()
        
        message = f"""
    Web服务器已启动！

    访问地址: {server_url}

    功能特性:
    • 📁 查看所有目录和文件
    • 🔍 搜索目录（支持拼音首字母）
    • 🖼️ 查看封面图片
    • 📂 一键打开目录
    • 🔄 远程扫描目录
    • 📱 响应式设计，支持手机访问

    注意:
    • 服务器运行在: {server_url}
    • 同一网络下的其他设备也可以访问
    • 点击"停止Web服务器"可关闭服务
    """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Web服务器信息")
        msg_box.setText(message)
        msg_box.addButton("复制访问地址", QMessageBox.ActionRole)
        msg_box.addButton("在浏览器中打开", QMessageBox.ActionRole)
        msg_box.addButton("确定", QMessageBox.AcceptRole)
        
        result = msg_box.exec_()
        
        if result == 0:  # 复制访问地址
            QApplication.clipboard().setText(server_url)
            self.statusBar().showMessage("访问地址已复制到剪贴板")
        elif result == 1:  # 在浏览器中打开
            import webbrowser
            webbrowser.open(server_url)

    def closeEvent(self, event):
        """重写关闭事件，确保服务器正确停止"""
        if hasattr(self, 'server') and self.server_status:
            self.stop_server()
        event.accept()



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
            self.server_action.setText("停止Web服务器")
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
            self.server_action.setText("启动Web服务器")
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
        """根据当前操作系统规范化路径分隔符"""
        if not path:
            return path
        
        if sys.platform == "win32":
            # Windows 使用反斜杠
            return path.replace('/', '\\')
        else:
            # Linux/macOS 使用正斜杠
            return path.replace('\\', '/')

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
    
    # 初始化服务器（但不自动启动）
    window.init_server()
    
    sys.exit(app.exec_())
