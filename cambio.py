import random

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.value = self.get_value()

    def get_value(self):
        card_nums = {'A': 1, 'J': 11, 'Q': 12, 'K': 13}
        if self.rank not in card_nums:
            return int(self.rank)
        elif self.rank == 'K' and self.suit in 'HD':
            return -1
        else:
            return card_nums[self.rank]

    def name(self):
        suit_names = {'C': "Clubs", 'H': "Hearts", 'S': "Spades", 'D': "Diamonds"}
        rank_names = {'A': "Ace", 'J': "Jack", 'Q': "Queen", 'K': "King"}
        rank = rank_names[self.rank] if self.rank in rank_names else self.rank
        suit = suit_names[self.suit]
        return rank + " of " + suit

    def __str__(self):
        return self.rank + self.suit
    
    def display(self, show=False, num=None):
        image = [
            "________",
            f"|{str(self) if show else f"{str(num)} " if num != None else "  "}{"" if self.rank == '10' and show else " "}   |",
            "|      |",
            "|      |",
            f"|{"" if self.rank == '10' and show else "_"}___{str(self) if show else "__"}|"
        ]

        return image

class Deck():
    def __init__(self):
        self.suits = ['C', 'H', 'S', 'D']
        self.ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        self.deck = [Card(rank, suit) for suit in self.suits for rank in self.ranks]
        self.drawn = []
        self.played_cards = []

        random.shuffle(self.deck)

    def draw(self):
        if len(self.deck) > 0:
            card = self.deck.pop() 
        else:
            self.deck = self.played_cards
            self.played_cards = []
            random.shuffle(self.deck)
            
        self.drawn.append(card)
        return card
    
    def display(self):
        image = [
            "________",
            "|      |",
            "| DECK |",
            "|      |",
            "|______|"
        ]
        return image

class Player():
    def __init__(self):
        self.cards = []
        self.hand = None
        self.score = 0

    def __str__(self):
        return " ".join(map(str, self.cards))


