#!/usr/bin/env python
from webdecks import DeckGenerator
from fireplace.utils import random_draft, CardClass
from hearthstone.enums import PlayState
from fireplace.exceptions import GameOver, InvalidAction
import random
import math
from hearthstate import HearthState, Move, MOVE
import copy
from utils import random_play
import logging
from fireplace.player import Player

from mcts import uct_search


class Agent:
	name = 'Barebones Agent'

	def __init__(self, card_class: CardClass):

		self.card_class = card_class
		self._player = None
		self._deck = None
		self._game = None

	@classmethod
	def get_name(cls):
		return cls.name

	@property
	def game(self):
		return self._game

	@game.setter
	def game(self, value):
		self._game = value

	@property
	def deck(self):
		if self._deck is not None:
			return self._deck
		else:
			self._deck = DeckGenerator().get_random_deck(self.card_class)
			return self._deck

	@property
	def hero(self):
		return self.card_class.default_hero

	@property
	def player(self):
		if self._player is not None:
			return self._player
		else:
			self._player = Player(self.name, self.deck, self.hero)
			return self._player

	def is_playing(self):
		return self.player.playstate == PlayState.PLAYING and self.game.current_player == self.player



	def play_turn(self):
		pass

	def play_mulligan(self):
		pass

	def play_random_move(self):
		return random_play(self.game)


class RandomAgent(Agent):
	name = "Random Agent"

	def play_turn(self):
		self.play_random_move()

	def play_mulligan(self):
		mull_count = random.randint(0, len(self.player.choice.cards))
		cards_to_mulligan = random.sample(self.player.choice.cards, mull_count)
		self.player.choice.choose(*cards_to_mulligan)


class MonteCarloAgent(Agent):
	name = "Monte Carlo Agent"

	def play_turn(self):

		hs = HearthState(self.game)

		logging.getLogger('fireplace').setLevel('WARNING')
		root = uct_search(hs.clone(), timeout=80)
		logging.getLogger('fireplace').setLevel('DEBUG')

		while hs.game.current_player == self.player and self.player.playstate == PlayState.PLAYING:
			try:
				root = root.most_visited_child()
				move = root.move
			except ValueError:
				# print("Unexplored Node: Ending Turn")
				move = Move(MOVE.END_TURN, None, None)

			print(move.tostring(hs.game))
			try:
				hs.do_move(move)
			except InvalidAction:
				# move is no longer valid: moving on to the next best move...
				invalid_node = root
				root = root.parent  # going back
				root.children.remove(invalid_node)


	def play_mulligan(self):
		mull_count = random.randint(0, len(self.player.choice.cards))
		cards_to_mulligan = random.sample(self.player.choice.cards, mull_count)
		self.player.choice.choose(*cards_to_mulligan)


class GameStateAgent(Agent):
	name = "Game State Agent"

	def play_turn(self):

		hs = HearthState(self.game)
		while hs.game.current_player == self.player and self.player.playstate == PlayState.PLAYING:

			valid_moves = hs.get_moves()

			best_score = -math.inf
			best_move = None
			logging.getLogger('fireplace').setLevel('WARNING')
			for move in valid_moves:

				new_state = hs.clone()
				new_state.do_move(move)

				new_score = new_state.get_score(new_state.game.players[1])
				if new_score > best_score:
					best_score = new_score
					best_move = move
			logging.getLogger('fireplace').setLevel('DEBUG')

			if best_move is None:
				self.game.end_turn()
			hs.do_move(best_move)

	def play_mulligan(self):
		mull_count = random.randint(0, len(self.player.choice.cards))
		cards_to_mulligan = random.sample(self.player.choice.cards, mull_count)
		self.player.choice.choose(*cards_to_mulligan)
