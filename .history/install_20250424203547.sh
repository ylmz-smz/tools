#!/bin/bash

# 确保脚本在错误时退出
set -e

echo "开始安装 12306 车票查询工具..."

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装 Python3"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo "升级 pip..."
python3 -m pip install --upgrade pip

# 安装依赖
echo "安装依赖..."
python3 -m pip install -r requirements.txt

# 检查安装是否成功
echo "检查安装..."
python3 -c "import requests, prettytable, yaml, urllib3; print('依赖安装成功!')"

echo "安装完成！"
echo "使用方法："
echo "1. 首先激活虚拟环境：source venv/bin/activate"
echo "2. 运行程序：python3 train_ticket_monitor.py" 