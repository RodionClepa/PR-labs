import socket
import threading
import time
import json
import random

from enum import Enum

def get_timestamp():
    return time.strftime("%H:%M:%S", time.localtime()) + f".{int(time.time() * 1000) % 1000:03}"

def get_random_message():
    try:
        # Open the JSON file
        with open("randomMessages.json", 'r') as file:
            # Load the data from the file (list of messages)
            messages = json.load(file)
        
        # Return a random message from the list
        return random.choice(messages)
    
    except FileNotFoundError:
        return "Error: The file does not exist."
    except json.JSONDecodeError:
        return "Error: The file is not a valid JSON format."
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Define the NodeRole Enum
class NodeRole(Enum):
    CANDIDATE = "Candidate"
    LEADER = "Leader"
    FOLLOWER = "Follower"

class Node:
    def __init__(self, ip, port, name, range_response, range_await):
        self.ip = ip
        self.port = port
        self.name = name
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.ip, self.port))
        self.role = NodeRole.FOLLOWER
        self.votes_received = 0
        self.term = 0
        self.patience = random.randint(range_await[0], range_await[1])
        self.response = random.randint(range_response[0], range_response[1])
        self.last_heartbeat_time = time.time()
        print(f"{get_timestamp()} - Node {self.name} is on {self.ip}:{self.port}, pat {self.patience}, res {self.response}")

    def listen_for_messages(self):
        while True:
            try:
                message, address = self.server_socket.recvfrom(4096)  # Buffer size of 4096 bytes
                d_message = message.decode().split("|")
                action = d_message[0]
                sender_name = d_message[1]
                rest = " ".join(d_message[2:])
                sender_port = address[1]
                print(f"{get_timestamp()} - Node {self.name} got action:{action}: '{rest}' from {sender_name}|{sender_port}")
                self.last_heartbeat_time = time.time()
                if action == "heartbeat":
                    # Update last_heartbeat_time when a heartbeat is received
                    self.last_heartbeat_time = time.time()
                    print(f"{get_timestamp()} - Node {self.name} received heartbeat.")

                    # Stop the election and become a follower if heartbeat from leader
                    if self.role == NodeRole.CANDIDATE:
                        print(f"{get_timestamp()} - Node {self.name} received heartbeat. Stopping election and following {sender_name}.")
                        self.role = NodeRole.FOLLOWER
                        self.votes_received = 0  # Reset vote count
                        self.term += 1  # Increment term as leader heartbeat has arrived

                    elif self.role == NodeRole.LEADER:
                        print(f"{get_timestamp()} - Node {self.name} received heartbeat. Stop being leader by {sender_name}.&&&&&&&&&&&&&&&&&&&")
                        self.role = NodeRole.FOLLOWER
                        self.votes_received = 0  # Reset vote count
                        self.term += 1  # Increment term as leader heartbeat has arrived

                    # Respond back to server
                    response_message = f"heartbeat_ack|{self.name}|Heartbeat acknowledged"
                    self.server_socket.sendto(response_message.encode(), address)
                    print(f"{get_timestamp()} - Node {self.name} sent heartbeat acknowledgment to {sender_name}")

                elif action == "heartbeat_ack":
                    print(f"{get_timestamp()} - Node {self.name} recieved heartbeat acknowledgment from {sender_name}")
                
                elif action == "RequestVote":
                    # Handle vote request during election
                    print(f"{get_timestamp()} - Node {self.name} received RequestVote from {sender_name}.")
                    if self.role == NodeRole.FOLLOWER:
                        if self.term <= int(rest):
                            print(f"{get_timestamp()} - Node {self.name} voted for {sender_name}")
                            self.send_vote(sender_name, address)
                        else:
                            print(f"{get_timestamp()} - Node {self.name} ignored vote request as election is ongoing.")
                    elif self.role == NodeRole.CANDIDATE:
                        print(f"{get_timestamp()} - Node {self.name} ignored vote request as election is ongoing.")

                elif action == "VoteGranted":
                    print(f"{get_timestamp()} - Node {self.name} received VoteGranted from {sender_name}.")
                    self.votes_received += 1
                    if self.votes_received > len(list_nodes) // 2:  # Majority votes
                        print(f"{get_timestamp()} - Node {self.name} has won the election and is now the LEADER.********************")
                        self.role = NodeRole.LEADER
                        self.votes_received = 0  # Reset vote count for new leader state

                else:
                    print(f"{get_timestamp()} - Node {self.name} received unknown message.")

            except socket.timeout:
                # Handle the timeout gracefully
                print(f"{get_timestamp()} - Node {self.name} did not receive any messages within the timeout period.")

    def send_vote(self, sender_name, address):
        # Respond to vote request by granting vote
        vote_message = f"VoteGranted|{self.name}|{sender_name}"
        self.server_socket.sendto(vote_message.encode(), address)
        print(f"{get_timestamp()} - Node {self.name} granted vote to {sender_name}")

    def start_election(self):
        # Start an election process when follower detects no heartbeats
        self.term += 1  # Increment term for each election cycle
        self.votes_received = 1  # Candidate votes for itself
        self.role = NodeRole.CANDIDATE
        print(f"{get_timestamp()} - Node {self.name} started election (Term {self.term}).")

        # Send RequestVote to all other nodes
        for port in list_nodes:
            if port != self.port:
                target = ('127.0.0.1', port)
                vote_message = f"RequestVote|{self.name}|{self.term}"
                self.server_socket.sendto(vote_message.encode(), target)
                print(f"{get_timestamp()} - Node {self.name} sent RequestVote to {target}")
        
        # Set timeout and wait for votes
        time.sleep(random.uniform(1, 2))  # Randomize timeout slightly to prevent collisions
    


    def select_target(self):
        available_ports = [port for port in list_nodes if port != self.port]
        return available_ports

    def sent_heartbeat(self):
        while True:
            if self.role != NodeRole.LEADER:
                continue
            # Send a heartbeat message to all other nodes
            message = f"heartbeat|{self.name}|{get_random_message()}"
            
            # Get the list of all other nodes
            targets = self.select_target()
            
            # Send the heartbeat to all nodes
            for target_port in targets:
                target = ('127.0.0.1', target_port)
                self.server_socket.sendto(message.encode(), target)
                print(f"{get_timestamp()} - Node {self.name} sent heartbeat to {target}")
            
            # Wait for a bit before sending the next heartbeat
            time.sleep(self.response)
    

    def start(self):
        # Create a thread to send heartbeats
        heartbeat_thread = threading.Thread(target=self.sent_heartbeat, daemon=True)
        heartbeat_thread.start()

        # Create a thread to listen for messages
        listen_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
        listen_thread.start()
        # Check if the follower has stopped receiving heartbeats
        self.last_heartbeat_time = time.time()
        threading.Thread(target=self.check_heartbeat_timeout).start()

        

    def set_role(self, new_role: NodeRole):
        # Method to change the role of the node
        if new_role in NodeRole:
            self.role = new_role
            print(f"{get_timestamp()} - Node {self.name} role changed to {self.role.value}")
        else:
            print(f"{get_timestamp()} - Node {self.name} Invalid role: {new_role}")

    def check_heartbeat_timeout(self):
        # Method to check if the follower has stopped receiving heartbeats
        while True:
            if self.role == NodeRole.FOLLOWER and (time.time() - self.last_heartbeat_time) > self.patience:
                print(f"{get_timestamp()} - Node {self.name} ({time.time() - self.last_heartbeat_time}) stopped receiving heartbeats. Leader may have failed!!!!!!!!!!!!!!!!!!!1")
                self.start_election()
            time.sleep(1)


global list_nodes

nicknames = [
    "Ace", "Buzz", "Champ", "Sparky", "Tiger", "Sparky", "Munchkin", "Cookie", 
    "Bear", "Doodle", "Rocket", "Bubbles", "Gizmo", "Jester", "Shadow", "Peanut", 
    "Zippy", "Sunshine", "Snickers", "Cuddlebug", "Pookie", "Snuffy", "Twinkle", 
    "Squirt", "Cookie Monster", "Bigfoot", "Taz", "Sweets", "Buddy", "Jellybean"
]

def get_random_nick():
    return random.choice(nicknames)

range_response = [10, 16]
range_await = [8, 13]
number_nodes = 4
list_nodes = []
port_number = 5000
leader_number = random.randint(0, number_nodes - 1)
node_list = []
for i in range(0, number_nodes):
    list_nodes.append(port_number + i)
    node = Node('127.0.0.1', port_number + i, get_random_nick(), range_response, range_await)
    if i == leader_number:
        node.set_role(NodeRole.LEADER)
    node_list.append(node)

for node in node_list:
    node.start()