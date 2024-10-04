import requests
from bs4 import BeautifulSoup
from pprint import pprint # For pretty print

base_url = 'https://999.md'
url = 'https://999.md/ro/list/transport/cars'

response = requests.get(url)
if response.status_code != 200:
    raise Exception(f"Fail: {response.status_code}")

html_content = response.text

soup = BeautifulSoup(html_content, 'html.parser')

# For none data
bad_value = None

cars = []

for item in soup.find_all('li', class_='ads-list-photo-item'):
    name_tag = item.find('div', class_='ads-list-photo-item-title')
    name = name_tag.get_text(strip=True) if name_tag else bad_value
    
    price_tag = item.find('div', class_='ads-list-photo-item-price')
    if price_tag:
        price = price_tag.get_text(strip=True).split('\xa0')[0]
        km_tag = price_tag.find('div', class_='is-offer-type')
        km = km_tag.get_text(strip=True) if km_tag else bad_value

    else:
        price = bad_value
        km = bad_value

    href_tag = item.find('a', class_='js-item-ad')
    href = href_tag['href'] if href_tag and 'href' in href_tag.attrs else bad_value

    full_url = base_url + href if href != bad_value else bad_value

    cars.append({
        'name': name,
        'price': price,
        'km': km,
        'url': full_url
    })

for car in cars:
    print(car)

test_data = cars[0:1]

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

        car["updateDate"] = update_date
        car["type"] = car_type
        car["views"] = views

# Page detail
print('&&&&&&&&&&&&&&&&&&&& PAGE DETAIL &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
pprint(test_data)

import re

def format_and_validate_data(cars_data):
    formatted_data = []

    for car in cars_data:
        formatted_car = {}

        formatted_car['name'] = car.get('name', 'N/A').strip()

        price = car.get('price', 'N/A').strip()
        formatted_car['price'] = format_price(price)

        km = car.get('km', 'N/A').strip()
        formatted_car['km'] = format_km(km)

        url = car.get('url', 'N/A').strip()
        formatted_car['url'] = format_url(url)

        update_date = car.get('updateDate', 'N/A').strip()
        formatted_car['updateDate'] = format_update_date(update_date)

        car_type = car.get('type', 'N/A').strip()
        formatted_car['type'] = car_type.replace('Tipul: ', '')

        views = car.get('views', 'N/A').strip()
        formatted_car['views'] = format_views(views)

        formatted_data.append(formatted_car)

    return formatted_data

def format_price(price):
    if price is None:
        return None
    price_cleaned = re.sub(r'\s+', '', price)
    return price_cleaned if price_cleaned.isdigit() else 'Invalid Price'

def format_km(km):
    if km is None:
        return None
    km_value = re.findall(r'\d+', km)
    return ' '.join(km_value) + ' km' if km_value else 'Invalid KM'

def format_url(url):
    if re.match(r'https?://[^\s]+', url):
        return url
    return 'Invalid URL'

def format_update_date(update_date):
    return update_date.replace('Data actualizării:', '').strip()

def format_views(views):
    return views.replace('Vizualizări:', '').strip() if 'Vizualizări:' in views else 'Invalid Views'

print('&&&&&&&&&&&&&&&&&&&& VALIDATION &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
formatted_cars = format_and_validate_data(test_data)

for car in formatted_cars:
    pprint(car)
