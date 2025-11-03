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
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QDialog, QComboBox, QSpinBox, 
                             QCheckBox, QFileDialog, QTabWidget, QGridLayout, QGroupBox,
                             QDateEdit, QToolButton, QSizePolicy, QStackedWidget, QAction,
                             QMenu, QSystemTrayIcon, QScrollArea, QInputDialog, QFrame, 
                             QTextEdit, QProgressDialog, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, QDateTime, QSize, QSettings, pyqtSignal
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
    VERSION = "2.42.0"
    BUILD_DATE = "2025-11-03"
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
    HELP_TEXT = """
使用说明:

版本: 2.42.0
作者: 杜玛

主要功能:
1. 多用户目录管理 - 支持多个用户独立管理各自的目录
2. 智能拼音搜索 - 支持中文拼音首字母搜索
3. 自动备份恢复 - 定期自动备份数据库，支持手动恢复
4. 图片预览功能 - 自动识别并预览目录中的图片
5. 可配置扫描 - 支持设置扫描深度和过滤条件
6. 主目录管理 - 支持管理多个主目录并分别设置扫描深度

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

技术支持: https://github.com/duma520
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
                    is_directory INTEGER DEFAULT 1  -- 添加这个新列，默认为1表示是目录
                )
            """)

            # 检查并添加缺失的列（防御性编程）
            cursor.execute("PRAGMA table_info(directories)")
            columns = [column[1] for column in cursor.fetchall()]
            
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
        cover_save_mode = self.get_setting('cover_save_mode', 'smart')

        if hasattr(self, 'parent') and self.parent():
            self.parent().batch_save_missing_covers()


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
    
    def init_ui(self):
        # self.setWindowTitle("目录扫描管理系统")
        self.setWindowTitle(f"{ProjectInfo.NAME} {ProjectInfo.VERSION} (Build: {ProjectInfo.BUILD_DATE})")
        self.setMinimumSize(800, 600)
        self.resize(800, 600)
        
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
        
        # 加载用户设置
        self.load_user_settings()
    
    def show_user_manager(self):
        dialog = UserManagerDialog(self.user_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            # 用户已登录，加载用户数据
            self.load_user_settings()
            self.load_directories()

            # 延迟启动自动扫描，避免登录后立即扫描造成卡顿
            QTimer.singleShot(3000, self.start_auto_scan)  # 延迟3秒启动
            print(f"[DEBUG] 用户 {self.user_manager.current_user} 已登录，加载用户数据完成")    
            self.statusBar().showMessage("登录成功，界面已就绪")

            # 启动自动扫描定时器
            self.start_auto_scan()
    
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
        self.main_directory = path
        self.dir_label.setText(f"主目录: {path}")
        
        # 获取当前用户的扫描模式设置
        scan_mode = "directories"  # 默认值
        if self.user_manager.current_db_path:
            conn = sqlite3.connect(self.user_manager.current_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'scan_mode'")
        result = cursor.fetchone()
        if result:
            scan_mode = result[0]
        
        # === 新增：显示进度条 ===
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"正在扫描目录: {path}...")
        QApplication.processEvents()
        
        try:
            # 传入扫描模式参数
            dirs = self.scan_directory_with_depth(path, depth, scan_mode)
        
            # === 新增：更新进度条 ===
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
                
                for dir_info in dirs:
                    # 更严格的数据验证
                    name = dir_info.get("name", "").strip() if dir_info.get("name") else ""
                    path = dir_info.get("path", "").strip() if dir_info.get("path") else ""
                    
                    # 如果没有目录名称或没有路径，跳过不添加到列表
                    if not name or not path:
                        invalid_dirs_count += 1
                        print(f"[DEBUG] 跳过空名称或空路径的目录: {dir_info}")
                        continue
                    
                    # 其他验证条件
                    if (name and path and
                        dir_info.get("created_time") and dir_info.get("last_modified") and
                        path not in duplicate_paths):  # 防止重复路径
                        
                        # 检查路径是否实际存在
                        if os.path.exists(path):
                            cursor.execute("""
                                INSERT INTO directories 
                                (name, path, created_time, last_modified, directory_exists, last_scanned, is_main_dir, is_directory)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                name,
                                path,
                                dir_info["created_time"],
                                dir_info["last_modified"],
                                1,
                                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                dir_info["is_main_dir"],
                                dir_info["is_directory"]
                            ))
                            valid_dirs_count += 1
                            duplicate_paths.add(path)  # 记录已处理的路径
                        else:
                            invalid_dirs_count += 1
                            print(f"[DEBUG] 跳过不存在的路径: {path}")
                    else:
                        invalid_dirs_count += 1
                        print(f"[DEBUG] 跳过无效数据: {dir_info}")
                
                conn.commit()
                
                # === 新增：更新进度条 ===
                self.progress_bar.setValue(75)
                self.progress_label.setText("正在创建备份...")
                QApplication.processEvents()
                
                # 创建备份
                self.backup_manager.create_backup(self.user_manager.current_db_path)

                # 保存主目录设置
                self.save_main_directory_settings()
            
                # === 新增：更新进度条 ===
                self.progress_bar.setValue(90)
                self.progress_label.setText("正在保存封面图片...")
                QApplication.processEvents()

                # === 改进：每次扫描都保存/更新封面图片 ===
                # 检查是否开启了"扫描时保存封面"选项
                scan_save_cover = self.get_setting('scan_save_cover', '0') == '1'
                cover_save_mode, cover_save_dir = self.get_cover_save_settings()
                
                if scan_save_cover and cover_save_dir:  # 只有在开启了选项且设置了保存目录时才保存封面
                    saved_count = 0
                    total_dirs = len([d for d in dirs if d.get("is_directory", 1) == 1])

                    for i, dir_info in enumerate(dirs):                    
                        if dir_info.get("is_directory", 1) == 1:  # 只处理目录
                            dir_path = dir_info["path"]
                            if os.path.exists(dir_path):
                                cover_path = self.find_cover_image(dir_path)
                                if cover_path:
                                    if self.save_cover_image(dir_path, cover_path):
                                        saved_count += 1

                            # === 新增：更新封面保存进度 ===
                            if total_dirs > 0:
                                progress_value = 90 + int((i + 1) / total_dirs * 10)
                                self.progress_bar.setValue(progress_value)
                                self.progress_label.setText(f"正在保存封面图片... ({i+1}/{total_dirs})")
                                QApplication.processEvents()
                
                    if saved_count > 0:
                        self.statusBar().showMessage(f"扫描完成，保存了 {saved_count} 个封面")
            
                # === 新增：完成进度 ===
                self.progress_bar.setValue(100)
                self.progress_label.setText("扫描完成")
                
                # 显示扫描统计信息
                stats_msg = f"扫描完成: {valid_dirs_count} 个有效目录"
                if invalid_dirs_count > 0:
                    stats_msg += f", {invalid_dirs_count} 个无效目录被跳过"
                self.statusBar().showMessage(stats_msg)

        except Exception as e:
            # === 新增：扫描失败时更新进度条 ===
            self.progress_bar.setValue(0)
            self.progress_label.setText("扫描失败")
            self.statusBar().showMessage("扫描失败")
            QMessageBox.critical(self, "扫描错误", f"扫描目录时出错:\n{e}")
            print(f"[ERROR] 扫描错误: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
        
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
        
        # === 新增：多目录扫描进度显示 ===
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"准备扫描 {len(main_dirs)} 个主目录...")
        QApplication.processEvents()
        
        # 扫描每个主目录
        for i, dir_info in enumerate(main_dirs):
            dir_id, path, depth = dir_info  # 获取已保存的扫描深度
            
            # 更新进度
            progress_value = int((i) / len(main_dirs) * 100)
            self.progress_bar.setValue(progress_value)
            self.progress_label.setText(f"正在扫描: {os.path.basename(path)}... ({i+1}/{len(main_dirs)})")
            QApplication.processEvents()
            
            # 调用扫描单个主目录的方法
            self.scan_single_main_directory(path, depth)
        
        # 加载最新的目录列表
        self.load_directories()
        
        # === 新增：完成多目录扫描 ===
        self.progress_bar.setValue(100)
        self.progress_label.setText("所有主目录扫描完成")
        self.statusBar().showMessage("所有主目录扫描完成")
        
        # 2秒后隐藏进度条
        QTimer.singleShot(2000, self.hide_progress_bar)

    




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
                
                # 第五列：目录地址
                path_item = QTableWidgetItem(path)
                path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
                self.table_widget.setItem(row_idx, 4, path_item)
            
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
            
            # 过滤掉封面图片
            other_images = []
            for img in all_images:
                # 使用绝对路径比较，确保封面图片不会被包含在其他缩略图中
                if cover_path and os.path.abspath(img) == os.path.abspath(cover_path):
                    continue  # 跳过封面图片
                other_images.append(img)
            
            max_thumbnails = len(other_images)
            
            for i in range(max_thumbnails):
                thumb_label = QLabel()
                thumb_label.setFixedSize(180, 120)  # 跟封面一样的尺寸
                thumb_label.setAlignment(Qt.AlignCenter)
                thumb_label.setCursor(Qt.PointingHandCursor)  # 添加手型光标，提示可点击
            
                if i < len(other_images):
                    self.set_preview_image(thumb_label, other_images[i])
                    # 为缩略图设置点击事件
                    thumb_label.mousePressEvent = lambda event, img_path=other_images[i]: self.on_image_clicked(event, img_path)
                else:
                    thumb_label.setText("")
                
                layout.addWidget(thumb_label)
        
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
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.statusBar().showMessage("路径已复制到剪贴板", 2000)

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
        
        # 安全停止现有定时器
        if self.scan_timer.isActive():
            self.scan_timer.stop()
            print("[DEBUG] 已停止现有的自动扫描定时器")
        
        # 获取设置值
        interval, auto_scan = self.get_auto_scan_settings()
        
        if auto_scan:
            try:
                self.scan_timer.start(interval)
                print(f"[SUCCESS] 自动扫描定时器已启动，间隔: {interval/1000}秒")
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
                        for entry in os.listdir(current_path):
                            full_path = os.path.join(current_path, entry)
                            # 过滤掉隐藏文件和系统文件
                            if not entry.startswith('.') and not entry.startswith('~'):
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
        
        version_label = QLabel(f"版本: {about_info['version']} | 构建日期: {about_info['build_date']}")
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
        """为所有图片设置点击事件"""
        if not hasattr(self, 'table_widget'):
            return
        
        for row in range(self.table_widget.rowCount()):
            # 封面图片点击事件
            cover_widget = self.table_widget.cellWidget(row, 0)
            if cover_widget and isinstance(cover_widget, QLabel):
                # 获取该行的路径信息
                path_item = self.table_widget.item(row, 4)
                if path_item:
                    path = path_item.text()
                    is_directory_item = self.table_widget.item(row, 1)  # 假设第二列有目录信息
                    
                    if is_directory_item:
                        # 如果是目录，查找封面图片路径
                        cover_path = self.find_cover_image(path)
                        if cover_path:
                            # 移除原有的事件过滤器（如果有）
                            cover_widget.mousePressEvent = lambda event, img_path=cover_path: self.on_image_clicked(event, img_path)
            
            # 其他缩略图点击事件 - 修复索引计算问题
            thumbnails_widget = self.table_widget.cellWidget(row, 2)
            if thumbnails_widget:
                # 查找所有缩略图标签
                for i in range(thumbnails_widget.layout().count()):
                    thumb_label = thumbnails_widget.layout().itemAt(i).widget()
                    if thumb_label and isinstance(thumb_label, QLabel):
                        # 获取该缩略图对应的图片路径
                        path_item = self.table_widget.item(row, 4)
                        if path_item:
                            path = path_item.text()
                            # 查找该目录中的所有图片
                            all_images = self.find_all_images(path)
                            
                            # 获取封面图片路径
                            cover_path = self.find_cover_image(path)
                            
                            # 过滤掉封面图片，获取其他图片列表
                            other_images = []
                            for img in all_images:
                                if cover_path and os.path.abspath(img) == os.path.abspath(cover_path):
                                    continue  # 跳过封面图片
                                other_images.append(img)
                            
                            # 按文件名排序确保顺序一致
                            other_images.sort()
                            
                            # 修复：确保索引正确对应
                            if i < len(other_images):
                                img_path = other_images[i]
                                # 使用闭包确保每个缩略图都有正确的图片路径
                                thumb_label.mousePressEvent = lambda event, img_path=img_path, row=row, idx=i: self.on_thumbnail_clicked(event, img_path, row, idx)



    def on_image_clicked(self, event, image_path):
        """处理图片点击事件"""
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
                print(f"[DEBUG] 封面已存在，跳过保存: {save_path}")
                return True  # 返回True表示"跳过"是预期行为
        
            # 确保目标目录存在
            target_dir = os.path.dirname(save_path)
            os.makedirs(target_dir, exist_ok=True)
            
            # 复制封面图片
            if not os.path.exists(save_path):
                shutil.copy2(cover_image_path, save_path)
                print(f"[DEBUG] 封面保存成功: {save_path}")
                return True
            else:
                print(f"[DEBUG] 封面已存在: {save_path}")
                return True  # 已存在也算成功
                
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
                
                if os.path.exists(dir_path):
                    cover_path = self.find_cover_image(dir_path)
                    if cover_path and os.path.exists(cover_path):
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
            
            QMessageBox.information(self, "批量保存完成", result_msg)
            self.statusBar().showMessage(f"批量保存完成 - 成功 {saved_count} 个目录")
            
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
            
            QMessageBox.information(self, "保存完成", f"成功保存 {saved_count} 个缺失封面")
            self.statusBar().showMessage(f"缺失封面保存完成 - 成功 {saved_count} 个")
            
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
    
    sys.exit(app.exec_())
