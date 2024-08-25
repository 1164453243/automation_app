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

def handle_payment(driver, wait):
    try:
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
        visa_option = wait.until(
            EC.element_to_be_clickable((By.XPATH, '(//label[contains(@class, "jtcpKe")])[1]')))
        visa_option.click()

        sleep(1)
        # 点击确认支付按钮
        confirm_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, '(//button[contains(@class,"sc-iCoGMd")])[1]')))
        confirm_button.click()

    except Exception as e:
        print(f"An error occurred during the payment process: {e}")
        raise
