import requests
from bs4 import BeautifulSoup
from pprint import pprint  # For pretty print
import re
from datetime import datetime, timezone
from functools import reduce

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

test_data = cars[0:5]

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
        formatted_car = {
            'name': car.get('name', bad_value).strip(),
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
    map_curr = {
        "€": "EUR"
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
        "endRange": 500000,
        "cars": []
    },
    {
        "startRange": 500000,
        "endRange": 1000000,
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