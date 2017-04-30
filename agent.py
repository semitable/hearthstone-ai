#!/usr/bin/env python
from webdecks import DeckGenerator
from fireplace.utils import random_draft, CardClass
from hearthstone.enums import PlayState
from fireplace.exceptions import GameOver
import random
import math
from hearthstate import HearthState, Move, MOVE
import copy
from utils import random_play

from mcts import uct_search


class Agent:
	def __init__(self, game, player):
		self.game = game
		self.player = player

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

		root = uct_search(hs.clone(), timeout=10)

		while hs.game.current_player == self.player and self.player.playstate == PlayState.PLAYING:
			try:
				root = root.best_child(0)
				move = root.move
			except ValueError:
				print("Unexplored Node: Ending Turn")
				move = Move(MOVE.END_TURN, None, None)

			# print(move.tostring(hs.game))
			hs.do_move(move)

	def play_mulligan(self):
		mull_count = random.randint(0, len(self.player.choice.cards))
		cards_to_mulligan = random.sample(self.player.choice.cards, mull_count)
		self.player.choice.choose(*cards_to_mulligan)


class GameStateAgent(Agent):
	name = "Game State Agent"

	def play_turn(self):

		hs = HearthState(self.game)
		valid_moves = hs.get_moves()

		best_score = -math.inf
		best_move = None

		for move in valid_moves:

			new_state = hs.clone()
			new_state.do_move(move)

			new_score = new_state.get_score(new_state.game.players[1])
			if new_score > best_score:
				best_score = new_score
				best_move = move

		if best_move is None:
			self.game.end_turn()
		hs.do_move(best_move)

	def play_mulligan(self):
		mull_count = random.randint(0, len(self.player.choice.cards))
		cards_to_mulligan = random.sample(self.player.choice.cards, mull_count)
		self.player.choice.choose(*cards_to_mulligan)
