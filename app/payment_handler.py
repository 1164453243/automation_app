import itertools
import json

import requests
from time import sleep

from selenium.webdriver.support.select import Select

from app.config_handler import load_config, save_config
from selenium.webdriver import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def update_payment_status(order_id, state):
    url = f"https://www.savestamp.com/api/update_order_status.php?order_id={order_id}&state={state}&token=123456"
    response = requests.get(url)
    if response.status_code == 200:
        print("Payment status updated successfully.")
    else:
        print("Failed to update payment status.")

def handle_payment(self,driver,card_info):
    try:
        # self.log("abc")
        wait = WebDriverWait(driver, 10)
        # 打印页面源代码以帮助调试
        #print(driver.page_source)

        # 输入银行卡金额
        price = card_info['price']

        # # 填写价格 From
        # price_from = wait.until(EC.visibility_of_element_located((By.NAME, 'min')))
        # price_from.clear()  # 清除默认值
        # price_from.send_keys(price-10)  # 输入起始价格
        # price_from.send_keys(Keys.RETURN)  # 按下回车键
        #
        # # 填写价格 To
        # price_to = wait.until(EC.visibility_of_element_located((By.NAME, 'max')))
        # price_to.clear()  # 清除默认值
        # price_to.send_keys(price)  # 输入结束价格
        # price_to.send_keys(Keys.RETURN)  # 按下回车键

        # sleep(2)
        #
        # # 等待商品列表加载完成并点击第一个商品
        # first_product = wait.until(EC.element_to_be_clickable((By.XPATH, '(//a[contains(@class, "sc-jQAxuV")])[1]')))
        # first_product.click()
        #
        # sleep(2)
        # # 等待 "Add to cart" 按钮出现并点击它
        # add_to_cart_button = wait.until(
        #     EC.element_to_be_clickable((By.XPATH, '//button[@data-locator="ppa-payment__btn"]')))
        # add_to_cart_button.click()
        #
        # sleep(2)
        # # 点击继续购物车按钮
        # continue_button = wait.until(
        #     EC.element_to_be_clickable((By.XPATH, '//button[@data-event="cart-continue"]')))
        # continue_button.click()

        handle_registration_and_add_to_cart(self,driver,'',price);


        driver.get('https://www.g2a.com/page/cart')
        sleep(2)

        ##跳转支付页面
        # 点击继续购物车按钮
        continue_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//button[@data-event="cart-continue"]')))
        continue_button.click()



        sleep(2)
        # 选择支付方式（例如 Visa）
        # visa_option = wait.until(
        #     EC.element_to_be_clickable((By.XPATH, '(//label[contains(@class, "jtcpKe")])[1]')))
        visa_option = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[contains(@class, 'beTfHe') and text()='Credit or debit card']")))
        visa_option.click()

        sleep(1)
        # 点击确认支付按钮
        confirm_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, '(//button[contains(@class,"sc-iCoGMd")])[1]')))
        confirm_button.click()

        sleep(1)
        # 填卡号
        # 获取 iframe 的 src 并打开它

        iframe_element = wait.until(EC.visibility_of_element_located((By.XPATH,"(//iframe[contains(@class,'indexes__IFrame-sc-1ksp1zs-23 gvYYcB')])[1]")))
        iframe_src = iframe_element.get_attribute('src')
        self.log(f"{iframe_src} - 获取到的支付页面 URL: {iframe_src}")

        # 打开获取到的 URL
        driver.get(iframe_src)

        # 填写支付表单
        try:
            # 等待并获取各个表单元素
            card_number_field = wait.until(EC.visibility_of_element_located((By.ID, "cardNumber")))
            expiry_date_field = wait.until(EC.visibility_of_element_located((By.ID, "expiryDate")))
            cvv_field = wait.until(EC.visibility_of_element_located((By.ID, "cvv")))
            cardholder_name_field = wait.until(EC.visibility_of_element_located((By.ID, "cardHolderName")))

            # 填写表单数据
            card_number_field.send_keys(card_info['card_number'])
            expiry_date_field.send_keys(card_info['expiration_date'][5:7] + "/" + card_info['expiration_date'][2:4])
            cvv_field.send_keys(card_info['security_code'])
            cardholder_name_field.send_keys("Test User")  # 根据需要修改持卡人姓名

            # 提交表单
            submit_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and text()='Confirm']")))
            submit_button.click()

            self.log("第一次支付表单已提交")
            fill_billing_address(driver,card_info)
            self.log("第二次支付表单已提交")
        except Exception as e:
            self.log(f"填写支付表单时出错: {str(e)}")


    except Exception as e:
        print(f"An error occurred during the payment process: {e}")
        raise

