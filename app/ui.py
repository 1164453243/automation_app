import sys
import threading

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTextEdit, QGroupBox, QTableWidget, QTableWidgetItem,
    QMenuBar, QAction, QSpinBox, QLabel, QHeaderView, QFileDialog, QMenu, QInputDialog
)
from PyQt5.QtCore import Qt, QTimer
import logging
from app.config_handler import load_config, save_config
from app.registration_worker import RegistrationWorker
from app.browser_manager import BrowserManager

# 设置日志记录
logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.log_lock = threading.Lock()  # 初始化线程锁
        self.browser_manager = BrowserManager(max_browsers=10)
        self.threads_running = False
        self.initUI()
        self.load_initial_configs()
        self.load_proxy_template()


    def initUI(self):
        main_layout = QVBoxLayout(self)
        menu_bar = self.create_menu_bar()
        main_layout.setMenuBar(menu_bar)

        first_row_layout = self.create_first_row()
        main_layout.addLayout(first_row_layout)

        second_row_layout = self.create_second_row()
        main_layout.addLayout(second_row_layout)

        self.log_output = QTextEdit(self)
        self.log_output.setReadOnly(True)
        main_layout.addWidget(self.log_output)

        self.setLayout(main_layout)
        self.setWindowTitle('自动化业务流程')
        self.setGeometry(100, 100, 1500, 1200)
        self.show()

    def create_menu_bar(self):
        menu_bar = QMenuBar(self)
        file_menu = menu_bar.addMenu('文件')
        self.add_menu_action(file_menu, '保存更改', self.save_all_configs)
        self.add_menu_action(file_menu, '导入账号', self.import_accounts)
        self.add_menu_action(file_menu, '导入商品列表', self.import_products)

        return menu_bar

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

    def add_menu_action(self, menu, title, callback):
        action = QAction(title, self)
        action.triggered.connect(callback)
        menu.addAction(action)

    def show_product_menu(self, position):
        menu = QMenu()
        modify_action = QAction('修改', self)
        modify_action.triggered.connect(lambda: self.modify_cell(self.product_table))
        menu.addAction(modify_action)

        delete_action = QAction('删除', self)
        delete_action.triggered.connect(lambda: self.delete_row(self.product_table))
        menu.addAction(delete_action)

        menu.exec_(self.product_table.viewport().mapToGlobal(position))

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


    def create_first_row(self):
        first_row_layout = QHBoxLayout()

        self.account_table = self.create_table(3, ['邮箱', '密码', '注册状态'])
        first_row_layout.addWidget(self.account_table)
        self.account_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.account_table.customContextMenuRequested.connect(self.show_account_menu)
        proxy_group = self.create_proxy_group()
        first_row_layout.addWidget(proxy_group)

        self.product_table = self.create_table(3, ['标题', '价格', '链接地址'])
        self.product_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.product_table.customContextMenuRequested.connect(self.show_product_menu)
        first_row_layout.addWidget(self.product_table)


        return first_row_layout

    def create_second_row(self):
        second_row_layout = QHBoxLayout()

        browser_management_group = self.create_browser_management_group()
        second_row_layout.addWidget(browser_management_group)

        # thread_config_group = self.create_thread_config_group()
        # second_row_layout.addWidget(thread_config_group)

        settings_group = self.create_settings_group()
        second_row_layout.addWidget(settings_group)

        thread_status_group = self.create_thread_status_group()
        second_row_layout.addWidget(thread_status_group)

        return second_row_layout

    def create_table(self, column_count, headers):
        table = QTableWidget()
        table.setColumnCount(column_count)
        table.setHorizontalHeaderLabels(headers)
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        return table

    def create_proxy_group(self):
        proxy_group = QGroupBox("代理设置")
        proxy_layout = QVBoxLayout()

        self.proxy_template_input = QTextEdit(self)
        self.proxy_template_input.setPlaceholderText(
            "输入代理模板，例如：proxy.ipipgo.com:31212:customer-abd5da6e-country-{country}-region-{region}-city-{city}-session-xxxx-time-3:password"
        )
        self.proxy_template_input.setFixedHeight(140)
        proxy_layout.addWidget(QLabel("城市使用变量{city}，省份使用：{region}"))
        proxy_layout.addWidget(self.proxy_template_input)

        self.save_proxy_button = QPushButton("保存代理模板", self)
        self.save_proxy_button.clicked.connect(self.save_all_configs)
        proxy_layout.addWidget(self.save_proxy_button)

        proxy_group.setLayout(proxy_layout)
        return proxy_group

    def create_browser_management_group(self):
        group = QGroupBox("浏览器管理")
        layout = QVBoxLayout()

        self.max_browsers_spinbox = self.create_spinbox(1, 100, self.browser_manager.max_browsers, self.set_max_browsers)
        layout.addWidget(QLabel("最大浏览器数量:"))
        layout.addWidget(self.max_browsers_spinbox)

        self.browser_list_table = self.create_table(2, ['线程名', '浏览器ID'])
        layout.addWidget(self.browser_list_table)
        self.browser_manager.browser_list_updated.connect(self.update_browser_list)

        group.setLayout(layout)
        return group

    # def create_thread_config_group(self):
    #     group = QGroupBox("线程配置")
    #     layout = QVBoxLayout()
    #
    #
    #
    #     group.setLayout(layout)
    #     return group

    def create_settings_group(self):
        group = QGroupBox("设置参数区域")
        layout = QVBoxLayout()

        self.param_input = QLineEdit(self)
        self.param_input.setPlaceholderText("输入参数")
        layout.addWidget(self.param_input)

        self.start_monitor_button = QPushButton("启动监听线程数量")
        self.start_monitor_button.clicked.connect(self.start_monitor)
        layout.addWidget(self.start_monitor_button)

        self.thread_spinbox = self.create_spinbox(1, 100, 10)
        layout.addWidget(QLabel("线程数量:"))
        layout.addWidget(self.thread_spinbox)

        self.start_registration_button = QPushButton("开始注册")
        self.start_registration_button.clicked.connect(self.start_registration)
        layout.addWidget(self.start_registration_button)

        self.toggle_threads_button = QPushButton("启动线程")
        self.toggle_threads_button.clicked.connect(self.toggle_threads)
        layout.addWidget(self.toggle_threads_button)

        group.setLayout(layout)
        return group

    def create_thread_status_group(self):
        group = QGroupBox("线程执行状态")
        layout = QVBoxLayout()

        self.thread_status_table = self.create_table(2, ['线程名', '状态'])
        layout.addWidget(self.thread_status_table)

        group.setLayout(layout)
        return group

    def create_spinbox(self, min_value, max_value, default_value, callback=None):
        spinbox = QSpinBox()
        spinbox.setRange(min_value, max_value)
        spinbox.setValue(default_value)
        if callback:
            spinbox.valueChanged.connect(callback)
        return spinbox

    def load_proxy_template(self):
        try:
            proxy_template = load_config('proxies.json').get('proxy_template', '')
            self.proxy_template_input.setText(proxy_template)
            self.log("代理模板已加载")
        except Exception as e:
            self.log(f"加载代理模板时出错: {str(e)}")

    def save_all_configs(self):
        try:
            self.save_config_file('accounts.json', self.get_table_data(self.account_table, ['email', 'password', 'status']))
            self.save_config_file('links.json', self.get_table_data(self.product_table, ['title', 'price', 'link']))
            self.save_config_file('proxies.json', {'proxy_template': self.proxy_template_input.toPlainText()})
            self.log("所有配置文件已保存")
        except Exception as e:
            self.log(f"保存配置文件时出错: {str(e)}")

    def save_config_file(self, file_name, data):
        save_config(data, file_name)

    def get_table_data(self, table, keys):
        data = []
        for row in range(table.rowCount()):
            row_data = {}
            for i, key in enumerate(keys):
                row_data[key] = table.item(row, i).text()
            data.append(row_data)
        return data

    def import_accounts(self):
        self.import_file('选择包含账号和密码的文件', self.parse_accounts, self.add_accounts_to_table)

    def import_products(self):
        self.import_file('选择包含商品列表的文件', self.parse_products, self.add_products_to_table)

    def import_file(self, title, parse_callback, add_callback):
        file_name, _ = QFileDialog.getOpenFileName(self, title, "", "Text Files (*.txt);;All Files (*)")
        if file_name:
            with open(file_name, 'r', encoding='utf-8') as f:
                content = f.read()
            items = parse_callback(content)
            add_callback(items)
            self.save_all_configs()

    def parse_accounts(self, input_string):
        return self.parse_items(input_string, 'email', 'password', '----')

    def parse_products(self, input_string):
        return self.parse_items(input_string, 'url', 'price', '----')

    def parse_items(self, input_string, key1, key2, delimiter):
        items = []
        lines = input_string.strip().split('\n')
        for line in lines:
            if delimiter in line:
                part1, part2 = line.split(delimiter)
                items.append({key1: part1.strip(), key2: part2.strip()})
        return items

    def add_accounts_to_table(self, accounts):
        self.add_items_to_table(self.account_table, accounts, ['email', 'password', 'status'], default_status='未注册')

    def add_products_to_table(self, products):
        self.add_items_to_table(self.product_table, products, ['url', 'price', 'link'])

    def add_items_to_table(self, table, items, keys, default_status=None):
        current_row_count = table.rowCount()
        table.setRowCount(current_row_count + len(items))
        for i, item in enumerate(items):
            for j, key in enumerate(keys):
                table.setItem(current_row_count + i, j, QTableWidgetItem(item.get(key, default_status)))

    def load_initial_configs(self):
        self.load_table_data('accounts.json', self.account_table, ['email', 'password', 'status'])
        self.load_table_data('links.json', self.product_table, ['title', 'price', 'link'])

    def load_table_data(self, file_name, table, keys):
        try:
            items = load_config(file_name)
            table.setRowCount(len(items))
            for row, item in enumerate(items):
                for i, key in enumerate(keys):
                    table.setItem(row, i, QTableWidgetItem(item.get(key, '')))
            self.log(f"自动加载了 {len(items)} 个记录从 {file_name}")
        except Exception as e:
            self.log(f"加载 {file_name} 时出错: {str(e)}")

    def start_registration(self):
        self.threads_running = True
        self.toggle_threads_button.setText("停止线程")
        thread_count = self.thread_spinbox.value()
        self.thread_status_table.setRowCount(thread_count)
        self.registration_worker = RegistrationWorker(
            self.account_table,
            thread_count,
            self.log,
            self.browser_manager
        )
        # self.connect_registration_worker_signals()
        self.registration_worker.start()

    # def connect_registration_worker_signals(self):
        # self.registration_worker.update_status.connect(self.update_thread_status)
        # self.registration_worker.reload_table.connect(self.load_initial_configs)
        # self.registration_worker.save_configs_signal.connect(self.save_all_configs)
        # self.registration_worker.log_signal.connect(self.log)

    def update_thread_status(self, thread_index, status_message):
        thread_name = f"线程{thread_index + 1}"
        self.thread_status_table.setItem(thread_index, 0, QTableWidgetItem(thread_name))
        self.thread_status_table.setItem(thread_index, 1, QTableWidgetItem(status_message))

    def start_monitor(self):
        threads = self.registration_worker.get_threads()
        for i, thread in enumerate(threads):
            status = "运行中" if thread.is_alive() else "已完成"
            self.update_thread_status(i, status)

    def log(self, message):
        with self.log_lock:  # 使用线程锁保护日志记录
            self.log_output.append(message)
            logging.info(message)
        # print(message)

    def set_max_browsers(self):
        self.browser_manager.set_max_browsers(self.max_browsers_spinbox.value())

    def update_browser_list(self):
        self.update_table(self.browser_list_table, self.browser_manager.get_allocated_browsers())

    def update_table(self, table, data):
        table.setRowCount(len(data))
        for i, (key, value) in enumerate(data.items()):
            table.setItem(i, 0, QTableWidgetItem(key))
            table.setItem(i, 1, QTableWidgetItem(value))

    def stop_threads(self):
        self.threads_running = False
        self.toggle_threads_button.setText("启动线程")
        if hasattr(self, 'registration_worker') and self.registration_worker.isRunning():
            self.registration_worker.stop()

    def toggle_threads(self):
        if self.threads_running:
            self.stop_threads()
        else:
            self.start_registration()

def run_app():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run_app()
