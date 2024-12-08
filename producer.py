import pika
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import socket
import ssl
import json

# 1 if use socket, 0 for library
use_socket = 0

base_url = 'https://999.md'
url = '/ro/list/transport/cars'
host = '999.md'

def send_to_rabbitmq(data):
    print("&&&&&&&&&&&&&&&&&&&&&&&")
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='car_listings')

    channel.basic_publish(exchange='', routing_key='car_listings', body=json.dumps(data))

    print(f"Sent data to RabbitMQ: {data}")
    connection.close()

def http_request_lib(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Fail: {response.status_code}")
    return response.text

def socket_request(host, url_path):
    port = 443
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    context = ssl.create_default_context()
    secure_socket = context.wrap_socket(client_socket, server_hostname=host)
    secure_socket.connect((host, port))
    http_request = f"GET {url_path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
    secure_socket.sendall(http_request.encode())
    response_data = b""
    while True:
        data = secure_socket.recv(4096)
        if not data:
            break
        response_data += data
    secure_socket.close()
    return response_data.decode('utf-8')

soup = ""
if use_socket == 1:
    soup = BeautifulSoup(socket_request(host, url), 'html.parser')
else:
    soup = BeautifulSoup(http_request_lib(base_url + url), 'html.parser')

bad_value = None
cars = []

# Scraping and data extraction logic
for item in soup.find_all('li', class_='ads-list-photo-item'):
    name_tag = item.find('div', class_='ads-list-photo-item-title')
    name = name_tag.get_text(strip=True) if name_tag else bad_value
    price = bad_value
    km = bad_value
    price_tag = item.find('div', class_='ads-list-photo-item-price')
    if price_tag:
        price_parts = price_tag.get_text(strip=True).split('\xa0')
        price = price_parts[0]
        km_tag = price_tag.find('div', class_='is-offer-type')
        km = km_tag.get_text(strip=True) if km_tag else bad_value

    href_tag = item.find('a', class_='js-item-ad')
    href = href_tag['href'] if href_tag and 'href' in href_tag.attrs else bad_value
    full_url = base_url + href if href != bad_value else bad_value

    cars.append({
        'name': name,
        'price': price,
        'km': km,
        'url': full_url,
    })

test_data = cars[0:3]

# Now that we have the data, we can send it to RabbitMQ
for car in test_data:
    if car['url'] != bad_value:
        detail_response = requests.get(car['url'])
        if detail_response.status_code != 200:
            print(f"Failed to fetch details for {car['name']}. Status code: {detail_response.status_code}")
            continue

        detail_soup = BeautifulSoup(detail_response.text, 'html.parser')

        update_date_tag = detail_soup.find('div', class_='adPage__aside__stats__date')
        update_date = update_date_tag.get_text(strip=True) if update_date_tag else bad_value

        type_tag = detail_soup.find('div', class_='adPage__aside__stats__type')
        car_type = type_tag.get_text(strip=True).replace('Tipul: ', '') if type_tag else bad_value

        views_tag = detail_soup.find('div', class_='adPage__aside__stats__views')
        views = views_tag.get_text(strip=True).replace('Vizualizări: ', '') if views_tag else bad_value

        currency_tag = detail_soup.find('span', class_='adPage__content__price-feature__prices__price__currency')
        currency = bad_value
        if currency_tag:
            currency = currency_tag.get_text(strip=True) if currency_tag else bad_value

        car.update({
            "currency": currency,
            "updateDate": update_date,
            "type": car_type,
            "views": views
        })

print("----------------------------")
# Send the formatted data to RabbitMQ
send_to_rabbitmq(test_data)

