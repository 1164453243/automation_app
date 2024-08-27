import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import logging

# 从 bit_api 导入 openBrowser（假设 bit_api 已实现）
from app.email_code import getCodeAndUrl


def register_account(self,driver,email, password, other_password):
    logging.info("Starting the registration process.")
    try:
        # 等待页面加载并查找输入框
        wait = WebDriverWait(driver, 10)

        # 填写 Email
        email_field = wait.until(EC.visibility_of_element_located((By.NAME, 'email')))
        email_field.send_keys(email)

        # 填写 Password
        password_field = wait.until(EC.visibility_of_element_located((By.NAME, 'password')))
        password_field.send_keys(other_password)

        # 点击注册按钮
        # time.sleep(1)
        # 勾选 "registration" 复选框
        try:
            registration_checkbox = driver.find_element(By.NAME, 'registration')
            if not registration_checkbox.is_selected():
                registration_checkbox.click()
            # cookies_checkbox = driver.find_element(By.NAME, 'cookies')
            # if not cookies_checkbox.is_selected():
            #     cookies_checkbox.click()
        except Exception as e:
            self.log(f"注册复选框未找到或无法点击，继续执行。Error: {str(e)}")

        # 点击注册按钮
        time.sleep(3)

        submit_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@class, 'indexes__Button') and text()='Create account']")))
        submit_button.click()

        # 检查是否存在 "The email has already been taken." 提示
        try:
            error_message_element = wait.until(EC.visibility_of_element_located(
                (By.XPATH,
                 "//div[@class='sc-ellfGf blLHlf']//span[contains(@class, 'sc-iqAclL')]")
            ))
            error_message = error_message_element.text
            self.log(f"{email} - 注册失败，提示信息: {error_message}")
            return  '' # 如果提示存在，则停止后续操作
        except Exception:
            self.log(f"{email} - 未发现重复注册提示，继续进行。")




        # 获取邮箱验证码
        self.log(f"{email} - 获取邮箱验证码")
        verification_code, url = getCodeAndUrl(email, password, 0)

        # 等待验证码输入框出现并输入验证码 "123456"
        try:
            time.sleep(3)  # 等待页面加载验证码输入框
            for i in range(6):
                input_box = wait.until(EC.visibility_of_element_located((By.NAME, f'val_{i}')))
                input_box.send_keys(verification_code[i])
            self.log(f"{email} - 验证码输入成功")
        except Exception as e:
            self.log(f"{email} - 验证码输入失败。Error: {str(e)}")

    except Exception as e:
        logging.error(f"An error occurred during registration: {e}")
    finally:
        time.sleep(5)

