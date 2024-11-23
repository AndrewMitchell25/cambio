import socket
import json
import http.client
import time
import sys
import select

class CambioClient:
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
                    if r["type"] == "cambio" and r["project"] == server_name:
                        host = r["name"]
                        port = r["port"]
                        try:
                            self.socket.connect((host, port))
                            print("Connected to server")
                            return
                        except Exception as e:
                            continue
            except Exception as e:
                print(f"Connection error: {e}")
                
            print("Server not found. Retrying...")
            
            time.sleep(5)

    def receive_message(self):
        try:    
            message_length = int(self.socket.recv(10).decode())

            if message_length <= 1024:
                message_data = self.socket.recv(message_length).decode()
            else:
                message_data = ""
                while len(message_data) < message_length:
                    chunk = self.socket.recv(1024).decode()
                    if not chunk:
                        break
                    message_data += chunk
            message = json.loads(message_data)
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
        while True:
            ready_inputs, _, _ = select.select([self.socket, sys.stdin], [], [], 1)
            for source in ready_inputs:
                if source is self.socket:
                    print(self.receive_message())
                elif source is sys.stdin:
                    self.send_input()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Please include server name.")
        sys.exit(1)

    server_name = sys.argv[1]

    client = CambioClient()
    client.connect(server_name)
    client.game_loop()