#!/usr/bin/env python
"""
ClassAudio 快捷启动入口
运行此文件即可启动整个系统
"""
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 导入并运行 launcher
from scripts.launcher import main

if __name__ == "__main__":
    main()
