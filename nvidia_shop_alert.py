import os
from colorama import init, Fore, Style
from dotenv import load_dotenv
import requests
import datetime
import json
import time
import html

init()
load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
GPUs = os.getenv('GPUS') or '3070,3080,3090'
FETCH_INTERVAL = os.getenv('FETCH_INTERVAL') or 2
NVIDIA_URL = 'https://api.nvidia.partners/edge/product/search?page=1&limit=9&locale=en-gb&manufacturer=NVIDIA'
SKU_MAP = {'3070': 'NVGFT070', '3080': 'NVGFT080', '3090': 'NVGFT090'}


def get_SKUs():
    gpus = GPUs.split(',')
    return [SKU_MAP[i] for i in gpus]


def alert_on_discord(message):
    requests.post(DISCORD_WEBHOOK_URL, headers={
                  'Content-Type': 'application/json'}, data=json.dumps({'content': message}))


def check_availability(product):
    current_time = datetime.datetime.now()
    if product['prdStatus'] == 'out_of_stock':
        print(
            f"{current_time}: {product['productTitle']} {Fore.RED}out of stock{Style.RESET_ALL}")
    else:
        message = f"{current_time}: {product['productTitle']} {Fore.GREEN}in stock{Style.RESET_ALL}"
        print(message)
        alert_on_discord(message)
        for i in product['retailers']:
            link = html.unescape(i['purchaseLink'])
            print(link)
            alert_on_discord(link)


def main():
    skus = get_SKUs()
    while True:
        response = requests.get(NVIDIA_URL, headers={
                                'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36'})
        data = response.json()
        products = data['searchedProducts']
        featured_product = products['featuredProduct']
        if (featured_product and featured_product['productSKU'] in skus):
            check_availability(featured_product)
        for i in products['productDetails']:
            if (i['productSKU'] in skus):
                check_availability(i)
        time.sleep(FETCH_INTERVAL)


if __name__ == '__main__':
    main()
