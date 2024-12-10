import socket
import json
import http.client
import random
import time
import sys
import select

class MockClient:
    def __init__(self):
        self.socket = None
        self.name_server_address = "catalog.cse.nd.edu"
        self.name_server_port = 9097
        self.server_name = None

    def connect(self, server_name):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_name = server_name
        name_server = http.client.HTTPConnection(self.name_server_address, self.name_server_port)
        while True:
            try:
                name_server.request("GET", "/query.json")
                response = json.loads(name_server.getresponse().read())
                for r in response:
                    if r.get("type", "") == "cambio" and r.get("project", "") == server_name:
                        host = r["name"]
                        port = r["port"]
                        try:
                            self.socket.connect((host, port))
                            print(f"Connected to server {host}, {port}")
                            return
                        except Exception as e:
                            continue
            except Exception as e:
                print(f"Connection error: {e}")
                
            print("Server not found. Retrying...")
            
            time.sleep(5)

    def receive_message(self):
        try:    
            # Read the length of the message
            message_length = int(self.socket.recv(10).decode())

            # Receive the full message
            message_data = b""
            while len(message_data) < message_length:
                chunk = self.socket.recv(min(1024, message_length - len(message_data)))
                if not chunk:
                    break
                message_data += chunk

            # Decode and parse as JSON
            decoded_message = message_data.decode()
            try:
                message = json.loads(decoded_message)
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                return None

            if isinstance(message, str) and message.startswith("Error"):
                print(message)
                exit(1)

            return message
            
        except Exception as e:
            print(f"Receive error: {e}")
        
        self.socket.close()
        self.connect(self.server_name)


    def send_input(self):
        input_data = sys.stdin.readline().strip()
        if len(input_data) > 20:
            print("Error: Input is too long, please try again.")
            return
        #print(input_data) #TESTING
        self.socket.sendall(json.dumps(input_data).encode())

    def game_loop(self):
        total_requests = 0
        total_time = 0
        while True:
            # ready_inputs, _, _ = select.select([self.socket, sys.stdin], [], [], 1) # checks to see if it needs to read from socket or in sys.stdin
            # for source in ready_inputs:
            #     if source is self.socket:
            message = self.receive_message()
            total_requests += 1
            # Automatically respond to specific prompts
            if "What would you like to do?" in message:
                # Automatically respond with "1"
                response = str(random.choice([1,1,1,2]))
                print(f"Automatically responding: {response}")
                self.socket.sendall(json.dumps(response).encode())

            elif 'The game is now starting.'  in message:
                start = time.time()
            
            elif 'Which position would you like to switch with' in message:
                response = str(random.choice([0,1,2,3]))
                print(f"Automatically responding: {response}")
                self.socket.sendall(json.dumps(response).encode())

            
            elif "Enter 1 to play again or 0 to quit" in message:
                # Automatically respond with "1" (to continue) or "0" (to quit)
                response = "0"  # Change to "0" to simulate quitting
                end = time.time()
                time_elapsed = end - start
                print(f"Automatically responding: {response}")
                self.socket.sendall(json.dumps(response).encode())

            
            elif "Enter -1 to decline the power" in message:
                response = "-1"
                print(f"Automatically responding: {response}")
                self.socket.sendall(json.dumps(response).encode())

            
            elif "EXIT" in message:
                end = time.time()
                total_time = end - start
                return total_time, total_requests
            
            else:
                print(message)

                # elif source is sys.stdin:
                #     # Manual input for other cases
                #     self.send_input()



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Please include server name.")
        sys.exit(1)

    server_name = sys.argv[1]

    client = MockClient()
    client.connect(server_name)
    time_elapsed, total_requests = client.game_loop()
    print(time_elapsed, total_requests)
    with open(f'output.txt', 'a') as output_file:
        output_file.write(f'{time_elapsed} {total_requests}\n')

