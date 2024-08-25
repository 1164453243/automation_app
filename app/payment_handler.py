import requests
from time import sleep
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
        self.log("abc")
        wait = WebDriverWait(driver, 10)
        # 打印页面源代码以帮助调试
        print(driver.page_source)
        sleep(2)

        # 等待商品列表加载完成并点击第一个商品
        first_product = wait.until(EC.element_to_be_clickable((By.XPATH, '(//a[contains(@class, "sc-jQAxuV")])[1]')))
        first_product.click()

        sleep(2)
        # 等待 "Add to cart" 按钮出现并点击它
        add_to_cart_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//button[@data-locator="ppa-payment__btn"]')))
        add_to_cart_button.click()

        sleep(2)
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

            self.log("支付表单已提交")
        except Exception as e:
            self.log(f"填写支付表单时出错: {str(e)}")


    except Exception as e:
        print(f"An error occurred during the payment process: {e}")
        raise
