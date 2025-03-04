@echo off
echo 创建Python虚拟环境...
python -m venv venv
call venv\Scripts\activate.bat

echo 安装依赖...
pip install -r requirements.txt

echo 检查安装...
python -c "import requests, prettytable, yaml, urllib3; print('依赖安装成功!')"

echo 安装完成！可以通过以下命令运行程序：
echo python train_ticket_monitor.py
pause 