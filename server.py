import json
import select
import socket
import sys
from cambio import Cambio

class CambioServer:
    def __init__(self, server_name, num_players):
        self.cambio = Cambio(num_players)
        self.num_players = num_players
        self.client_sockets = {} # Keys are sockets and values are addresses
        #TODO: Make sure that only one client can connect from each address so that if a client crashes and reconnects we can look it up in this dict and see which player number it was
        self.players = [] # Maps player number (index) to client socket
        self.server_socket = None
        self.name_server_address = "catalog.cse.nd.edu"
        self.name_server_port = 9097
        self.server_name = server_name
        self.port = 0

    def send_to_client(self, client_num, message):
        message_data = json.dumps(message).encode()
        message_length = str(len(message_data)).zfill(10).encode()
        message = message_length + message_data

        self.players[client_num].sendall(message)

        print(f"Sent to Player {client_num}: {message}") #TESTING

    def send_to_all_clients(self, message):
        for i in range(self.num_players):
            self.send_to_client(i, message)
        print(f"Sent to all players: {message}")

    def send_heartbeat(self):
        try:
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            message = {
                        "type": "cambio",
                        "owner": "amitch27",
                        "port": self.port,
                        "project": self.server_name,
                    }
            udp_socket.sendto(json.dumps(message).encode(), (self.name_server_address, self.name_server_port))
            print(f"Heartbeat sent to {self.name_server_address}:{self.name_server_port}")
        except Exception as e:
            print(f"Failed to send heartbeat: {e}")
        finally:
            udp_socket.close()

    def setup(self):
        #LOG AND CHECKPOINT ETC
        pass

    def log(self):
        pass

    def accept_clients(self):
        pass
        #TODO: NEED TO WORK ON THIS
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('', self.port))
        server_socket.listen(5)
        self.port = server_socket.getsockname()[1]
        print(f"Listening on port {self.port}")
        
        self.send_heartbeat()
        
        self.client_sockets[server_socket] = "server"
        self.server_socket = server_socket

        for _ in range(self.num_players):
            (client_socket, address) = server_socket.accept()
            print(f"Client {address} connected")
            #client_socket.settimeout(1)
            self.client_sockets[client_socket] = address
            self.players.append(client_socket)  

    def send_game_state(self):
        #TODO: UPDATE TO BE LIKE A PICTURE OF THE GAME
        self.send_to_all_clients(self.cambio.game_state())

    def wait_for_sticking(self):
        #TODO: WORK ON THIS
        #Timeout after 5 seconds?
        """
        while True:
            #if input
            try:
                self.cambio.stick(input_client, input['player'], input['pos'])
                if input_client != input['player']:
                    try:
                        self.cambio.give()
                    except ValueError as e:
                        pass
                break
            except ValueError as e:
                self.send_to_all_clients(e)
        """
        pass

    def get_client_input(self, client_num):
        data = self.players[client_num].recv(1024).decode()
        # TODO: IN CASE CLIENT CRASHES  
        #if not data:
        #    print(f"Player {client_num} (Client {self.client_sockets[self.players[client_num]]}) disconnected")
        #    self.reconnect_client()
        print(json.loads(data)) #TESTING
        return json.loads(data)

    def play_game(self):
        #TODO: Figure out how to restore from log and checkpoint in case the server previously crashed

        self.cambio = Cambio(self.num_players)

        while True:
            self.cambio.setup()

            self.send_to_all_clients("The game is now starting.")

            for i, player in enumerate(self.cambio.players):
                self.send_to_client(i, f"You are Player {i}. Your first two cards are {self.cambio.look_at_two(i)}")
                self.send_to_client(i, "IMAGE OF GAME WITH CARDS FLIPPED OVER")

            game_over = False
            while not game_over:
                for i, player in enumerate(self.cambio.players):
                    self.cambio.turn = i
                    if self.cambio.last_turn and self.cambio.last_player == i:
                        game_over = True
                        break
                    self.send_game_state()
                    self.send_to_all_clients(f"Player {i}'s turn.")
                    while True:
                        self.send_to_client(i, "What would you like to do?\n\t1. Draw a card.\n\t2. Call Cambio.")
                        turn_type = int(self.get_client_input(i))
                        if turn_type == 1:
                            self.cambio.draw()
                            while True:
                                self.send_to_client(i, f"You drew the {player.hand.name()}. What would you like to do?\n\t1. Replace one of your cards with the new card.\n\t2. Play the new card.")
                                input = self.get_client_input(i)
                                if input == "1":
                                    while True:
                                        self.send_to_client(i, "Which position would you like to switch with?")
                                        pos = int(self.get_client_input(i))
                                        try:
                                            self.cambio.place(pos)
                                            break
                                        except ValueError as e:
                                            self.send_to_client(i, e)
                                    self.send_to_all_clients(f"Player {i} placed the drawn card in position {pos} and played the {self.cambio.played_cards[-1].name()}.")
                                    break
                                elif input == "2":
                                    self.cambio.play()
                                    self.send_to_all_clients(f"Player {i} played the {self.cambio.played_cards[-1].name()}.")
                                    power = self.cambio.has_power()
                                    if power:
                                        while True:
                                            self.send_to_client(i, power)
                                            power_input = self.get_client_input(i).split()
                                            try:
                                                res, K_power = self.cambio.use_power(power_input)
                                                if K_power:
                                                    while True:
                                                        self.send_to_client(i, f"That card is the {res}. Would you like to swap? If yes, enter the position of one of your cards that you would like to swap. If no, enter -1.")
                                                        K_power_input = int(self.get_client_input(i))
                                                        if K_power_input != -1:
                                                            try:
                                                                self.cambio.swap(K_power_input, int(power_input[0]), int(power_input[1]))
                                                                break
                                                            except ValueError as e:
                                                                self.send_to_client(i, e)
                                                elif res and isinstance(res, str):
                                                    self.send_to_client(i, f"That card is the {res}.")
                                                elif res and isinstance(res, list):
                                                    self.send_to_all_clients(f"Player {i} switched the card in position {res[0]} with Player {res[1]}'s card in position {res[2]}.")
                                                else:
                                                    self.send_to_client(i, "The power has been declined.")
                                                break
                                            except ValueError as e:
                                                self.send_to_client(i, e)
                                    break
                                else:
                                    print("Please pick 1 or 2.")
                            break
                        elif turn_type == 2:
                            if not self.cambio.last_turn:
                                self.cambio.call_cambio()
                                self.send_to_all_clients(f"Player {i} has called Cambio. This will be the last round of the game.")
                                break
                            else:
                                self.send_to_client(i, "Cambio has already been called.")
                        else:
                            pass

                    self.send_game_state()
                    self.send_to_all_clients("All players may now attempt to stick a card.")
                    self.wait_for_sticking()

            self.send_to_all_clients(f"The game is over.\n\n{self.cambio.get_winner()}\nEnter 1 to play again or 0 to quit.")
            #TODO: WAIT FOR INPUT AND IF ANY CLIENTS PRESS 1 CONTINUE
            #IF ANY CLIENT PRESSES 0, RETURN BACK TO LOOP()       
                    
    def game_loop(self):
        while True:
            self.accept_clients()
            self.play_game()
    

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Please include server name.")
        sys.exit(1)
        
    server_name = sys.argv[1]

    server = CambioServer(server_name, 2)
    server.game_loop()


