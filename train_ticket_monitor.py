import requests
import time
import json
import datetime
import platform
from prettytable import PrettyTable
import os
import yaml  # 需要安装 pyyaml 库
import random
import urllib3
import argparse

# PushPlus 推送配置
PUSHPLUS_TOKEN = "30e6fd60c6174936be254e678f9b7bfa"
PUSHPLUS_URL = "http://www.pushplus.plus/send"

# 根据操作系统选择提醒方式
system = platform.system()
if system == 'Windows':
    import winsound
elif system == 'Darwin':  # macOS
    import os
    def play_alert():
        os.system('afplay /System/Library/Sounds/Ping.aiff')
    
    def show_notification(title, message):
        """在 macOS 上显示通知"""
        os_command = f'''
        osascript -e 'display notification "{message}" with title "{title}"'
        '''
        os.system(os_command)
else:  # Linux 或其他系统
    import os
    def play_alert():
        os.system('echo -e "\a"')  # 使用终端响铃
    
    def show_notification(title, message):
        """尝试在 Linux 上显示通知（如果安装了 notify-send）"""
        os.system(f'notify-send "{title}" "{message}"')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TrainTicketMonitor:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        self.proxies = None
        self.is_logged_in = False
        self.username = None
        # PushPlus 推送状态跟踪
        self.train_found_notified = set()  # 已通知发现的车次
        self.train_available_notified = set()  # 已通知有票的车次
        
    def set_proxy(self, proxy=None):
        """设置代理"""
        if proxy:
            self.proxies = {
                'http': proxy,
                'https': proxy
            }
            print(f"已设置代理: {proxy}")
        else:
            self.proxies = None
    
    def push_notification(self, title, content, template="html"):
        """通过 PushPlus 发送微信推送通知
        
        Args:
            title: 消息标题
            content: 消息内容（支持HTML格式）
            template: 模板类型，默认html，可选 txt/html/json/markdown
        
        Returns:
            bool: 推送是否成功
        """
        try:
            data = {
                "token": PUSHPLUS_TOKEN,
                "title": title,
                "content": content,
                "template": template
            }
            response = requests.post(PUSHPLUS_URL, json=data, timeout=10)
            result = response.json()
            
            if result.get("code") == 200:
                print(f"✓ PushPlus推送成功: {title}")
                return True
            else:
                print(f"✗ PushPlus推送失败: {result.get('msg', '未知错误')}")
                return False
        except Exception as e:
            print(f"✗ PushPlus推送异常: {e}")
            return False
    
    def notify_train_found(self, train_info, from_station, to_station, train_date):
        """推送发现指定车次的通知（每个车次只推送一次）
        
        Args:
            train_info: 车次信息字典
            from_station: 出发站
            to_station: 到达站
            train_date: 出发日期
        """
        train_code = train_info['train_code']
        
        # 检查是否已经通知过
        if train_code in self.train_found_notified:
            return
        
        title = f"🚄 发现车次 {train_code}"
        content = f"""
        <h3>车次信息</h3>
        <p><b>车次:</b> {train_code}</p>
        <p><b>日期:</b> {train_date}</p>
        <p><b>区间:</b> {from_station} → {to_station}</p>
        <p><b>发车时间:</b> {train_info['departure_time']}</p>
        <p><b>到达时间:</b> {train_info['arrival_time']}</p>
        <p><b>历时:</b> {train_info['duration']}</p>
        <hr>
        <h4>座位情况</h4>
        <ul>
            <li>商务座: {train_info['seats'].get('商务座', '--')}</li>
            <li>一等座: {train_info['seats'].get('一等座', '--')}</li>
            <li>二等座: {train_info['seats'].get('二等座', '--')}</li>
            <li>硬卧: {train_info['seats'].get('硬卧', '--')}</li>
            <li>软卧: {train_info['seats'].get('软卧', '--')}</li>
            <li>硬座: {train_info['seats'].get('硬座', '--')}</li>
            <li>无座: {train_info['seats'].get('无座', '--')}</li>
        </ul>
        <p style="color: gray; font-size: 12px;">发现时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        if self.push_notification(title, content):
            self.train_found_notified.add(train_code)
    
    def notify_ticket_available(self, train_info, from_station, to_station, train_date, available_seats):
        """推送有票通知（每个车次只推送一次）
        
        Args:
            train_info: 车次信息字典
            from_station: 出发站
            to_station: 到达站
            train_date: 出发日期
            available_seats: 有票的座位类型列表
        """
        train_code = train_info['train_code']
        
        # 检查是否已经通知过
        if train_code in self.train_available_notified:
            return
        
        # 构建有票座位信息
        seats_html = ""
        for seat_type in available_seats:
            count = train_info['seats'].get(seat_type, '--')
            seats_html += f"<li><b style='color: green;'>{seat_type}: {count}</b></li>"
        
        title = f"🎫 有票啦！{train_code} {from_station}→{to_station}"
        content = f"""
        <h2 style="color: red;">🎉 有票提醒！</h2>
        <h3>车次信息</h3>
        <p><b>车次:</b> {train_code}</p>
        <p><b>日期:</b> {train_date}</p>
        <p><b>区间:</b> {from_station} → {to_station}</p>
        <p><b>发车时间:</b> {train_info['departure_time']}</p>
        <p><b>到达时间:</b> {train_info['arrival_time']}</p>
        <p><b>历时:</b> {train_info['duration']}</p>
        <hr>
        <h4 style="color: green;">✅ 有票座位</h4>
        <ul>
            {seats_html}
        </ul>
        <hr>
        <p><a href="https://kyfw.12306.cn/otn/leftTicket/init">👉 点击前往12306购票</a></p>
        <p style="color: gray; font-size: 12px;">检测时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        if self.push_notification(title, content):
            self.train_available_notified.add(train_code)

    def login(self, username, password):
        """登录12306账号
        
        注意：12306的登录流程较为复杂，包含验证码验证等。
        这个简化版本尝试基本的登录流程，但可能需要人工介入处理验证码。
        推荐使用 login_with_cookie() 方法代替。
        """
        try:
            print(f"\n正在尝试登录12306账号: {username}")
            print("注意：账号密码登录通常需要验证码，成功率较低")
            print("推荐使用Cookie登录方式")
            
            # 第一步：访问登录页面，获取必要的cookies
            login_page_url = "https://kyfw.12306.cn/otn/resources/login.html"
            headers = self.headers.copy()
            headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            response = self.session.get(
                login_page_url,
                headers=headers,
                proxies=self.proxies,
                verify=False,
                timeout=15
            )
            
            if response.status_code != 200:
                print(f"访问登录页面失败，状态码: {response.status_code}")
                return False
            
            time.sleep(1)
            
            # 尝试登录
            login_url = "https://kyfw.12306.cn/otn/login/loginAysnSuggest"
            
            login_data = {
                'loginUserDTO.user_name': username,
                'userDTO.password': password,
                'randCode': '',
            }
            
            headers.update({
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'https://kyfw.12306.cn/otn/resources/login.html',
                'Accept': '*/*',
            })
            
            response = self.session.post(
                login_url,
                data=login_data,
                headers=headers,
                proxies=self.proxies,
                verify=False,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('data', {}).get('loginCheck') == 'Y':
                    self.is_logged_in = True
                    self.username = username
                    print("✓ 登录成功！")
                    return True
                else:
                    error_msg = result.get('messages', ['未知错误'])
                    print(f"✗ 登录失败: {error_msg}")
                    print("\n请使用Cookie登录方式（推荐）")
                    return False
            else:
                print(f"✗ 登录请求失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ 登录过程出错: {e}")
            return False
    
    def login_with_cookie(self, cookie_config):
        """使用Cookie登录（推荐方式）
        
        Args:
            cookie_config: Cookie配置字典，包含:
                - cookie_string: 完整的Cookie字符串（优先使用）
                - 或单独的Cookie字段: JSESSIONID, tk, uamtk 等
        """
        try:
            print("\n正在使用Cookie登录...")
            
            # 优先使用完整的cookie_string
            cookie_string = cookie_config.get('cookie_string', '')
            
            if cookie_string and cookie_string.strip():
                # 解析cookie字符串并设置到session
                print("使用完整Cookie字符串登录...")
                cookies = {}
                for item in cookie_string.split(';'):
                    item = item.strip()
                    if '=' in item:
                        key, value = item.split('=', 1)
                        cookies[key.strip()] = value.strip()
                
                # 设置cookies到session
                for key, value in cookies.items():
                    self.session.cookies.set(key, value, domain='.12306.cn')
                
                print(f"已导入 {len(cookies)} 个Cookie")
            else:
                # 使用单独的Cookie字段
                print("使用单独Cookie字段登录...")
                cookie_fields = ['JSESSIONID', 'tk', 'uamtk', 'uamclk', 'route', 
                               'BIGipServerotn', 'BIGipServerpassport']
                
                set_count = 0
                for field in cookie_fields:
                    value = cookie_config.get(field, '')
                    if value and value.strip():
                        self.session.cookies.set(field, value.strip(), domain='.12306.cn')
                        set_count += 1
                
                if set_count == 0:
                    print("✗ 未配置任何有效的Cookie")
                    return False
                
                print(f"已设置 {set_count} 个Cookie字段")
            
            # 验证Cookie是否有效
            print("验证Cookie有效性...")
            if self.check_login_status():
                self.is_logged_in = True
                print("✓ Cookie登录成功！")
                return True
            else:
                print("✗ Cookie无效或已过期，请重新获取")
                print("\n获取Cookie的步骤：")
                print("1. 在浏览器中打开 https://kyfw.12306.cn 并登录")
                print("2. 按F12打开开发者工具")
                print("3. 切换到 Network（网络）标签")
                print("4. 刷新页面，点击任意一个请求")
                print("5. 在请求头(Request Headers)中找到 Cookie")
                print("6. 复制完整的Cookie值到 config.yaml 的 cookie_string 字段")
                return False
                
        except Exception as e:
            print(f"✗ Cookie登录出错: {e}")
            return False
    
    def check_login_status(self):
        """检查当前登录状态"""
        try:
            # 访问一个需要登录的页面来检查状态
            check_url = "https://kyfw.12306.cn/otn/login/checkUser"
            headers = self.headers.copy()
            headers.update({
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'https://kyfw.12306.cn/otn/leftTicket/init',
            })
            
            response = self.session.post(
                check_url,
                headers=headers,
                proxies=self.proxies,
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('data', {}).get('flag'):
                    self.is_logged_in = True
                    print("✓ 当前已登录")
                    return True
            
            self.is_logged_in = False
            return False
            
        except Exception as e:
            print(f"检查登录状态失败: {e}")
            self.is_logged_in = False
            return False
        
    def query_tickets(self, from_station, to_station, train_date, train_codes=None):
        """查询车票信息"""
        # 首先尝试从网页爬取
        tickets = self.query_tickets_from_web(from_station, to_station, train_date, train_codes)
        if tickets:
            return tickets
        
        # 如果网页爬取失败，尝试使用API
        print("从网页爬取失败，尝试使用API...")
        
        # 获取站点代码
        from_code = self.get_station_code(from_station)
        to_code = self.get_station_code(to_station)
        
        if not from_code or not to_code:
            print(f"无法找到站点代码: {from_station} 或 {to_station}")
            return []
            
        # 构建查询URL - 使用最新的12306 API
        # 12306的API可能会变化，这里使用最可能有效的端点
        api_endpoints = [
            f"https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date={train_date}&leftTicketDTO.from_station={from_code}&leftTicketDTO.to_station={to_code}&purpose_codes=ADULT",
            f"https://kyfw.12306.cn/otn/leftTicket/queryZ?leftTicketDTO.train_date={train_date}&leftTicketDTO.from_station={from_code}&leftTicketDTO.to_station={to_code}&purpose_codes=ADULT",
            f"https://kyfw.12306.cn/otn/leftTicket/queryA?leftTicketDTO.train_date={train_date}&leftTicketDTO.from_station={from_code}&leftTicketDTO.to_station={to_code}&purpose_codes=ADULT"
        ]
        
        # 添加更多请求头，模拟真实浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://kyfw.12306.cn/otn/leftTicket/init',
            'Connection': 'keep-alive',
            'sec-ch-ua': '"Google Chrome";v="120", "Chromium";v="120", "Not-A.Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest',
        }
        
        # 添加随机延迟，避免被反爬
        delay = random.uniform(1, 3)
        print(f"随机延迟 {delay:.2f} 秒...")
        time.sleep(delay)
        
        try:
            # 尝试所有API端点
            for endpoint_url in api_endpoints:
                print(f"尝试API端点: {endpoint_url}")
                
                try:
                    # 添加随机延迟，避免请求过于频繁
                    time.sleep(random.uniform(0.5, 1.5))
                    
                    # 发送请求
                    response = self.session.get(
                        endpoint_url, 
                        headers=headers, 
                        timeout=15,
                        proxies=self.proxies,
                        verify=False  # 禁用SSL验证，可能有助于解决某些连接问题
                    )
                    response.raise_for_status()
                    
                    # 打印响应内容以便调试
                    print(f"API响应状态码: {response.status_code}")
                    
                    # 检查响应是否为空
                    if not response.text.strip():
                        print("API返回空响应")
                        continue
                    
                    # 尝试解析JSON
                    try:
                        data = response.json()
                        
                        # 添加调试信息
                        print(f"API返回数据: {json.dumps(data, ensure_ascii=False)[:500]}...")
                        
                        # 检查API返回的数据结构
                        if 'data' in data and 'result' in data['data']:
                            tickets = []
                            for ticket_info in data['data']['result']:
                                ticket_data = ticket_info.split('|')
                                if len(ticket_data) < 34:  # 确保数据完整
                                    continue
                                    
                                train_info = {
                                    'train_code': ticket_data[3],  # 车次
                                    'from_station': ticket_data[6],  # 出发站代码
                                    'to_station': ticket_data[7],  # 到达站代码
                                    'departure_time': ticket_data[8],  # 出发时间
                                    'arrival_time': ticket_data[9],  # 到达时间
                                    'duration': ticket_data[10],  # 历时
                                    'seats': {
                                        '商务座': ticket_data[32] or '--',
                                        '一等座': ticket_data[31] or '--',
                                        '二等座': ticket_data[30] or '--',
                                        '高级软卧': ticket_data[21] or '--',
                                        '软卧': ticket_data[23] or '--',
                                        '动卧': ticket_data[33] or '--',
                                        '硬卧': ticket_data[28] or '--',
                                        '软座': ticket_data[24] or '--',
                                        '硬座': ticket_data[29] or '--',
                                        '无座': ticket_data[26] or '--',
                                    }
                                }
                                
                                # 如果指定了车次，只返回指定车次的信息
                                if train_codes and train_info['train_code'] not in train_codes:
                                    continue
                                    
                                tickets.append(train_info)
                            
                            if tickets:  # 如果找到了票，立即返回
                                return tickets
                            else:
                                print("没有找到符合条件的车次")
                        else:
                            print(f"查询失败，返回数据格式不正确")
                            if 'messages' in data:
                                print(f"错误信息: {data['messages']}")
                            elif 'message' in data:
                                print(f"错误信息: {data['message']}")
                            
                    except json.JSONDecodeError:
                        print("响应不是有效的JSON格式")
                        # 如果响应包含HTML，可能是重定向到登录页面
                        if '<html' in response.text.lower():
                            print("API返回了HTML页面，可能需要登录")
                        continue
                        
                except requests.exceptions.RequestException as e:
                    print(f"请求异常: {e}")
                    continue
            
            print("所有API端点都失败，无法获取车票信息")
            return []
                
        except Exception as e:
            print(f"查询出错: {e}")
            print(f"错误类型: {type(e).__name__}")
            if hasattr(e, 'response') and e.response:
                print(f"响应状态码: {e.response.status_code}")
                print(f"响应内容: {e.response.text[:200]}...")  # 只打印前200个字符
            return []
    
    def get_station_code(self, station_name):
        """获取站点代码"""
        # 尝试从本地缓存获取站点代码
        try:
            with open('station_codes.json', 'r', encoding='utf-8') as f:
                station_codes = json.load(f)
                if station_name in station_codes:
                    return station_codes[station_name]
        except (FileNotFoundError, json.JSONDecodeError):
            # 如果本地缓存不存在或无效，则从12306获取
            try:
                print("正在从12306获取站点代码表...")
                url = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js"
                response = self.session.get(url, headers=self.headers)
                response.raise_for_status()
                
                # 解析站点代码
                station_text = response.text
                station_text = station_text.split('=')[1].strip("';\n")
                stations = station_text.split('@')
                
                station_codes = {}
                for station in stations:
                    if not station:
                        continue
                    parts = station.split('|')
                    if len(parts) >= 5:
                        station_codes[parts[1]] = parts[2]  # 站名:代码
                
                # 保存到本地缓存
                with open('station_codes.json', 'w', encoding='utf-8') as f:
                    json.dump(station_codes, f, ensure_ascii=False, indent=2)
                    
                if station_name in station_codes:
                    return station_codes[station_name]
            except Exception as e:
                print(f"获取站点代码表失败: {e}")
        
        # 如果无法从12306获取，则使用内置的简化站点代码表
        fallback_codes = {
            '北京': 'BJP', '上海': 'SHH', '广州': 'GZQ', '深圳': 'SZQ',
            '杭州': 'HZH', '南京': 'NJH', '武汉': 'WHN', '西安': 'XAY',
            '成都': 'CDW', '重庆': 'CQW', '天津': 'TJP', '长沙': 'CSQ',
            '郑州': 'ZZF', '济南': 'JNK', '青岛': 'QDK', '大连': 'DLT',
            '沈阳': 'SYT', '哈尔滨': 'HBB', '长春': 'CCT',
            '太子城': 'TZC', '清河': 'QIP'
        }
        return fallback_codes.get(station_name)
    
    def has_available_tickets(self, ticket_info, seat_types=None):
        """检查是否有可用票"""
        if not seat_types:
            seat_types = ['二等座', '一等座', '商务座', '硬卧', '软卧', '硬座']
            
        for seat_type in seat_types:
            if seat_type in ticket_info['seats'] and ticket_info['seats'][seat_type] not in ['--', '无']:
                return True
        return False
    
    def monitor_tickets(self, from_station, to_station, train_date, train_codes, seat_types=None, interval=60):
        """监控车票，有票时提醒"""
        # 确保interval是整数
        try:
            interval = int(str(interval).replace('f', '').strip())
        except (ValueError, TypeError):
            print(f"警告: 查询间隔值 '{interval}' 无效，使用默认值60秒")
            interval = 60
        
        print(f"开始监控 {from_station} 到 {to_station} 在 {train_date} 的车票")
        print(f"监控车次: {', '.join(train_codes) if train_codes else '所有车次'}")
        print(f"监控座位类型: {', '.join(seat_types) if seat_types else '所有座位类型'}")
        print(f"检查间隔: {interval}秒")
        print("=" * 50)
        
        while True:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{current_time}] 正在查询...")
            
            tickets = self.query_tickets(from_station, to_station, train_date, train_codes)
            
            if tickets:
                self.display_tickets(tickets)
                
                # 推送发现车次通知（每个车次只推送一次）
                for ticket in tickets:
                    self.notify_train_found(ticket, from_station, to_station, train_date)
                
                # 检查是否有可用票
                available_tickets = []
                for ticket in tickets:
                    if self.has_available_tickets(ticket, seat_types):
                        available_tickets.append(ticket)
                
                if available_tickets:
                    print("\n发现有票！")
                    
                    # 构建通知消息
                    notification_title = f"12306 车票提醒 - {from_station}到{to_station}"
                    notification_message = ""
                    
                    for ticket in available_tickets:
                        ticket_info = f"车次: {ticket['train_code']}, 出发: {ticket['departure_time']}"
                        print(ticket_info)
                        notification_message += ticket_info + "\n"
                        
                        # 获取有票的座位类型
                        available_seat_types = []
                        for seat_type in seat_types if seat_types else ticket['seats'].keys():
                            if ticket['seats'][seat_type] not in ['--', '无']:
                                seat_info = f"  {seat_type}: {ticket['seats'][seat_type]}"
                                print(seat_info)
                                notification_message += seat_info + "\n"
                                available_seat_types.append(seat_type)
                        
                        # 推送有票通知（每个车次只推送一次）
                        self.notify_ticket_available(ticket, from_station, to_station, train_date, available_seat_types)
                    
                    # 发出提醒声音（根据不同操作系统）
                    for _ in range(5):
                        if system == 'Windows':
                            winsound.Beep(1000, 500)
                        else:
                            play_alert()
                        time.sleep(0.5)
                    
                    # 显示系统通知
                    if system == 'Darwin' or system == 'Linux':
                        show_notification(notification_title, notification_message)
                    
                    # 询问是否继续监控
                    choice = input("\n是否继续监控? (y/n): ")
                    if choice.lower() != 'y':
                        print("停止监控")
                        break
            else:
                print("没有查询到符合条件的车次")
            
            print(f"等待 {interval} 秒后重新查询...")
            time.sleep(interval)
    
    def display_tickets(self, tickets):
        """显示车票信息"""
        if not tickets:
            print("没有查询到符合条件的车次")
            return
            
        table = PrettyTable()
        table.field_names = ["车次", "出发时间", "到达时间", "历时", "商务座", "一等座", "二等座", "硬卧", "软卧", "硬座", "无座"]
        
        for ticket in tickets:
            table.add_row([
                ticket['train_code'],
                ticket['departure_time'],
                ticket['arrival_time'],
                ticket['duration'],
                ticket['seats']['商务座'],
                ticket['seats']['一等座'],
                ticket['seats']['二等座'],
                ticket['seats']['硬卧'],
                ticket['seats']['软卧'],
                ticket['seats']['硬座'],
                ticket['seats']['无座']
            ])
        
        print(table)

    def query_tickets_from_web(self, from_station, to_station, train_date, train_codes=None):
        """从12306网页爬取车票信息"""
        # 获取站点代码
        from_code = self.get_station_code(from_station)
        to_code = self.get_station_code(to_station)
        
        if not from_code or not to_code:
            print(f"无法找到站点代码: {from_station} 或 {to_station}")
            return []
        
        # 不再访问init页面，直接调用API
        # 构建API URL (直接跳过网页加载，直接使用API)
        api_url = f"https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date={train_date}&leftTicketDTO.from_station={from_code}&leftTicketDTO.to_station={to_code}&purpose_codes=ADULT"
        
        print(f"访问API: {api_url}")
        
        # 添加更多请求头，模拟真实浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://kyfw.12306.cn/otn/leftTicket/init',
            'Connection': 'keep-alive',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Google Chrome";v="120", "Chromium";v="120", "Not-A.Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        
        try:
            # 添加随机延迟
            delay = random.uniform(1, 3)
            print(f"随机延迟 {delay:.2f} 秒...")
            time.sleep(delay)
            
            # 发送请求 - 直接调用API
            response = self.session.get(
                api_url, 
                headers=headers, 
                timeout=15,
                proxies=self.proxies,
                verify=False
            )
            response.raise_for_status()
            
            # 检查响应是否为JSON
            try:
                data = response.json()
                print(f"API返回数据: {json.dumps(data, ensure_ascii=False)[:500]}...")
            except json.JSONDecodeError:
                # 如果不是JSON，可能是登录页面
                if "请登录" in response.text or "登录名" in response.text or "<title>登录</title>" in response.text:
                    print("需要登录12306账号才能查询车票")
                    return []
                else:
                    print(f"API返回非JSON响应，状态码: {response.status_code}")
                    return []
            
            # 检查API返回结果
            if not data.get('httpstatus') == 200 and not data.get('status'):
                # 可能需要登录或者API返回错误
                if data.get('messages'):
                    print(f"API返回错误: {data.get('messages')}")
                return []
            
            # 检查API返回的数据结构
            if 'data' in data and 'result' in data['data']:
                tickets = []
                for ticket_info in data['data']['result']:
                    ticket_data = ticket_info.split('|')
                    if len(ticket_data) < 34:  # 确保数据完整
                        continue
                        
                    train_info = {
                        'train_code': ticket_data[3],  # 车次
                        'from_station': ticket_data[6],  # 出发站代码
                        'to_station': ticket_data[7],  # 到达站代码
                        'departure_time': ticket_data[8],  # 出发时间
                        'arrival_time': ticket_data[9],  # 到达时间
                        'duration': ticket_data[10],  # 历时
                        'seats': {
                            '商务座': ticket_data[32] or '--',
                            '一等座': ticket_data[31] or '--',
                            '二等座': ticket_data[30] or '--',
                            '高级软卧': ticket_data[21] or '--',
                            '软卧': ticket_data[23] or '--',
                            '动卧': ticket_data[33] or '--',
                            '硬卧': ticket_data[28] or '--',
                            '软座': ticket_data[24] or '--',
                            '硬座': ticket_data[29] or '--',
                            '无座': ticket_data[26] or '--',
                        }
                    }
                    
                    # 如果指定了车次，只返回指定车次的信息
                    if train_codes and train_info['train_code'] not in train_codes:
                        continue
                        
                    tickets.append(train_info)
                
                if tickets:
                    return tickets
                else:
                    print("没有找到符合条件的车次")
                    return []
            else:
                print("API返回数据格式不正确")
                return []
                
        except Exception as e:
            print(f"从网页爬取车票信息失败: {e}")
            print(f"错误类型: {type(e).__name__}")
            if hasattr(e, 'response') and e.response:
                print(f"响应状态码: {e.response.status_code}")
            return []

