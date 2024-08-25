import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
import logging

# 从 bit_api 导入 openBrowser（假设 bit_api 已实现）
from app.bit_api import openBrowser

def register_account(email, password, verification_code):
    logging.info("Starting the registration process.")

    # 使用 openBrowser 打开浏览器并获取相关参数
    res = openBrowser("46051e012fb74d419a0bbaa07d7afed7")

    driverPath = res['data']['driver']
    debuggerAddress = res['data']['http']

    # 设置 Chrome 选项
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("debuggerAddress", debuggerAddress)

    # 使用获取的路径和选项启动浏览器
    # chrome_service = Service(driverPath)
    # driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    driver = webdriver.Chrome(executable_path=driverPath, options=chrome_options)
    try:
        # 打开目标注册页面
        driver.get('https://login.g2a.com/register-page?redirect_uri=https%3A%2F%2Fwww.g2a.com%2F&source=topbar')
        driver.implicitly_wait(10)

        # 等待页面加载并查找输入框
        wait = WebDriverWait(driver, 10)

        # 填写 Email
        email_field = wait.until(EC.visibility_of_element_located((By.NAME, 'email')))
        email_field.send_keys(email)

        # 填写 Password
        password_field = wait.until(EC.visibility_of_element_located((By.NAME, 'password')))
        password_field.send_keys(password)

        logging.info("Email and password filled.")

        # 勾选 "registration" 复选框
        try:
            registration_checkbox = driver.find_element(By.NAME, 'registration')
            if not registration_checkbox.is_selected():
                registration_checkbox.click()
            logging.info("Registration checkbox selected.")
        except Exception as e:
            logging.warning(f"Registration checkbox not found or not clickable: {e}")
        time.sleep(3)
        # 点击注册按钮
        submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'indexes__Button') and text()='Create account']")))
        submit_button.click()
        logging.info("Registration button clicked.")

        # 等待验证码输入框出现并输入验证码
        time.sleep(3)  # 等待页面加载验证码输入框
        for i in range(6):
            input_box = wait.until(EC.visibility_of_element_located((By.NAME, f'val_{i}')))
            input_box.send_keys(verification_code[i])
        logging.info("Verification code entered successfully.")

    except Exception as e:
        logging.error(f"An error occurred during registration: {e}")
    finally:
        input("Press Enter to close the browser...")
        driver.quit()
        logging.info("Browser closed after registration.")

