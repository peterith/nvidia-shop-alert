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
FETCH_INTERVAL = int(os.getenv('FETCH_INTERVAL')) or 2
NVIDIA_URL = 'https://api.nvidia.partners/edge/product/search?page=1&limit=9&locale=en-gb&manufacturer=NVIDIA'
HEADERS = {
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36'}
statuses = {}
links = {}


def main():
    while True:
        response = requests.get(NVIDIA_URL, headers=HEADERS)
        data = response.json()
        products = data['searchedProducts']
        featured_product = products['featuredProduct']
        if (featured_product):
            check_availability(featured_product)
        for i in products['productDetails']:
            check_availability(i)
        time.sleep(FETCH_INTERVAL)


def check_availability(product):
    if product['productSKU'] not in statuses:
        initialise_product(product)
    check_status(product)
    check_retailers(product)


def initialise_product(product):
    statuses[product['productSKU']] = 'out_of_stock'
    links[product['productSKU']] = []


def check_status(product):
    print_status(product)
    if statuses[product['productSKU']] != product['prdStatus']:
        statuses[product['productSKU']] = product['prdStatus']
        alert_on_discord(
            f"{datetime.datetime.now()}: {product['productTitle']} {product['prdStatus']}")


def check_retailers(product):
    current_time = datetime.datetime.now()
    for i in product['retailers']:
        if i['purchaseLink'] not in links[product['productSKU']]:
            links[product['productSKU']].append(i['purchaseLink'])
            link = html.unescape(i['purchaseLink'])
            print(f"{current_time}: {product['productTitle']} link")
            print(link)
            alert_on_discord(link)


def print_status(product):
    colour = Fore.RED if product['prdStatus'] == 'out_of_stock' else Fore.GREEN
    print(
        f"{datetime.datetime.now()}: {product['productTitle']} {colour}{product['prdStatus']}{Style.RESET_ALL}")


def alert_on_discord(message):
    requests.post(DISCORD_WEBHOOK_URL, headers={
                  'Content-Type': 'application/json'}, data=json.dumps({'content': message}))


if __name__ == '__main__':
    main()
