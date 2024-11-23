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

class Deck():
    def __init__(self):
        self.suits = ['C', 'H', 'S', 'D']
        self.ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        self.deck = [Card(rank, suit) for suit in self.suits for rank in self.ranks]
        self.drawn = []
        self.played_cards = []

        random.shuffle(self.deck)

    def draw(self):
        card = self.deck.pop() if self.deck else None #TODO: FIGURE OUT WHAT TO DO WHEN CARDS RUN OUT
        self.drawn.append(card)
        return card

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
        self.players = [Player() for _ in range(num_players)]
        self.turn = 0
        self.num_cards = 4
        self.last_player = -1
        self.last_turn = False
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


    def game_state(self):
        #TODO: UNFINISHED
        game_state = {}
        for i, player in enumerate(self.players):
            game_state[f'Player{i}'] = str(player)
        game_state['face-up'] = str(self.deck.played_cards[-1]) if self.deck.played_cards else "None"
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
        if self.players[self.turn].cards[pos1] == None:
            raise ValueError(f"You do not have a card at position {pos1}.")
        if self.players[player2].cards[pos2] == None:
            raise ValueError(f"Player {player2} does not have a card at position {pos2}.")
        temp = self.players[self.turn].cards[pos1]
        self.players[self.turn].cards[pos1] = self.players[player2].cards[pos2]
        self.players[player2].cards[pos2] = temp

    def stick(self, stick_player, stuck_player, pos):
        if self.players[stuck_player].cards[pos] == None:
            raise ValueError(f"Player {stick_player} attempted to stick Player {stuck_player}'s card at position {pos} but there is no card there.")
        if self.players[stuck_player].cards[pos].rank != self.deck.played_cards[-1].rank:
            self.players[stick_player].cards.append(self.deck.draw())
            raise ValueError(f"Player {stick_player} attempted to stick Player {stuck_player}'s card at position {pos} but failed and has received a penalty card.")
        self.deck.played_cards.append(self.players[stuck_player].cards[pos])
        self.players[stuck_player].cards[pos] = None

    def give(self, player1, pos1, player2, pos2):
        if self.players[player1].cards[pos1] == None:
            raise ValueError(f"ERROR") #TODO
        if self.players[player2].cards[pos2] != None:
            raise ValueError(f"ERROR") #TODO
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
            if player > len(self.players) or player < 0:
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
        self.last_player = (self.turn + len(self.players)) % len(self.players)

    def get_winner(self):
        best_players = []
        best_score = float('inf')
        scores = []
        for i, player in enumerate(self.players):
            score = sum([card.get_value() for card in player.cards])
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
        
        return "\n".join(s)