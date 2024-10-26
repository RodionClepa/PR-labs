import socket
import signal
import sys
from time import sleep
# Define the server's IP address and port
HOST = '127.0.0.1' # IP address to bind to (localhost)
PORT = 8080 # Port to listen on
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(5) # Backlog for multiple simultaneous connections
print(f"Server is listening on {HOST}:{PORT}")
def signal_handler(sig, frame):
    print("\nShutting down the server...")
    server_socket.close()
    sys.exit(0)
    # Register the signal handler
    signal.signal(signal.SIGINT, signal_handler)
# Function to handle client requests
def handle_request(client_socket):
    # Receive and print the client's request data
    # request_data = client_socket.recv(1024).decode('utf-8')
    request_data = b"" # Empty byte string
    while True:
        data = client_socket.recv(4096)  # Receive in chunks of 4096 bytes
        if not data:
            break
        request_data += data
        if b'--\r\n' in data:
            break
        print(f"Data: {data}")
        print(len(data))
    print("FiniHSDJAFNajjk")
    request_data = request_data.decode('utf-8')
    print(f"Received Request:\n{request_data}")
    # Parse the request to get the HTTP method and path
    request_lines = request_data.split('\n')
    request_line = request_lines[0].strip().split()
    method = request_line[0]
    path = request_line[1]
    # Initialize the response content and status code
    response_content = ''
    status_code = 200
    # Define a simple routing mechanism
    if path == '/json':
        response_content = 'Hello, World!'
    elif path == '/about':
        response_content = 'This is the About page.'
    else:
        response_content = '404 Not Found'
        status_code = 404
    response = f'HTTP/1.1 {status_code} OK\nContent-Type: text/html\n\n{response_content}'
    client_socket.send(response.encode('utf-8'))
    # Close the client socket
    client_socket.close()
while True:
    # Accept incoming client connections
    client_socket, client_address = server_socket.accept()
    print(f"Accepted connection from {client_address[0]}:{client_address[1]}")
    try:
        # Handle the client's request in a separate thread
        handle_request(client_socket)
    except KeyboardInterrupt:
        pass