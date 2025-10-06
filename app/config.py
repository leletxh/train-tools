# -*- coding: utf-8 -*-
"""
应用配置模块
"""

import os


class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key_here'
    JSON_AS_ASCII = False
    
    # 系统配置
    OPEN_HISTORY_LOG = True
    FILE_TREE_FILTER = True
    ENV_DIR_NAME = ".conda"
    
    # 默认路径配置
    DEFAULT_LOG_PATH = "logs"
    DEFAULT_PORT = "5000"


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
