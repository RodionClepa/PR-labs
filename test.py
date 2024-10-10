def serialize_categories_custom(categories_data):
    output = ""
    
    for category in categories_data:
        category_str = f"{{startRange|{category['startRange']}|endRange|{category['endRange']}|totalPrice|{category['totalPrice'] if category['totalPrice'] is not None else 0}|timestamp|{category['timestamp']}|cars:"
        
        cars_str = ""
        for car in category["cars"]:
            car_str = f"<name|{car['name']}|price|{car['price']}|currency|{car['currency']}|km|{car['km']}|url|{car['url']}|updateDate|{car['updateDate']}|type|{car['type']}|views|{car['views']}>"
            cars_str += car_str
        
        category_str += cars_str + "}\n"
        output += category_str
    
    return output

def deserialize_categories_custom(serialized_data):
    categories = []
    
    # Split the data by '}' to separate categories
    category_blocks = serialized_data.split('}\n')
    
    for category_block in category_blocks:
        if not category_block.strip():
            continue
        
        # Remove starting '{' and 'cars:' part
        category_part, cars_part = category_block[1:].split('|cars:')
        
        # Split the category part to extract the fields
        category_fields = category_part.split('|')
        category_dict = {
            'startRange': int(category_fields[1]),
            'endRange': int(category_fields[3]),
            'totalPrice': int(category_fields[5]),
            'timestamp': category_fields[7],
            'cars': []
        }
        
        # Split the cars part by '>' to separate each car
        car_blocks = cars_part.split('>')
        
        for car_block in car_blocks:
            if not car_block.strip():
                continue
            
            # Remove starting '<' and split by '|'
            car_fields = car_block[1:].split('|')
            car_dict = {}
            for i in range(0, len(car_fields), 2):
                car_dict[car_fields[i]] = car_fields[i + 1]
            
            category_dict['cars'].append(car_dict)
        
        categories.append(category_dict)
    
    return categories


from datetime import datetime, timezone

# Example categories data
categories = [
    {
        "startRange": 1000,
        "endRange": 60000,
        "totalPrice": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cars": [
            {
                "name": "Car A",
                "price": 15000,
                "currency": "MDL",
                "km": "100000 km",
                "url": "http://example.com/carA",
                "updateDate": "Monday, January 01, 2023 at 12:00 PM",
                "type": "Sedan",
                "views": "200"
            },
            {
                "name": "Car B",
                "price": 20000,
                "currency": "MDL",
                "km": "50000 km",
                "url": "http://example.com/carB",
                "updateDate": "Monday, January 02, 2023 at 12:00 PM",
                "type": "Hatchback",
                "views": "150"
            }
        ]
    }
]

# Serialize categories to custom format
serialized_data = serialize_categories_custom(categories)

# Save the serialized data to a file
with open('categories_custom.txt', 'w', encoding='utf-8') as file:
    file.write(serialized_data)

print("Custom serialized data saved to categories_custom.txt")

# Read from file and deserialize
with open('categories_custom.txt', 'r', encoding='utf-8') as file:
    file_content = file.read()

deserialized_data = deserialize_categories_custom(file_content)

# Display deserialized data
print("Deserialized Categories Data:")
print(deserialized_data)