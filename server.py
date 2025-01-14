import json
import os
import select
import socket
import sys
from cambio import Cambio, Card

class CambioServer:
    def __init__(self, server_name, num_players):
        self.cambio = Cambio(num_players)
        self.num_players = num_players
        self.client_sockets = {} # Keys are sockets and values are addresses
        self.players = [] # Maps player number (index) to client socket
        self.server_socket = None
        self.name_server_address = "catalog.cse.nd.edu"
        self.name_server_port = 9097
        self.server_name = server_name
        self.port = 0
        self.game_over = False
        self.ckpt_file_name = server_name + ".ckpt"
        self.log_file_name = server_name + ".log"
        self.new_game = True

    def send_to_client(self, client_num, message):
        message_data = json.dumps(message).encode()
        message_length = str(len(message_data)).zfill(10).encode()
        message = message_length + message_data

        try:
            self.players[client_num].sendall(message)
        except Exception as e:
            print(f"Client send error: {e}")
            self.reconnect_client(client_num)

    def send_to_all_clients(self, message, skip=None):
        for i in range(self.num_players):
            if skip == i:
                continue

            self.send_to_client(i, message)

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

    def accept_clients(self, only_setup=False):
        if self.server_socket == None:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind(('', self.port))
            server_socket.listen(5)
            self.port = server_socket.getsockname()[1]
            self.client_sockets[server_socket] = "server"
            self.server_socket = server_socket
        print(f"Listening on port {self.port}")
        
        self.send_heartbeat()
        
        if not only_setup:
            for _ in range(self.num_players):
                (client_socket, address) = self.server_socket.accept()
                print(f"Client {address} connected")
                self.client_sockets[client_socket] = address
                self.players.append(client_socket)  

    def send_game_state(self, first_turn=False, show_all=False):
        state = self.cambio.game_state(first_turn=first_turn,show_all=show_all)
        for i in range(self.num_players):
            self.send_to_client(i, state[i])

    def wait_for_sticking(self):
        self.send_to_all_clients("All players may now attempt to stick a card. Enter the player number and the position of the card you'd like to stick.")
        count = 0
        while count < 10:
            readable_sockets, _, _ = select.select(self.client_sockets.keys(), [], [], 1)
            for sock in readable_sockets:
                if sock != self.server_socket:
                    try:
                        data = sock.recv(1024).decode()
                        client_num = self.players.index(sock)

                        if not data:
                            print(f"Client {self.client_sockets[sock]} disconnected")
                            self.reconnect_client(client_num)
                            continue
                        
                        message = list(map(int, json.loads(data).split()))

                        if len(message) != 2:
                            self.send_to_client(client_num, f"That is not a valid input. Please try again.")
                            continue

                        try:
                            self.cambio.stick(client_num, message[0], message[1])
                            self.send_to_all_clients(f"Player {client_num} has stuck Player {message[0]}'s card in position {message[1]}, which was the {self.cambio.deck.played_cards[-1].name()}.")
                            self.send_game_state()
                        except ValueError as e:
                            self.send_to_all_clients(str(e))
                            continue
                        
                        while True:
                            if client_num != message[0]:
                                try:
                                    self.send_to_all_clients(f"Player {client_num} can now give Player {message[0]} a card.")
                                    self.send_to_client(client_num, f"Enter the position of the card you'd like to give Player {message[0]}.")
                                    pos = int(self.get_client_input(client_num))
                                    self.cambio.give(client_num, pos, message[0], message[1])
                                    self.send_to_all_clients(f"Player {client_num} has given Player {message[0]} the card in position {pos}.")
                                    return
                                except ValueError as e:
                                    self.send_to_client(client_num, str(e))
                            else:
                                return
                    except Exception as e:
                        print(f"Error: {e}")
            count += 1

    def reconnect_client(self, client_num, send_message=True):
        if send_message:
            self.send_to_all_clients(f"Player {client_num} has disconnected. Waiting for reconnection...", skip=client_num)
        self.send_heartbeat()

        while True:
            (client_socket, address) = self.server_socket.accept()
            if address[0] == self.client_sockets[self.players[client_num]][0]:
                del self.client_sockets[self.players[client_num]]
                self.client_sockets[client_socket] = address
                self.players[client_num] = client_socket
                print(f"Client {address} connected")
                if send_message:
                    self.send_to_all_clients(f"Player {client_num} has reconnected.")
                return
            else:
                print(f"Incorrect client has tried to connect: {address}")
                message_data = json.dumps("Error: The server you are trying to connect to is full. Please try another server.").encode()
                message_length = str(len(message_data)).zfill(10).encode()
                message = message_length + message_data

                client_socket.sendall(message)

                client_socket.close()

    def get_client_input(self, client_num):
        while True:
            data = self.players[client_num].recv(1024).decode()
            if not data:
                print(f"Player {client_num} (Client {self.client_sockets[self.players[client_num]]}) disconnected")
                self.reconnect_client(client_num)
            else:
                break
        return json.loads(data)

    def log(self):
        log = {
            'turn': self.cambio.turn,
            'players': [[[card.rank, card.suit] if card else "None" for card in p.cards] for p in self.cambio.players],
            'played_cards': [[card.rank, card.suit] for card in self.cambio.deck.played_cards],
            'deck_len': len(self.cambio.deck.deck),
            'last_turn': self.cambio.last_turn,
            'last_player': self.cambio.last_player
        }

        self.log_file.write(json.dumps(log) + "\n")

    def setup(self):
        self.game_over = False

        self.cambio.setup()

        self.log_file = open(self.log_file_name, "a+")

        with open(self.ckpt_file_name, "a+") as checkpoint_file:
            checkpoint_file.seek(0)
            data = checkpoint_file.read()

            # If the game crashed and restarting
            if data: 
                game_state = json.loads(data)

                self.accept_clients(True)

                self.cambio.deck.deck = [Card(card[0], card[1]) for card in game_state['deck']]
                for i, player in enumerate(game_state['players']):
                    self.cambio.players[i].score = player['score']
                    self.cambio.players[i].cards = [Card(card[0], card[1]) if card else None for card in player['cards']]
                    self.players.append(str(i))
                    self.client_sockets[str(i)] = player['address']

                    self.reconnect_client(i, False)

                self.log_file.seek(0)
                log_data = False
                for log in self.log_file:
                    log_data = True
                    log = json.loads(log.rstrip())
                    self.cambio.turn = log['turn']
                    self.cambio.last_turn = log['last_turn']
                    self.cambio.last_player = log['last_player']
                    self.cambio.deck.played_cards = [Card(card[0], card[1]) for card in log['played_cards']]
                    while len(self.cambio.deck.deck) > log['deck_len']:
                        self.cambio.deck.draw()
                    for i, cards in enumerate(log['players']):
                        self.cambio.players[i].cards = [Card(card[0], card[1]) if card != "None" else None for card in cards]
                if log_data:
                    self.cambio.turn = (self.cambio.turn + 1) % self.cambio.num_players
                print(list(map(str, self.cambio.deck.deck)))

            #Starting a new game
            else:
                if self.new_game:
                    self.client_sockets = {}
                    self.players = []
                    self.accept_clients()
                game_state = {}
                game_state['deck'] = [[card.rank, card.suit] for card in self.cambio.deck.deck]
                game_state['players'] = [{
                        'address': self.client_sockets[self.players[i]],
                        'score': p.score,
                        'cards': [[card.rank, card.suit] for card in p.cards]
                    } for i, p in enumerate(self.cambio.players)]
                checkpoint_file.write(json.dumps(game_state))

                self.pregame()
        
    def pregame(self):
        self.send_to_all_clients("The game is now starting.")

        for i, player in enumerate(self.cambio.players):
            self.send_to_client(i, f"You are Player {i}. Your first two cards are {self.cambio.look_at_two(i)}")
        self.send_game_state(first_turn=True)

    def play_game(self):
        i = self.cambio.turn
        while not self.game_over:
            player = self.cambio.players[i]
            self.cambio.turn = i
            if self.cambio.last_turn and self.cambio.last_player == i:
                self.game_over = True
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
                                    self.send_to_client(i, str(e))
                            self.send_to_all_clients(f"Player {i} placed the drawn card in position {pos} and played the {self.cambio.deck.played_cards[-1].name()}.")
                            break
                        elif input == "2":
                            self.cambio.play()
                            self.send_to_all_clients(f"Player {i} played the {self.cambio.deck.played_cards[-1].name()}.")
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
                                                        self.send_to_all_clients(f"Player {i} switched the card in position {K_power_input} with Player {power_input[0]}'s card in position {power_input[1]}.")
                                                        break
                                                    except ValueError as e:
                                                        self.send_to_client(i, str(e))
                                        elif res and isinstance(res, str):
                                            self.send_to_client(i, f"That card is the {res}.")
                                        elif res and isinstance(res, list):
                                            self.send_to_all_clients(f"Player {i} switched the card in position {res[0]} with Player {res[1]}'s card in position {res[2]}.")
                                        else:
                                            self.send_to_all_clients(f"Player {i} has declined the power.")
                                        break
                                    except ValueError as e:
                                        self.send_to_client(i, str(e))
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

            self.wait_for_sticking()
            self.log()
            i = (i + 1) % self.num_players

        self.send_game_state(False, True)
        self.send_to_all_clients(f"The game is over.\n\n{self.cambio.get_winner()}\nEnter 1 to play again or 0 to quit.")
        os.remove(self.ckpt_file_name)
        self.log_file.close()
        self.log_file = None
        os.remove(self.log_file_name)

        if int(self.get_client_input(0)) == 0:
            self.send_to_all_clients("EXIT")
            self.new_game = True
            return

        self.new_game = False
        return 
                    
    def game_loop(self):
        while True:
            self.setup()
            self.play_game()
    

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage is 'python server.py <server_name> <player_num>'")
        sys.exit(1)
        
    server_name = sys.argv[1]
    player_num = int(sys.argv[2])

    server = CambioServer(server_name, player_num)
    server.game_loop()
