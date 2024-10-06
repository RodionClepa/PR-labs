import requests
from bs4 import BeautifulSoup
from pprint import pprint  # For pretty print
import re
from datetime import datetime, timezone
from functools import reduce
import socket
import ssl

# 1 if use socket, 0 for library
use_socket = 0

base_url = 'https://999.md'
url = '/ro/list/transport/cars'
host = '999.md'

def http_request_lib(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Fail: {response.status_code}")

    return response.text

def socket_request(host, url_path):
    port = 443  # HTTPS port, server port we try to access

    # Create a TCP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    context = ssl.create_default_context()

    # Wrap the socket to add SSL (for HTTPS)
    secure_socket = context.wrap_socket(client_socket, server_hostname=host)

    # Connect to the host on port value
    secure_socket.connect((host, port))

    # Create the HTTP GET request
    http_request = f"GET {url_path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
    # \r\n useed to separate different parts of HTTP request
    # GET /ro/list/transport/cars 
    # HTTP/1.1 - The version of the HTTP protocol being used
    # Host: 999.md
    # Connection: close - to ensure the server close connection after sending the response

    # Send the request
    secure_socket.sendall(http_request.encode())

    # Receive the response
    response_data = b"" # Empty byte string
    while True:
        data = secure_socket.recv(4096)  # Receive in chunks of 4096 bytes
        if not data:
            break
        response_data += data

    # Close the socket
    secure_socket.close()

    # Decode the response (assuming the server uses UTF-8)
    response_text = response_data.decode('utf-8')

    # Split response into headers and body
    headers, body = response_text.split("\r\n\r\n", 1) # 1 to split only once

    # Print headers to verify the response
    print(headers)
    return body

soup = ""
if use_socket == 1:
    soup = BeautifulSoup(socket_request(host, url), 'html.parser')
else:
    soup = BeautifulSoup(http_request_lib(base_url+url), 'html.parser')

# For none data
bad_value = None

cars = []

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

# for car in cars:
#     print(car)

test_data = cars[0:10]

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

# Page detail
# print('&&&&&&&&&&&&&&&&&&&& PAGE DETAIL &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
# pprint(test_data)

def format_and_validate_data(cars_data):
    formatted_data = []

    for car in cars_data:
        print(car)
        if car['name'] is None: # bad data
            continue
        if 'token' in car['url']:
            continue
        formatted_car = {
            'name': car['name'],
            'price': format_price(car['price']),
            'currency': format_currency(car['currency']),
            'km': format_km(car['km']),
            'url': format_url(car['url']),
            'updateDate': format_date(format_update_date(car['updateDate'])),
            'type': car['type'],
            'views': format_views(car['views'])
        }

        formatted_data.append(formatted_car)

    return formatted_data

def format_price(price):
    if price is None:
        return None
    if price == 'Negociabil':
        return None
    price_cleaned = re.sub(r'\s+', '', price)
    return price_cleaned if price_cleaned.isdigit() else None

def format_currency(currency):
    if currency is None:
        return None

    map_curr = {
        "€": "EUR",
        "$": "USD",
        "lei": "MDL"
    }
    print(currency)
    return map_curr[currency]

def format_km(km):
    if km is None:
        return None
    km_value = re.findall(r'\d+', km)
    return ' '.join(km_value) + ' km' if km_value else None

def format_url(url):
    if re.match(r'https?://[^\s]+', url):
        return url
    return 'Invalid URL'

def format_update_date(update_date):
    return update_date.replace('Data actualizării:', '').strip()

def format_date(date_string):
    input_format = "%d %b %Y, %H:%M"
    
    output_format = "%A, %B %d, %Y at %I:%M %p"
    
    date_string = date_string.replace('oct.', 'Oct')
    
    try:
        parsed_date = datetime.strptime(date_string, input_format)
        return parsed_date.strftime(output_format)
    except ValueError as e:
        print(f"Error parsing date: {e}")
        return None

def format_views(views):
    print(views)
    views = views.replace(" ", "")
    views = views[:views.find("(")-1]
    return views

print('&&&&&&&&&&&&&&&&&&&& VALIDATION &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
formatted_cars = format_and_validate_data(test_data)

for car in formatted_cars:
    pprint(car)

print('&&&&&&&&&&&&&&&&&&&& MAPPING/FILTER/REDUCE &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
EUR_TO_MDL_RATE = 20

def convert_price(price, currency):
    if currency == 'EUR':
        return int(price) * EUR_TO_MDL_RATE
    elif currency == 'MDL':
        return int(price) / EUR_TO_MDL_RATE
    return None

formatted_cars = list(map(lambda car: {
    **car, 
    'price': convert_price(car['price'], car['currency']), 
    'currency': 'MDL'
} if car['price'] is not None else car, formatted_cars))

categories = [
    {
        "startRange": 1000,
        "endRange": 60000,
        "cars": []
    },
    {
        "startRange": 60000,
        "endRange": 150000,
        "cars": []
    },
    {
        "startRange": 150000,
        "endRange": 250000,
        "cars": []
    },
    {
        "startRange": 250000,
        "endRange": 350000,
        "cars": []
    },
    {
        "startRange": 350000,
        "endRange": 450000,
        "cars": []
    },
    {
        "startRange": 450000,
        "endRange": 99999999,
        "cars": []
    }
]

def categorize_cars(cars):
    for category in categories:
        filtered_cars = list(filter(lambda car: car['price'] is not None and 
                                         category["startRange"] <= int(car['price']) <= category["endRange"], 
                                        cars))
        
        category["cars"] = filtered_cars

        category["totalPrice"] = reduce(lambda acc, car: acc + int(car['price']), filtered_cars, 0)
        
        category["timestamp"] = datetime.now(timezone.utc).isoformat()

categorize_cars(formatted_cars)

for category in categories:
    print(f"Price Range: {category['startRange']} - {category['endRange']}")
    print(f"{category['timestamp']} - Total Price: {category['totalPrice']} MDL")
    for car in category['cars']:
        pprint(car)

def serialize_categories_to_json(categories_data):
    json_output = '['
    for category in categories_data:
        json_output += '{'
        json_output += f'"startRange": {category["startRange"]}, '
        json_output += f'"endRange": {category["endRange"]}, '
        json_output += f'"totalPrice": {category["totalPrice"] if category["totalPrice"] is not None else 0}, '
        json_output += f'"timestamp": "{category["timestamp"]}", '
        json_output += '"cars": ['

        for i, car in enumerate(category["cars"]):
            json_output += '{'
            json_output += f'"name": "{car["name"]}", '
            json_output += f'"price": {car["price"]}, '
            json_output += f'"currency": "{car["currency"]}", '
            json_output += f'"km": "{car["km"]}", '
            json_output += f'"url": "{car["url"]}", '
            json_output += f'"updateDate": "{car["updateDate"]}", '
            json_output += f'"type": "{car["type"]}", '
            json_output += f'"views": "{car["views"]}"'
            json_output += '}'
            if i < len(category["cars"]) - 1:
                json_output += ', '

        json_output += ']'
        json_output += '}'
        if category != categories_data[-1]:
            json_output += ', '
    
    json_output += ']'
    return json_output

# JSON
json_categories_data = serialize_categories_to_json(categories)
with open('categories.json', 'w', encoding='utf-8') as file:
    file.write(json_categories_data)

# JSON validator
# https://jsonformatter.curiousconcept.com/#
print("JSON Categories Output:")
print(json_categories_data)

# XML
def serialize_categories_to_xml(categories_data):
    xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n<categories>\n'

    for category in categories_data:
        xml_output += '  <category>\n'
        xml_output += f'    <startRange>{category["startRange"]}</startRange>\n'
        xml_output += f'    <endRange>{category["endRange"]}</endRange>\n'
        xml_output += f'    <totalPrice>{category["totalPrice"] if category["totalPrice"] is not None else 0}</totalPrice>\n'
        xml_output += f'    <timestamp>{category["timestamp"]}</timestamp>\n'
        xml_output += '    <cars>\n'

        for car in category["cars"]:
            xml_output += '      <car>\n'
            xml_output += f'        <name>{car["name"]}</name>\n'
            xml_output += f'        <price>{car["price"]}</price>\n'
            xml_output += f'        <currency>{car["currency"]}</currency>\n'
            xml_output += f'        <km>{car["km"]}</km>\n'
            xml_output += f'        <url>{car["url"]}</url>\n'
            xml_output += f'        <updateDate>{car["updateDate"]}</updateDate>\n'
            xml_output += f'        <type>{car["type"]}</type>\n'
            xml_output += f'        <views>{car["views"]}</views>\n'
            xml_output += '      </car>\n'

        xml_output += '    </cars>\n'
        xml_output += '  </category>\n'

    xml_output += '</categories>'
    return xml_output


xml_categories_data = serialize_categories_to_xml(categories)
with open('categories.xml', 'w', encoding='utf-8') as file:
    file.write(xml_categories_data)

# XML validator
# https://jsonformatter.org/xml-viewer
print("XML Categories Output:")
print(xml_categories_data)