import json
import logging
import threading
import time
import random

import requests
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QTableWidgetItem
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from app.bit_api import openBrowser, url, headers, check_proxy
from app.config_handler import load_config, parse_proxy_info
from app.email_code import check_pay_status
from app.payment_handler import handle_payment
from app.register_handler import register_account
from app.thread_manager import ThreadManager

logging.basicConfig(
    filename='logs/pay.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
class ThreadManager:
    def __init__(self, max_threads):
        self.max_threads = max_threads
        self.threads = []

    def start_thread(self, target, args=()):
        if len(self.threads) >= self.max_threads:
            self.wait_for_completion()  # 等待现有线程完成

        thread = threading.Thread(target=target, args=args)
        self.threads.append(thread)
        thread.start()

    def stop_all_threads(self):
        for thread in self.threads:
            if thread.is_alive():
                # 通知所有线程停止（假设线程内部检查 `_is_running`）
                thread._is_running = False  # 假设目标函数检查此变量
        # 等待所有线程完成
        # self.wait_for_completion()

    def wait_for_completion(self):
        for thread in self.threads:
            thread.join()  # 等待线程完成
        self.threads.clear()  # 清除完成的线程


class RegistrationWorker(QThread):
    # update_status = pyqtSignal(int, str)
    # reload_table = pyqtSignal()
    # save_configs_signal = pyqtSignal()

    def __init__(self, account_table, thread_count, log_callback, browser_manager):
        super().__init__()
        self.account_table = account_table
        self.thread_count = thread_count
        self.log = log_callback
        self.log_lock = threading.Lock()
        self.thread_manager = ThreadManager(thread_count)
        self.card_info_used = set()
        self._is_running = True

    def run(self):
        self.log("注册线程启动...")

        accounts_to_register = self.get_unregistered_accounts()
        self.log(f"找到 {len(accounts_to_register)} 个未注册账号")

        for i, account in enumerate(accounts_to_register):
            if not self._is_running:
                break

            # 循环获取卡号
            card_info = self.get_unique_card_info()
            if not card_info:
                self.log(f"线程{i + 1} - 获取银行卡信息失败，停止创建更多线程")
                break  # 如果无法获取到卡号，停止创建线程

            # 获取并解析代理信息
            proxy_template = load_config('proxies.json').get('proxy_template', '')
            proxy_str = proxy_template.format(region=card_info['province'], city=card_info['city'])
            match_proxy = parse_proxy_info(self,proxy_str)

            if not match_proxy:
                self.log(f"线程{i + 1} - 获取代理信息失败")
                continue
            if not check_proxy(match_proxy):
                self.log(f"线程{i + 1} - 代理无效")
                continue

            thread_name = f"线程{i + 1}"
            self.thread_manager.start_thread(self.process_account, (i, account, thread_name, card_info, match_proxy))

        self.thread_manager.wait_for_completion()
        self.log("所有账号注册完成")
        # self.save_configs_signal.emit()
        # self.reload_table.emit()


    def stop(self):
        self._is_running = False
        self.log("正在停止所有线程...")
        self.thread_manager.stop_all_threads()

    def get_unique_card_info(self):
        while self._is_running:
            card_info = self.get_card_info()
            if card_info and card_info['card_number'] not in self.card_info_used:
                self.card_info_used.add(card_info['card_number'])
                return card_info
            time.sleep(1)
        return None

    def get_card_info(self, max_retries=9999, delay=2):
        url = "https://www.savestamp.com/api/get_and_update_random_order.php?token=123456"
        retries = 0

        while retries < max_retries and self._is_running:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    response_data = response.json()
                    if response_data['success']:
                        self.log(f"获取银行卡成功: {response_data['data']}")
                        return response_data['data']
                    else:
                        self.log("获取银行卡信息失败: 响应中 success 字段为 False")
                else:
                    self.log(f"请求失败，状态码: {response.status_code}")
            except Exception as e:
                self.log(f"获取银行卡信息时出错: {str(e)}")

            retries += 1
            # self.log(f"重试第 {retries} 次...")
            time.sleep(delay)

        self.log("超过最大重试次数，仍然无法获取银行卡信息")
        self._is_running = False  # 设置标志位以停止线程
        return None


    def get_unregistered_accounts(self):
        unregistered = []
        for row in range(self.account_table.rowCount()):
            status = self.account_table.item(row, 2).text()
            if status == '未注册':
                email = self.account_table.item(row, 0).text()
                password = self.account_table.item(row, 1).text()
                unregistered.append((row, email, password))
        return unregistered

    def process_account(self, thread_index, account, thread_name, card_info, proxy):
        row, email, password = account

        if not self._is_running:
            return None # 退出线程

        browser = self.create_browser_instance(proxy, email)
        if browser is None:
            self.log(f"线程{thread_index + 1} - 无法创建浏览器实例，跳过账号 {email}")
            return None

        try:
            if not self._is_running:
                return  None# 再次检查
            other_password = 'A234fgdfhfgh45'
            # 执行注册操作
            # self.update_status.emit(thread_index, f"{email} - 注册中")
            self.register_account(browser, email, password,other_password)
            # self.update_status.emit(thread_index, f"{email} - 注册完成")
            # self.account_table.setItem(row, 2, QTableWidgetItem("已注册"))
            self.log(f"账号 {email} 注册成功")

            if not self._is_running:
                return  None# 再次检查

            # 模拟加入购物车过程
            # self.update_status.emit(thread_index, f"{email} - 加入购物车中")
            self.add_to_cart(browser, card_info)
            # self.update_status.emit(thread_index, f"{email} - 加入购物车完成")
            self.log(f"账号 {email} 加入购物车完成")

            if not self._is_running:
                return  None# 再次检查

            # 模拟支付过程
            # self.update_status.emit(thread_index, f"{email} - 支付中")
            self.process_payment(browser)
            # self.update_status.emit(thread_index, f"{email} - 支付完成")
            self.log(f"账号 {email} 支付完成")

            # 获取支付结果
            if check_pay_status(email, password, 0):
                logging.info(f"账号: {email} 邮箱密码：{password} 平台密码：{other_password}  支付成功")
                self.pay_log(f"账号 {email} 支付成功")
            else :
                logging.info(f"账号: {email} 邮箱密码：{password} 平台密码：{other_password}  支付成功")
                self.pay_log(f"账号 {email} 支付失败")
        finally:
            browser.quit()

    def create_browser_instance(self, proxy, email):
        try:
            self.log(f'{email} 开始创建比特浏览器实例:')
            browser_type = random.choice(['Android', 'IOS'])

            if browser_type == 'Android':
                os_type = 'Android'
                os_name = 'Linux armv81'
                device_pixel_ratio = 3
            else:
                os_type = 'IOS'
                os_name = 'iPhone'
                device_pixel_ratio = 2

            json_data = {
                'name': f'{browser_type} browser',
                'browserFingerPrint': {
                    'coreVersion': '118',
                    'ostype': os_type,
                    'os': os_name,
                    'openWidth': 360,
                    'openHeight': 748,
                    'resolutionType': '1',
                    'resolution': '360x748',
                    'devicePixelRatio': device_pixel_ratio
                },
                'proxyMethod': 2,
                "proxyType": "noproxy",
            }
            self.log(f"{email} 代理配置: {json_data}")

            res = requests.post(f"{url}/browser/update", data=json.dumps(json_data), headers=headers)
            res.raise_for_status()
            res_json = res.json()

            if 'data' in res_json and 'id' in res_json['data']:
                browser_id = res_json['data']['id']
            else:
                self.log(f"API 返回数据不包含 'id': {res_json}")
                self._is_running = False
                return None

            self.log(f"Browser created with ID: {browser_id}")

            res = openBrowser(browser_id)

            if 'data' not in res or 'driver' not in res['data'] or 'http' not in res['data']:
                self.log(f"浏览器创建失败，返回的数据不完整: {res}")
                self._is_running = False
                return None

            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_experimental_option("debuggerAddress", res['data']['http'])
            service = Service(executable_path=res['data']['driver'])

            browser = webdriver.Chrome(service=service, options=chrome_options)
            return browser

        except Exception as e:
            self.log(f"{email} 创建浏览器出错: {str(e)}")
            self.log(f"{email} 停止线程")
            self._is_running = False
            return None

    def register_account(self, browser, email, password,other_password):
        browser.get('https://login.g2a.com/register-page?redirect_uri=https%3A%2F%2Fwww.g2a.com%2F&source=topbar')
        register_account(self, browser, email, password, other_password)

    def add_to_cart(self, browser, card_info):
        handle_payment(self, browser, card_info)

    def pay_log(self, message):
        with self.log_lock:  # 使用线程锁保护日志记录
            self.log(message)
            logging.info(message)
        # print(message)