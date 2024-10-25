from datetime import datetime
from db_operations import insert_car
from db_operations import create_cars_table
from db_operations import insert_multiple_cars
import json
import socket
from urllib.parse import urlparse, parse_qs

create_cars_table()

def load_cars_from_json(filename):
    """Loads car data from a JSON file and formats it for insertion."""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
        car_list = []
        for car in data['cars']:
            # Convert updateDate to a datetime object
            update_date = datetime.strptime(car['updateDate'], "%A, %B %d, %Y at %I:%M %p")
            car_list.append((
                car['name'],
                car['price'],
                car['currency'],
                car['km'] if car['km'] != "None" else None,
                car['url'],
                update_date,
                car['type'],
                int(car['views'])
            ))
        return car_list
    

def run_server(host='localhost', port=8080):
    # Create a socket that uses IPv4 and TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server is listening on {host}:{port}")
    while True:
        # Accept incoming client connections
        client_socket, client_address = server_socket.accept()
        print(f"Accepted connection from {client_address[0]}:{client_address[1]}")

        # Receive and print the client's request data
        request_data = client_socket.recv(1024).decode('utf-8')
        print(f"Received Request:\n{request_data}")

        # Construct an HTTP response
        response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nHello, World!"
        
        # Send the HTTP response back to the client
        client_socket.sendall(response.encode('utf-8'))

        # Close the client socket
        client_socket.close()


run_server()

# cars_list = load_cars_from_json('cars.json')

# insert_multiple_cars(cars_list)

# Example data
# name = "Mercedes GLE Coupe, 2016 an"
# price = 944000
# currency = "MDL"
# km = "135 km"
# url = "https://999.md/ro/88473766"
# update_date = datetime(2024, 10, 10, 15, 37)
# type = "Vând"
# views = 26

# # Insert car data
# insert_car(name, price, currency, km, url, update_date, type, views)
