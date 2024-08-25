import threading
import time
from selenium.webdriver.support import expected_conditions as EC

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QTableWidgetItem
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from app.bit_api import openBrowser
from app.browser_manager import BrowserManager  # 导入 BrowserManager

class RegistrationWorker(QThread):
    update_status = pyqtSignal(int, str)
    reload_table = pyqtSignal()  # 用于通知主线程重新加载表格
    save_configs_signal = pyqtSignal()  # 用于通知主线程保存配置

    def __init__(self, account_table, thread_count, log_callback, browser_manager):
        super().__init__()
        self.account_table = account_table
        self.thread_count = thread_count
        self.log = log_callback
        self.browser_manager = browser_manager
        self.threads = []

    def run(self):
        self.log("注册线程启动...")
        accounts_to_register = self.get_unregistered_accounts()
        self.log(f"找到 {len(accounts_to_register)} 个未注册账号")

        for i, account in enumerate(accounts_to_register):
            thread_name = f"线程{i + 1}"  # 设置线程名称为“线程1、线程2……”等
            thread = threading.Thread(target=self.process_account, args=(i, account, thread_name))
            self.threads.append(thread)
            thread.start()

        for i, thread in enumerate(self.threads):
            thread.join()

        self.log("所有账号注册完成")
        self.save_configs_signal.emit()  # 触发信号保存配置
        self.reload_table.emit()  # 触发信号重新加载表格

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

    def process_account(self, thread_index, account, thread_name):
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
            self.add_to_cart(browser)
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
        browser.implicitly_wait(10)  # 等待页面加载
        # 等待页面加载并查找输入框
        wait = WebDriverWait(browser, 10)
        # 填写 Email
        email_field = wait.until(EC.visibility_of_element_located((By.NAME, 'email')))
        email_field.send_keys(email)

        # 填写 Password
        password_field = wait.until(EC.visibility_of_element_located((By.NAME, 'password')))
        password_field.send_keys(password)

        # 勾选 "registration" 复选框
        try:
            registration_checkbox = browser.find_element(By.NAME, 'registration')
            if not registration_checkbox.is_selected():
                registration_checkbox.click()
            cookies_checkbox = browser.find_element(By.NAME, 'cookies')
            if not cookies_checkbox.is_selected():
                cookies_checkbox.click()
        except Exception as e:
            self.log(f"注册复选框未找到或无法点击，继续执行。Error: {str(e)}")

        # 点击注册按钮
        time.sleep(3)

        submit_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@class, 'indexes__Button') and text()='Create account']")))
        submit_button.click()

        # 等待验证码输入框出现并输入验证码 "123456"
        try:
            time.sleep(3)  # 等待页面加载验证码输入框
            verification_code = "123456"
            for i in range(6):
                input_box = wait.until(EC.visibility_of_element_located((By.NAME, f'val_{i}')))
                input_box.send_keys(verification_code[i])
            self.log(f"{email} - 验证码输入成功")
        except Exception as e:
            self.log(f"{email} - 验证码输入失败。Error: {str(e)}")

    def add_to_cart(self, browser):
        # 模拟加入购物车的操作
        browser.get('https://www.g2a.com/category/games-c189')
        add_to_cart_button = browser.find_element_by_name('add_to_cart')
        add_to_cart_button.click()
        time.sleep(2)  # 等待操作完成

    def process_payment(self, browser):
        # 模拟支付的操作
        pay_button = browser.find_element_by_name('pay')
        pay_button.click()
        time.sleep(2)  # 等待支付完成
