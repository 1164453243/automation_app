import threading
import time

import requests
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QTableWidgetItem
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from app.bit_api import openBrowser
from app.payment_handler import handle_payment
from app.register_handler import register_account


class RegistrationWorker(QThread):
    update_status = pyqtSignal(int, str)
    reload_table = pyqtSignal()  # 用于通知主线程重新加载表格
    save_configs_signal = pyqtSignal()  # 用于通知主线程保存配置

    def __init__(self, account_table, thread_count, log_callback, browser_manager):
        super().__init__()
        self.account_table = account_table
        self._is_running = True
        self.thread_count = thread_count
        self.log = log_callback
        self.browser_manager = browser_manager
        self.threads = []

    def run(self):
        self.log("注册线程启动...")
        accounts_to_register = self.get_unregistered_accounts()
        self.log(f"找到 {len(accounts_to_register)} 个未注册账号")


        for i, account in enumerate(accounts_to_register):
            if not self._is_running:
                break  # 停止循环
            # 获取银行卡信息
            card_info = self.get_card_info()
            if not card_info:
                self.log(f"线程{i + 1} - 获取银行卡信息失败")
                continue

            thread_name = f"线程{i + 1}"  # 设置线程名称为“线程1、线程2……”等
            thread = threading.Thread(target=self.process_account, args=(i, account, thread_name,card_info))
            self.threads.append(thread)
            thread.start()

        for i, thread in enumerate(self.threads):
            thread.join()

        self.log("所有账号注册完成")
        self.save_configs_signal.emit()  # 触发信号保存配置
        self.reload_table.emit()  # 触发信号重新加载表格

    def get_card_info(self):
        url = "https://www.savestamp.com/api/get_and_update_random_order.php?token=123456"
        try:
            response = requests.get(url)
            response_data = response.json()
            if response_data['success']:
                return response_data['data']
            else:
                self.log("获取银行卡信息失败")
                return None
        except Exception as e:
            self.log(f"获取银行卡信息时出错: {str(e)}")
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

    def process_account(self, thread_index, account, thread_name,card_info):
        row, email, password = account
        browser_id = self.browser_manager.allocate_browser(thread_name)

        while browser_id is None:  # 如果没有可用浏览器，则等待
            if not self._is_running:
                return  # 退出线程
            time.sleep(1)
            browser_id = self.browser_manager.allocate_browser(thread_name)

        browser = self.create_browser_instance(browser_id)
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
            self.browser_manager.release_browser(thread_name)

        # 实时保存每次成功操作后的配置
        self.save_configs_signal.emit()

    def create_browser_instance(self, browser_id):
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
        browser.get('https://www.g2a.com/category/games-c189')

        handle_payment(self,browser,card_info)


    def process_payment(self, browser):
        # 模拟支付的操作
        pay_button = browser.find_element_by_name('pay')
        pay_button.click()
        time.sleep(2)  # 等待支付完成
