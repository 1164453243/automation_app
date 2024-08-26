import json
import threading
import time
import random

import requests
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QTableWidgetItem
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from app.bit_api import openBrowser, url, headers
from app.config_handler import load_config, parse_proxy_info
from app.payment_handler import handle_payment
from app.register_handler import register_account
from app.thread_manager import ThreadManager


class RegistrationWorker(QThread):
    update_status = pyqtSignal(int, str)
    reload_table = pyqtSignal()
    save_configs_signal = pyqtSignal()

    def __init__(self, account_table, thread_count, log_callback, browser_manager):
        super().__init__()
        self.account_table = account_table
        self.thread_count = thread_count
        self.log = log_callback
        # self.browser_manager = browser_manager
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

            card_info = self.get_unique_card_info()
            if not card_info:
                self.log(f"线程{i + 1} - 获取银行卡信息失败")
                continue

            proxy_template = load_config('proxies.json').get('proxy_template', '')
            proxy_str = proxy_template.format(region=card_info['province'], city=card_info['city'])
            match_proxy = parse_proxy_info(proxy_str)

            if not match_proxy:
                self.log(f"线程{i + 1} - 获取代理信息失败")
                continue

            thread_name = f"线程{i + 1}"
            self.thread_manager.start_thread(self.process_account, (i, account, thread_name, card_info, match_proxy))

        self.thread_manager.wait_for_completion()
        self.log("所有账号注册完成")
        self.save_configs_signal.emit()
        self.reload_table.emit()

    def get_unique_card_info(self):
        while True:
            card_info = self.get_card_info()
            if card_info and card_info['card_number'] not in self.card_info_used:
                self.card_info_used.add(card_info['card_number'])
                return card_info
            time.sleep(1)

    def get_card_info(self, max_retries=9999, delay=2):
        url = "https://www.savestamp.com/api/get_and_update_random_order.php?token=123456"
        retries = 0

        while retries < max_retries:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    response_data = response.json()
                    if response_data['success']:
                        self.log(f"获取银行卡成功:{response_data['data']}")
                        return response_data['data']
                    else:
                        self.log("获取银行卡信息失败: 响应中 success 字段为 False")
                else:
                    self.log(f"请求失败，状态码: {response.status_code}")
            except Exception as e:
                self.log(f"获取银行卡信息时出错: {str(e)}")

            retries += 1
            self.log(f"重试第 {retries} 次...")
            time.sleep(delay)

        self.log("超过最大重试次数，仍然无法获取银行卡信息")
        return None

    def stop(self):
        self._is_running = False
        self.log("正在停止所有线程...")

    def get_unregistered_accounts(self):
        unregistered = []
        for row in range(self.account_table.rowCount()):
            status = self.account_table.item(row, 2).text()
            if status == '未注册':
                email = self.account_table.item(row, 0).text()
                password = self.account_table.item(row, 1).text()
                unregistered.append((row, email, password))
        return unregistered

    def process_account(self, thread_index, account, thread_name,card_info,proxy):
        row, email, password = account


        if not self._is_running:
           return  # 退出线程

        browser = self.create_browser_instance(proxy)
        try:
            # 执行注册操作
            self.update_status.emit(thread_index, f"{email} - 注册中")
            self.register_account(browser, email, password)
            self.update_status.emit(thread_index, f"{email} - 注册完成")
            self.account_table.setItem(row, 2, QTableWidgetItem("已注册"))
            self.log(f"账号 {email} 注册成功")

            # 模拟加入购物车过程
            self.update_status.emit(thread_index, f"{email} - 加入购物车中")
            self.add_to_cart(browser,card_info)
            self.update_status.emit(thread_index, f"{email} - 加入购物车完成")
            self.log(f"账号 {email} 加入购物车完成")

            # 模拟支付过程
            self.update_status.emit(thread_index, f"{email} - 支付中")
            self.process_payment(browser)
            self.update_status.emit(thread_index, f"{email} - 支付完成")
            self.log(f"账号 {email} 支付完成")

        finally:
            browser.quit()


        # 实时保存每次成功操作后的配置
        self.save_configs_signal.emit()

    def create_browser_instance(self,proxy):
        # 使用 browser_id 创建比特浏览器实例
        # 随机选择浏览器类型（安卓或iOS）
        self.log('开始创建比特浏览器实例:')
        browser_type = random.choice(['Android', 'IOS'])

        # 根据随机选择的类型设置指纹和窗口尺寸
        if browser_type == 'Android':
            os_type = 'Android'
            os_name = 'Linux armv81'
            device_pixel_ratio = 2
        else:
            os_type = 'IOS'
            os_name = 'iPhone'
            device_pixel_ratio = 3

        json_data = {
            'name': f'{browser_type} browser',  # 可以根据需求自定义浏览器名称
            'browserFingerPrint': {
                'coreVersion': '118',  # 或者其他适当的版本
                'ostype': os_type,  # 安卓或iOS
                'os': os_name,  # 操作系统名称
                'openWidth': 360,  # 窗口宽度
                'openHeight': 748,  # 窗口高度
                'resolutionType': '1',
                'resolution': '360x748',
                'devicePixelRatio': device_pixel_ratio
            },
            'proxyMethod': 2,  # 代理方式，2 表示自定义代理
            "proxyType": "noproxy",
            # 'proxyType': 'https',  # 根据传入的代理类型设置
            # 'host': proxy['ip'],  # 代理主机
            # 'port': proxy['port'],  # 代理端口
            # 'proxyUserName': proxy['username'],  # 代理账号
            # 'proxyPassword': proxy['password'],  # 代理密码
        }

        self.log(f"代理配置: {json_data}")
        # 发送请求到比特浏览器 API，更新浏览器设置
        res = requests.post(f"{url}/browser/update", data=json.dumps(json_data), headers=headers).json()
        browser_id = res['data']['id']

        print(f"Browser created with ID: {browser_id}")

        # 使用 browser_id 创建一个新的浏览器实例
        res = openBrowser(browser_id)
        driverPath = res['data']['driver']
        debuggerAddress = res['data']['http']

        # 设置 Chrome 选项
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("debuggerAddress", debuggerAddress)
        service = Service(executable_path=driverPath)
        # 使用获取的路径和选项启动浏览器
        browser = webdriver.Chrome(service=service, options=chrome_options)
        return browser

    def register_account(self, browser, email, password):

        # 打开注册页面
        browser.get('https://login.g2a.com/register-page?redirect_uri=https%3A%2F%2Fwww.g2a.com%2F&source=topbar')
        register_account(self,browser,email,password,'123456')

    def add_to_cart(self, browser,card_info):
        # 模拟加入购物车的操作
        browser.get('https://www.g2a.com/category/games-c189?sort=price-highest-first')

        handle_payment(self,browser,card_info)


    def process_payment(self, browser):
        # 模拟支付的操作
        pay_button = browser.find_element_by_name('pay')
        pay_button.click()
        time.sleep(2)  # 等待支付完成