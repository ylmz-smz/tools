#!/bin/bash

# 创建虚拟环境（可选）
echo "创建Python虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 检查安装结果
echo "检查安装..."
python -c "import requests, prettytable, yaml, urllib3; print('依赖安装成功!')"

echo "安装完成！可以通过以下命令运行程序："
echo "python train_ticket_monitor.py" 