#二次填写表单
def fill_billing_address(driver, card_info):
    try:
        wait = WebDriverWait(driver, 10)

        # 等待并获取各个表单元素
        # country_field = wait.until(EC.visibility_of_element_located((By.ID, "avsCountryCode")))
        address_field = wait.until(EC.visibility_of_element_located((By.ID, "address")))
        zip_field = wait.until(EC.visibility_of_element_located((By.ID, "zip")))

        # 填写表单数据
        # select_country = Select(country_field)
        # select_country.select_by_value(card_info['country'])  # 根据国家代码选择国家
        address_field.send_keys(card_info['street'])
        zip_field.send_keys(card_info['postalcode'])

        # 提交表单
        submit_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.btn-block"))
        )
        submit_button.click()

        print("表单填写并提交成功！")

    except Exception as e:
        print(f"填写表单时出错: {str(e)}")


#选择商品逻辑
def handle_registration_and_add_to_cart(self, driver, email, products):
    try:
        # 假设这里是账号注册逻辑，成功后会打印日志
        # 这里加入你自己的账号注册逻辑
        registration_success = True  # 假设注册成功
        if registration_success:
            # 寻找最佳商品组合
            target_amount = products  # 这里可以根据你的实际需求设置目标金额
            best_combination, best_total = find_best_combination(load_products_from_json(), target_amount)

            if best_combination:
                for product in best_combination:
                    # 打开商品链接
                    driver.get(product['link'])
                    self.log(f"打开商品链接: {product['link']}")
                    sleep(1)
                    driver.execute_script("window.scrollTo(0, 1300);")
                    self.log("页面已滚动到底部(滚动到底部按钮才会显示)")

                    sleep(2)

                    # 等待 "Add to cart" 按钮出现并点击它
                    wait = WebDriverWait(driver, 30)
                    add_to_cart_button = wait.until(
                       # EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'ghEko')]"))
                    EC.element_to_be_clickable((By.XPATH, '//button[@data-locator="ppa-payment__btn"]'))
                   # data - locator = "ppa-payment__btn"
                    )
                    try:
                        add_to_cart_button.click()
                    except Exception as e:
                        self.log(f"商品 '{product['title']}'无法找到")

                    self.log(f"已将商品 '{product['title']}' 添加到购物车，总金额: {best_total}")
            else:
                self.log("未找到合适的商品组合，未能加入购物车")
            # 等待一段时间以确保操作完成
            sleep(3)
    except Exception as e:
        self.log(f"处理账号注册和添加商品到购物车时出错: {str(e)}")
        raise

    # 读取 links.json 文件中的商品数据
def load_products_from_json(file_path='links.json'):
        try:

                products = load_config('links.json')
                # 确保价格是浮点数
                for product in products:
                    product['price'] = float(product['price'])
                return products
        except FileNotFoundError:
            print(f"文件 {file_path} 未找到.")
            return []
        except json.JSONDecodeError:
            print("解析 JSON 文件时出错.")
            return []
    # 根据给定的金额寻找最佳商品组合
def find_best_combination(products, target_amount, max_combinations=3):
    best_combination = None
    best_total = 0

    # 遍历所有可能的组合（最多 max_combinations 个商品）
    for r in range(1, max_combinations + 1):
        for combination in itertools.combinations(products, r):
            # 确保所有价格都是浮点数
            total = sum(float(item['price']) for item in combination)
            if best_total < total <= float(target_amount):
                best_combination = combination
                best_total = total
            # 如果已经找到一个完全匹配的组合，直接返回
            if best_total == target_amount:
                return best_combination, best_total

    return best_combination, best_total