def load_config(config_file='config.yaml'):
    """加载配置文件"""
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                print(f"已加载配置文件: {config_file}")
                return config
        except Exception as e:
            print(f"加载配置文件失败: {e}")
    return None

def save_config(config, config_file='config.yaml'):
    """保存配置到文件"""
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        print(f"配置已保存到: {config_file}")
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='12306车票查询监控工具')
    parser.add_argument('--config', type=str, default='config.yaml', help='配置文件路径')
    parser.add_argument('--proxy', type=str, help='代理服务器地址，格式: http://host:port')
    parser.add_argument('--from', dest='from_station', type=str, help='出发站')
    parser.add_argument('--to', dest='to_station', type=str, help='到达站')
    parser.add_argument('--date', type=str, help='出发日期，格式: YYYY-MM-DD')
    parser.add_argument('--trains', type=str, help='车次，多个用逗号分隔')
    parser.add_argument('--seats', type=str, help='座位类型，多个用逗号分隔')
    parser.add_argument('--interval', type=int, default=60, help='查询间隔（秒）')
    
    return parser.parse_args()

if __name__ == "__main__":
    # 解析命令行参数
    args = parse_arguments()
    
    # 创建监控器实例
    monitor = TrainTicketMonitor()
    
    # 设置代理（如果提供）
    if args.proxy:
        monitor.set_proxy(args.proxy)
    
    # 尝试加载配置文件
    config = load_config(args.config)
    
    # 处理登录配置
    if config and 'login_config' in config:
        login_config = config['login_config']
        login_success = False
        
        # 优先尝试Cookie登录
        cookie_config = login_config.get('cookie_login', {})
        if cookie_config.get('enabled'):
            login_success = monitor.login_with_cookie(cookie_config)
        
        # 如果Cookie登录未启用或失败，尝试账号密码登录
        if not login_success and login_config.get('enabled'):
            if login_config.get('username') and login_config.get('password'):
                print("\nCookie登录未成功，尝试账号密码登录...")
                login_success = monitor.login(login_config['username'], login_config['password'])
        
        if not login_success:
            print("\n" + "="*50)
            print("登录失败，但仍将尝试查询（部分查询可能无需登录）")
            print("="*50)
            choice = input("是否继续? (y/n): ")
            if choice.lower() != 'y':
                print("程序退出")
                exit(0)
    
    # 如果命令行参数提供了完整的查询参数，直接使用
    if args.from_station and args.to_station and args.date:
        from_station = args.from_station
        to_station = args.to_station
        train_date = args.date
        train_codes = args.trains.split(',') if args.trains else None
        seat_types = args.seats.split(',') if args.seats else None
        interval = args.interval
        
        # 开始监控
        monitor.monitor_tickets(from_station, to_station, train_date, train_codes, seat_types, interval)
    else:
        
        if config and 'query_params' in config:
            # 使用配置文件中的参数
            params = config['query_params']
            from_station = params.get('from_station')
            to_station = params.get('to_station')
            train_date = params.get('train_date')
            train_codes = params.get('train_codes')
            seat_types = params.get('seat_types')
            interval = params.get('interval', 60)
            
            # 确认配置信息
            print("\n当前配置信息:")
            print(f"出发站: {from_station}")
            print(f"到达站: {to_station}")
            print(f"出发日期: {train_date}")
            print(f"监控车次: {', '.join(train_codes) if train_codes else '所有车次'}")
            print(f"座位类型: {', '.join(seat_types) if seat_types else '所有类型'}")
            print(f"查询间隔: {interval}秒")
            
            use_config = input("\n是否使用以上配置? (y/n): ")
            if use_config.lower() != 'y':
                config = None  # 不使用配置文件，转为手动输入
        
        if not config:
            # 手动输入参数
            print("\n请输入查询参数:")
            from_station = input("请输入出发站（如北京）: ")
            to_station = input("请输入到达站（如上海）: ")
            train_date = input("请输入出发日期（格式: YYYY-MM-DD）: ")
            
            train_codes_input = input("请输入要监控的车次（多个车次用逗号分隔，留空监控所有车次）: ")
            train_codes = [code.strip() for code in train_codes_input.split(',')] if train_codes_input.strip() else None
            
            seat_types_input = input("请输入要监控的座位类型（多个类型用逗号分隔，留空监控所有类型）: ")
            seat_types = [seat.strip() for seat in seat_types_input.split(',')] if seat_types_input.strip() else None
            
            interval = int(input("请输入查询间隔（秒，建议不少于30秒）: ") or "60")
            
            # 询问是否保存配置
            save_config_choice = input("\n是否保存当前配置以便下次使用? (y/n): ")
            if save_config_choice.lower() == 'y':
                new_config = {
                    'query_params': {
                        'from_station': from_station,
                        'to_station': to_station,
                        'train_date': train_date,
                        'train_codes': train_codes,
                        'seat_types': seat_types,
                        'interval': interval
                    }
                }
                save_config(new_config)
        
        # 开始监控
        monitor.monitor_tickets(from_station, to_station, train_date, train_codes, seat_types, interval) 