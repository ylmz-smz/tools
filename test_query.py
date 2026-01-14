#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试查询车次"""

import sys
import json
from train_ticket_monitor import TrainTicketMonitor
import yaml

# 加载配置
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 创建监控器实例
monitor = TrainTicketMonitor()

# 登录
login_config = config.get('login_config', {})
cookie_config = login_config.get('cookie_login', {})

if cookie_config.get('enabled'):
    print("使用Cookie登录...")
    if monitor.login_with_cookie(cookie_config):
        print("✓ 登录成功")
    else:
        print("✗ 登录失败")
        sys.exit(1)

# 获取查询参数
query_params = config.get('query_params', {})
from_station = query_params.get('from_station', '太子城')
to_station = query_params.get('to_station', '清河')
train_date = query_params.get('train_date', '2026-01-18')

print(f"\n查询 {from_station} 到 {to_station} 在 {train_date} 的所有车次：\n")

# 查询所有车次（不过滤）
tickets = monitor.query_tickets(from_station, to_station, train_date, train_codes=None)

if tickets:
    print(f"\n找到 {len(tickets)} 趟车次：")
    for ticket in tickets:
        print(f"  车次: {ticket['train_code']}")
        print(f"    出发时间: {ticket['departure_time']}")
        print(f"    到达时间: {ticket['arrival_time']}")
        print(f"    历时: {ticket['duration']}")
        print(f"    座位情况:")
        for seat_type, count in ticket['seats'].items():
            if count and count != '--':
                print(f"      {seat_type}: {count}")
        print()
else:
    print("未找到任何车次")
