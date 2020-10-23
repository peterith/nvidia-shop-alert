import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchWindowException, WebDriverException
import requests
import datetime
import json

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
NVIDIA_URL = "https://www.nvidia.com/en-gb/shop/geforce/?page=1&limit=9&locale=en-gb&gpu=RTX%203080&manufacturer=NVIDIA&manufacturer_filter=NVIDIA~1,3XS%20SYSTEMS~0,ACER~0,ASUS~3,DELL~0,EVGA~4,GAINWARD~0,GIGABYTE~3,HP~0,LENOVO~0,MEDION~0,MSI~2,NOVATECH~0,PALIT~2,PNY~1,RAZER~0,ZOTAC~3"
WEB_DRIVER_MAX_GET_RETRIES = 50
WEB_DRIVER_WAIT_TIMEOUT = 5
BUTTON_CLASS_NAME = "featured-buy-link"
BUTTON_LABEL = "OUT OF STOCK"


class WebDriver:
    def __init__(self, options):
        self.driver = webdriver.Firefox(options=options)
        self.options = options
        self.counter = 0

    def load_page_and_find_buy_button(self):
        if self.counter > WEB_DRIVER_MAX_GET_RETRIES:
            self.restart_driver()
        self.counter = self.counter + 1
        self.driver.get(NVIDIA_URL)
        return WebDriverWait(self.driver, WEB_DRIVER_WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, BUTTON_CLASS_NAME)))

    def restart_driver(self):
        self.counter = 0
        self.driver.quit()
        self.driver = webdriver.Firefox(options=self.options)


class Alert:
    def __init__(self, message, threshold=0):
        self.message = message
        self.threshold = threshold
        self.timestamps = []

    def alert(self):
        current_datetime = datetime.datetime.now()
        self.adjust_timestamps(current_datetime.timestamp())

        if len(self.timestamps) > self.threshold:
            result = requests.post(DISCORD_WEBHOOK_URL, headers={
                                   "Content-Type": "application/json"}, data=json.dumps({"content": f"{current_datetime}: {self.message}"}))
        print(f"{current_datetime}: {self.message}")

    def adjust_timestamps(self, timestamp):
        self.timestamps.append(timestamp)
        self.timestamps = [i for i in self.timestamps if i > timestamp - 60]


class InfoPrinter:
    def __init__(self, interval):
        self.interval = interval
        self.loop_count = 0
        self.out_of_stock = 0
        self.in_stock = 0

    def print(self):
        self.loop_count = self.loop_count + 1
        if self.loop_count == self.interval:
            current_datetime = datetime.datetime.now()
            self.loop_count = 0
            print(f"{current_datetime}: Out of stock count: {self.out_of_stock}")
            print(f"{current_datetime}: In stock count: {self.in_stock}")


def main():
    options = Options()
    options.headless = True
    web_driver = WebDriver(options)
    availability_alert = Alert(f"Nvidia 3080 FE in stock! {NVIDIA_URL}")
    timeout_alert = Alert("TimeoutException", 3)
    info = InfoPrinter(WEB_DRIVER_MAX_GET_RETRIES)

    while True:
        try:
            current_datetime = datetime.datetime.now()
            element = web_driver.load_page_and_find_buy_button()
            if element.text == BUTTON_LABEL:
                info.out_of_stock = info.out_of_stock + 1
            else:
                info.in_stock = info.in_stock + 1
                print(f"{current_datetime}: Button changed to {element.text}")
                availability_alert.alert()
            info.print()
        except TimeoutException:
            timeout_alert.alert()
        except Exception as error:
            print(f"{current_datetime}: {error}")
            web_driver.restart_driver()


if __name__ == "__main__":
    main()