class Cambio():
    def __init__(self, num_players):
        self.deck = None
        self.num_players = num_players
        self.players = [Player() for _ in range(num_players)]
        self.turn = 0
        self.num_cards = 4
        self.last_player = -1
        self.last_turn = False
        #TODO: Maybe add this to log or checkpoint somewhere
        self.extra_cards = -1

    def setup(self):
        self.deck = Deck()
        self.turn = 0
        self.last_player = -1
        self.last_turn = False

        for i, player in enumerate(self.players):
            player.hand = None
            player.cards = []
            for _ in range(self.num_cards):
                player.cards.append(self.deck.draw())
            if i == self.extra_cards:
                player.cards.append(self.deck.draw())

        self.extra_cards = -1


    def game_state(self, first_turn=False, show_all=False):
        #TODO: UNFINISHED

        game_state = []
        middle = [
            self.deck.played_cards[-1].display(show=True) if self.deck.played_cards else self.deck.deck[0].display(show=False),
            self.deck.display()
        ]

        player_cards = [[card.display(show=show_all, num=i) if card else ["        "] * 5 for i, card in enumerate(player.cards)] for player in self.players]
        
        for p in range(self.num_players):
            state = "---------------------------\n"
            
            other_players = [i for i in range(self.num_players) if i != p]

            for i in other_players:
                state += f"Player {i}"
                state += "        " * int(len(player_cards[i]) // 2)
            state += "\n"

            for i in range(len(player_cards[0][0])):
                for j in other_players:
                    for k in range(2):
                        state += player_cards[j][k][i] + " "
                    state += "\t"
                state += "\n"

            for i in range(len(player_cards[0][0])):
                for j in other_players:
                    for k in range(2, len(player_cards[j])):
                        state += player_cards[j][k][i] + " "
                    state += "\t"
                state += "\n"
            
            state += "\n"

            for i in range(len(middle[0])):
                state += middle[0][i] + " " + middle[1][i] +"\n"

            state += "\n"

            for i in range(len(player_cards[0][0])):
                for j in range(2, len(player_cards[p])):
                    state += player_cards[p][j][i] + " "
                state += "\n"

            card0 = self.players[p].cards[0].display(show=True) if first_turn else player_cards[p][0]
            card1 = self.players[p].cards[1].display(show=True) if first_turn else player_cards[p][1]
            
            for i in range(len(player_cards[0][0])):
                state += card0[i] + " " + card1[i] + "\n"
            
            state += "---------------------------\n"

            game_state.append(state)

        return game_state

    def draw(self):
        self.players[self.turn].hand = self.deck.draw()

    def play(self):
        self.deck.played_cards.append(self.players[self.turn].hand)
        self.players[self.turn].hand = None

    #TODO: MORE ERROR HANDLING FOR ALL FUNCTIONS
    def place(self, pos):
        if self.players[self.turn].cards[pos] == None:
            raise ValueError(f"You do not have a card at position {pos}.")
        temp = self.players[self.turn].cards[pos]
        self.players[self.turn].cards[pos] = self.players[self.turn].hand
        self.players[self.turn].hand = None
        self.deck.played_cards.append(temp)

    def swap(self, pos1, player2, pos2):
        if pos1 > len(self.players[self.turn].cards) or pos1 < 0 or self.players[self.turn].cards[pos1] == None:
            raise ValueError(f"You do not have a card at position {pos1}.")
        if pos2 > len(self.players[player2].cards) or pos2 < 0 or self.players[player2].cards[pos2] == None:
            raise ValueError(f"Player {player2} does not have a card at position {pos2}.")
        temp = self.players[self.turn].cards[pos1]
        self.players[self.turn].cards[pos1] = self.players[player2].cards[pos2]
        self.players[player2].cards[pos2] = temp

    def stick(self, stick_player, stuck_player, pos):
        if pos > len(self.players[stuck_player].cards) or pos < 0 or self.players[stuck_player].cards[pos] == None:
            raise ValueError(f"Player {stick_player} attempted to stick Player {stuck_player}'s card at position {pos} but there is no card there.")
        if self.players[stuck_player].cards[pos].rank != self.deck.played_cards[-1].rank:
            self.players[stick_player].cards.append(self.deck.draw())
            raise ValueError(f"Player {stick_player} attempted to stick Player {stuck_player}'s card at position {pos} but failed and has received a penalty card.")
        self.deck.played_cards.append(self.players[stuck_player].cards[pos])
        self.players[stuck_player].cards[pos] = None

    def give(self, player1, pos1, player2, pos2):
        if pos1 > len(self.players[self.turn].cards) or pos1 < 0 or self.players[player1].cards[pos1] == None:
            raise ValueError(f"You do not have a card at position {pos1}.")
        if pos2 > len(self.players[player2].cards) or pos2 < 0 or self.players[player2].cards[pos2] == None:
            raise ValueError(f"Player {player2} does not have a card at position {pos2}.") 
        self.players[player2].cards[pos2] = self.players[player1].cards[pos1]
        self.players[player1].cards[pos1] = None

    def has_power(self):
        card = self.deck.played_cards[-1]
        if card.rank not in {'7', '8', '9', '10', 'J', 'Q', 'K'}:
            return
        elif card.rank in {'7', '8'}:
            return "You may look at one of your cards. Enter the position of the card you'd like to look at. Enter -1 to decline the power."
        elif card.rank in {'9', '10'}:
            return "You may look at one of another player's cards. Enter the player number and the position of the card you'd like to look at. Enter -1 to decline the power."
        elif card.rank in {'J', 'Q'}:
            return "You may swap one of your cards with one of another player's cards. Enter the position of your card, followed by the player number and the position of the card you'd like to swap with. Enter -1 to decline the power."
        elif card.rank == 'K':
            return "You may look at another players card and decide if you want to swap with it or not. Enter the player number and the position of the card you'd like to look at. Enter -1 to decline the power."

    def use_power(self, input):
        #TODO: NEEDS MORE ERROR HANDLING
        card = self.deck.played_cards[-1]
        if card.rank not in {'7', '8', '9', '10', 'J', 'Q', 'K'}:
            return
        if len(input) == 1 and input[0] == "-1":
            return None, None
        if card.rank in {'7', '8'}:
            pos = int(input[0])
            if self.players[self.turn].cards[pos] == None:
                raise ValueError(f"You do not have a card in that position.")
            return str(self.players[self.turn].cards[pos].name()), None
        elif card.rank in {'9', '10' , 'K'}:
            if len(input) < 2:
                raise ValueError(f"Invalid input. Please try again.")
            player = int(input[0])
            pos = int(input[1])
            if player > self.num_players or player < 0:
                raise ValueError(f"Player {player} does not exist.")
            if player == self.turn:
                raise ValueError(f"You cannot look at your own card, you must choose another player.")
            if player == self.last_player and self.last_turn:
                raise ValueError(f"You cannot use a power on the player who called Cambio.")
            if self.players[player].cards[pos] == None:
                raise ValueError(f"Player {player} does not have a card in that position.")
            if card.rank != 'K':
                return str(self.players[player].cards[pos].name()), None
            return str(self.players[player].cards[pos].name()), True
        elif card.rank in {'J', 'Q'}:
            if len(input) < 3:
                raise ValueError(f"Invalid input. Please try again.")
            pos = int(input[0])
            player = int(input[1])
            pos2 = int(input[2])
            if player == self.turn:
                raise ValueError(f"You cannot swap with yourself, you must choose another player.")
            if player == self.last_player and self.last_turn:
                raise ValueError(f"You cannot use a power on the player who called Cambio.")
            self.swap(pos, player, pos2)
            return [pos, player, pos2], None

    def look_at_two(self, player):
        return [str(self.players[player].cards[0]), str(self.players[player].cards[1])]

    def call_cambio(self):
        self.last_turn = True
        self.last_player = (self.turn + self.num_players) % self.num_players

    def get_winner(self):
        best_players = []
        best_score = float('inf')
        scores = []
        for i, player in enumerate(self.players):
            score = sum([card.get_value() if card else 0 for card in player.cards])
            player.score += score
            scores.append(score)
            if score < best_score:
                best_score = score
                best_players = [i]
            elif score == best_score:
                best_players.append(i)
        s = []
        s.append("Scores for this game:")
        for i, score in enumerate(scores):
            s.append(f"\tPlayer {i}: {score}")
        s.append("")

        if len(best_players) == 1 and best_players[0] == self.last_player:
            s.append(f"The winner is {best_players[0]}, the player who called Cambio.")
        else:
            s.append(f"Player {self.last_player} called Cambio and didn't win, so they will start with an additional card next round.")
            self.extra_cards = self.last_player
            if len(best_players) == 1:
                s.append(f"The winner is Player {best_players[0]}.")
            else:
                s2 = f"The winners are: Player " + ", Player ".join(best_players) + "."
                s.append(s2)

        s.append("")

        s.append("Total scores:")
        for i, player in enumerate(self.players):
            s.append(f"\tPlayer {i}: {player.score}")
        
        return "\n".join(s) + "\n"