import requests
from bs4 import BeautifulSoup

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
    name = name_tag.get_text(strip=True) if name_tag else 'N/A'
    
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