#First Attempt at client socket connections and stuff
"""
while True:
    readable_sockets, _, _ = select.select(self.client_sockets.keys(), [], [], 1)

    for sock in readable_sockets:
        if sock == self.server_socket:
            #Reconnect a client
            try:
                (client_socket, address) = sock.accept()
                # Check to see if this is a player who had already connected
                if address[0] in self.client_sockets.values():
                    # Delete the old entry for the client that crashed
                    for client in self.client_sockets:
                        if self.client_sockets[client][0] == address[0]:
                            del self.client_sockets[client]
                            break
                    print(f"Client {address} connected")
                    client_socket.settimeout(1)
                    self.client_sockets[client_socket] = address
                    #TODO: REPLACE THE OLD SOCKET IN SELF.PLAYERS
            except Exception as e:
                print(f"Error accepting connection: {e}")
        else:
            try:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    #TODO: REDO this
                    print(f"Client {address} disconnected")
                    client_socket.close()
                    del self.client_sockets[client_socket]
                    return
                
                request = json.loads(data)
                action = request.get('action')

                if sock == self.players[self.Cambio.turn]:
                # Player whose turn it is
                    pass
                else:
                    # CHECK HERE TO SEE IF ITS A STICK OTHERWISE DO NOTHING
                    if action == "stick":
                        pass
            
            except Exception as e:
                print(f"Error: {e}")
"""