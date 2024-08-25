import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QPushButton, QTextEdit, QGroupBox, QTableWidget, QTableWidgetItem, QMenuBar, QAction,
                             QMenu, QInputDialog, QSpinBox, QLabel, QHeaderView)
from PyQt5.QtCore import Qt
import logging
from app.config_handler import load_config, save_config
from app.registration_worker import RegistrationWorker
from app.browser_manager import BrowserManager  # 导入 BrowserManager

# 设置日志记录
logging.basicConfig(
    filename='logs/app.log',  # 日志文件路径
    level=logging.INFO,        # 日志记录级别
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 首先初始化浏览器管理器
        self.browser_manager = BrowserManager(max_browsers=10)  # 默认最大10个浏览器
        # 启动时自动加载配置文件
        self.initUI()
        self.load_initial_configs()

    def initUI(self):
        main_layout = QVBoxLayout(self)

        # 菜单栏
        menu_bar = QMenuBar(self)
        file_menu = menu_bar.addMenu('文件')

        save_action = QAction('保存更改', self)
        save_action.triggered.connect(self.save_all_configs)
        file_menu.addAction(save_action)

        main_layout.setMenuBar(menu_bar)

        # 第一行：账号列表、代理列表、商品链接列表
        first_row_layout = QHBoxLayout()

        # 账号列表
        self.account_table = QTableWidget()
        self.account_table.setColumnCount(3)
        self.account_table.setHorizontalHeaderLabels(['邮箱', '密码', '注册状态'])
        self.account_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.account_table.customContextMenuRequested.connect(self.show_account_menu)
        # 设置列宽自动铺满
        self.account_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        first_row_layout.addWidget(self.account_table)

        # 代理列表
        self.proxy_table = QTableWidget()
        self.proxy_table.setColumnCount(1)
        self.proxy_table.setHorizontalHeaderLabels(['代理地址'])
        self.proxy_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.proxy_table.customContextMenuRequested.connect(self.show_proxy_menu)
        # 设置列宽自动铺满
        self.proxy_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        first_row_layout.addWidget(self.proxy_table)

        # 商品链接列表
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(3)
        self.product_table.setHorizontalHeaderLabels(['标题', '价格', '链接地址'])
        self.product_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.product_table.customContextMenuRequested.connect(self.show_product_menu)
        # 设置列宽自动铺满
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        first_row_layout.addWidget(self.product_table)

        main_layout.addLayout(first_row_layout)

        # 第二行：线程配置、设置参数区域、启动监听线程数量、线程执行状态
        second_row_layout = QHBoxLayout()
        # 浏览器管理部分
        browser_management_group = QGroupBox("浏览器管理")
        browser_management_layout = QVBoxLayout()

        self.max_browsers_spinbox = QSpinBox()
        self.max_browsers_spinbox.setRange(1, 100)
        self.max_browsers_spinbox.setValue(self.browser_manager.max_browsers)
        self.max_browsers_spinbox.valueChanged.connect(self.set_max_browsers)
        browser_management_layout.addWidget(QLabel("最大浏览器数量:"))
        browser_management_layout.addWidget(self.max_browsers_spinbox)

        self.browser_list_table = QTableWidget()
        self.browser_list_table.setColumnCount(2)
        self.browser_list_table.setHorizontalHeaderLabels(['线程名', '浏览器ID'])
        browser_management_layout.addWidget(self.browser_list_table)
        self.browser_manager.browser_list_updated.connect(self.update_browser_list)

        browser_management_group.setLayout(browser_management_layout)
        main_layout.addWidget(browser_management_group)

        # 线程配置区域
        thread_config_group = QGroupBox("线程配置")
        thread_config_layout = QVBoxLayout()
        self.thread_spinbox = QSpinBox()
        self.thread_spinbox.setRange(1, 100)
        self.thread_spinbox.setValue(10)  # 默认10个线程
        thread_config_layout.addWidget(QLabel("线程数量:"))
        thread_config_layout.addWidget(self.thread_spinbox)

        self.start_registration_button = QPushButton("开始注册")
        self.start_registration_button.clicked.connect(self.start_registration)
        thread_config_layout.addWidget(self.start_registration_button)

        thread_config_group.setLayout(thread_config_layout)
        second_row_layout.addWidget(thread_config_group)

        # 设置参数区域
        settings_group = QGroupBox("设置参数区域")
        settings_layout = QVBoxLayout()
        self.param_input = QLineEdit()
        self.param_input.setPlaceholderText("输入参数")
        settings_layout.addWidget(self.param_input)

        self.start_monitor_button = QPushButton("启动监听线程数量")
        self.start_monitor_button.clicked.connect(self.start_monitor)
        settings_layout.addWidget(self.start_monitor_button)

        settings_group.setLayout(settings_layout)
        second_row_layout.addWidget(settings_group)

        # 线程执行状态
        thread_status_group = QGroupBox("线程执行状态")
        thread_status_layout = QVBoxLayout()
        self.thread_status_table = QTableWidget()
        self.thread_status_table.setColumnCount(2)
        self.thread_status_table.setHorizontalHeaderLabels(['线程名', '状态'])
        # 设置列宽自动铺满
        self.thread_status_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        thread_status_layout.addWidget(self.thread_status_table)
        thread_status_group.setLayout(thread_status_layout)

        second_row_layout.addWidget(thread_status_group)

        main_layout.addLayout(second_row_layout)

        # 第三行：执行记录日志框
        self.log_output = QTextEdit(self)
        self.log_output.setReadOnly(True)
        main_layout.addWidget(self.log_output)

        self.setLayout(main_layout)
        self.setWindowTitle('自动化业务流程')
        self.setGeometry(100, 100, 1000, 600)
        self.show()

    def load_initial_configs(self):
        # 加载账号配置文件
        try:
            accounts = load_config('accounts.json')
            self.account_table.setRowCount(len(accounts))
            for row, account in enumerate(accounts):
                self.account_table.setItem(row, 0, QTableWidgetItem(account['email']))
                self.account_table.setItem(row, 1, QTableWidgetItem(account['password']))
                self.account_table.setItem(row, 2, QTableWidgetItem(account.get('status', '未注册')))
            self.log(f"自动加载了 {len(accounts)} 个账号")
        except Exception as e:
            self.log(f"加载账号配置文件时出错: {str(e)}")

        # 加载代理配置文件
        try:
            proxies = load_config('proxies.json')
            self.proxy_table.setRowCount(len(proxies))
            for row, proxy in enumerate(proxies):
                self.proxy_table.setItem(row, 0, QTableWidgetItem(proxy))
            self.log(f"自动加载了 {len(proxies)} 个代理")
        except Exception as e:
            self.log(f"加载代理配置文件时出错: {str(e)}")

        # 加载商品链接配置文件
        try:
            links = load_config('links.json')
            self.product_table.setRowCount(len(links))
            for row, link in enumerate(links):
                self.product_table.setItem(row, 0, QTableWidgetItem(link['title']))
                self.product_table.setItem(row, 1, QTableWidgetItem(link['price']))
                self.product_table.setItem(row, 2, QTableWidgetItem(link['link']))
            self.log(f"自动加载了 {len(links)} 个商品链接")
        except Exception as e:
            self.log(f"加载商品链接配置文件时出错: {str(e)}")

    def save_all_configs(self):
        try:
            # 保存账号配置
            accounts = []
            for row in range(self.account_table.rowCount()):
                email = self.account_table.item(row, 0).text()
                password = self.account_table.item(row, 1).text()
                status = self.account_table.item(row, 2).text()
                accounts.append({"email": email, "password": password, "status": status})
            save_config(accounts, 'accounts.json')
            self.log("账号配置文件已保存")

            # 保存代理配置
            proxies = []
            for row in range(self.proxy_table.rowCount()):
                proxy = self.proxy_table.item(row, 0).text()
                proxies.append(proxy)
            save_config(proxies, 'proxies.json')
            self.log("代理配置文件已保存")

            # 保存商品链接配置
            links = []
            for row in range(self.product_table.rowCount()):
                title = self.product_table.item(row, 0).text()
                price = self.product_table.item(row, 1).text()
                link = self.product_table.item(row, 2).text()
                links.append({"title": title, "price": price, "link": link})
            save_config(links, 'links.json')
            self.log("商品链接配置文件已保存")

        except Exception as e:
            self.log(f"保存配置文件时出错: {str(e)}")

    def start_registration(self):
        thread_count = self.thread_spinbox.value()
        self.thread_status_table.setRowCount(thread_count)  # 动态设置线程状态表格行数

        # 创建 RegistrationWorker 实例时传递 browser_manager
        self.registration_worker = RegistrationWorker(
            self.account_table,
            thread_count,
            self.log,
            self.browser_manager  # 传递 browser_manager 实例
        )

        self.registration_worker.update_status.connect(self.update_thread_status)  # 连接信号更新线程状态
        self.registration_worker.reload_table.connect(self.load_initial_configs)  # 连接信号到重新加载方法
        self.registration_worker.save_configs_signal.connect(self.save_all_configs)  # 连接信号以保存配置
        self.registration_worker.start()

    def update_thread_status(self, thread_index, status_message):
        thread_name = f"线程{thread_index + 1}"  # 设置线程名称为“线程1、线程2……”等
        self.thread_status_table.setItem(thread_index, 0, QTableWidgetItem(thread_name))
        self.thread_status_table.setItem(thread_index, 1, QTableWidgetItem(status_message))

    def start_monitor(self):
        # 监听已经启动的注册线程
        threads = self.registration_worker.get_threads()  # 获取线程列表
        for i, thread in enumerate(threads):
            if thread.is_alive():
                self.update_thread_status(i, "运行中")
            else:
                self.update_thread_status(i, "已完成")

    # 右键菜单处理
    def show_account_menu(self, position):
        menu = QMenu()
        modify_action = QAction('修改', self)
        modify_action.triggered.connect(lambda: self.modify_cell(self.account_table))
        menu.addAction(modify_action)

        delete_action = QAction('删除', self)
        delete_action.triggered.connect(lambda: self.delete_row(self.account_table))
        menu.addAction(delete_action)

        menu.exec_(self.account_table.viewport().mapToGlobal(position))

    def show_proxy_menu(self, position):
        menu = QMenu()
        modify_action = QAction('修改', self)
        modify_action.triggered.connect(lambda: self.modify_cell(self.proxy_table))
        menu.addAction(modify_action)

        delete_action = QAction('删除', self)
        delete_action.triggered.connect(lambda: self.delete_row(self.proxy_table))
        menu.addAction(delete_action)

        menu.exec_(self.proxy_table.viewport().mapToGlobal(position))

    def show_product_menu(self, position):
        menu = QMenu()
        modify_action = QAction('修改', self)
        modify_action.triggered.connect(lambda: self.modify_cell(self.product_table))
        menu.addAction(modify_action)

        delete_action = QAction('删除', self)
        delete_action.triggered.connect(lambda: self.delete_row(self.product_table))
        menu.addAction(delete_action)

        menu.exec_(self.product_table.viewport().mapToGlobal(position))

    def delete_row(self, table):
        current_row = table.currentRow()
        if current_row >= 0:
            table.removeRow(current_row)
            self.save_all_configs()  # 实时保存配置
            self.log("删除了表格中的一行并已保存")

    def modify_cell(self, table):
        current_row = table.currentRow()
        current_column = table.currentColumn()
        if current_row >= 0 and current_column >= 0:
            item = table.item(current_row, current_column)
            if item:
                text, ok = QInputDialog.getText(self, "修改数据", "请输入新的值:", QLineEdit.Normal, item.text())
                if ok and text:
                    item.setText(text)
                    self.save_all_configs()  # 实时保存配置
                    self.log("修改了表格中的一个单元格并已保存")

    def log(self, message):
        self.log_output.append(message)
        logging.info(message)

    def set_max_browsers(self):
        max_browsers = self.max_browsers_spinbox.value()
        self.browser_manager.set_max_browsers(max_browsers)

    def update_browser_list(self):
        self.browser_list_table.setRowCount(len(self.browser_manager.get_allocated_browsers()))
        for i, (thread_name, browser_id) in enumerate(self.browser_manager.get_allocated_browsers().items()):
            self.browser_list_table.setItem(i, 0, QTableWidgetItem(thread_name))
            self.browser_list_table.setItem(i, 1, QTableWidgetItem(browser_id))
def run_app():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run_app()
