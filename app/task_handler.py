import requests
import time

def get_task(token):
    url = f"https://www.savestamp.com/api/get_and_update_random_order.php?token={token}"
    while True:
        response = requests.get(url)
        if response.status_code == 200 and response.json():
            task_data = response.json()
            return task_data
        else:
            print("No tasks available. Retrying in 10 seconds...")
            time.sleep(10)
