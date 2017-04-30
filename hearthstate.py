from hearthstone.enums import PlayState
import math
import copy
from enum import Enum
from fireplace import cards
from fireplace.deck import Deck
from hearthstone.enums import CardType, Rarity, PlayState, CardClass

import itertools


class MOVE(Enum):
	PRE_GAME = 1
	PICK_CLASS = 2
	PICK_CARD = 3
	END_TURN = 4
	HERO_POWER = 5
	MINION_ATTACK = 6
	HERO_ATTACK = 7
	PLAY_CARD = 8
	MULLIGAN = 9
	CHOICE = 10


class Move:
	def __init__(self, type, card, target):
		self.type = type
		self.card_index = card
		self.target_index = target

	def tostring(self, state):
		if self.type == MOVE.END_TURN:
			return str(MOVE.END_TURN)
		elif self.type == MOVE.HERO_POWER:
			if self.target_index is None:
				return str(MOVE.HERO_POWER)
			else:
				return "{} to {}".format(MOVE.HERO_POWER, state.hero.power.targets[self.target_index])
		elif self.type == MOVE.PLAY_CARD:
			card = state.current_player.hand[self.card_index]
			if self.target_index is None:
				return "{}: {}".format(MOVE.PLAY_CARD, card)
			else:
				return "{}: {} to {}".format(MOVE.PLAY_CARD, card, card.targets[self.target_index])

		elif self.type == MOVE.MINION_ATTACK:
			minion = state.current_player.field[self.card_index]
			return "{}: {} to {}".format(MOVE.MINION_ATTACK, minion, minion.targets[self.target_index])
		elif self.type == MOVE.HERO_ATTACK:
			hero = state.current_player.hero
			return "{} to {}".format(MOVE.HERO_ATTACK, hero.targets[self.target_index])
		elif self.type == MOVE.CHOICE:
			raise NotImplemented
		# self.game.current_player.choice.choose(move.card_index)
		else:
			raise NameError("DoMove ran into unclassified card", self)

		#
		# def __repr__(self):
		# 	if self.target is None:
		# 		return "{}: {}".format(self.type, self.card)
		# 	return "{}: {} on {}".format(self.type, self.card, self.target)


class MoveSequence:
	def __init__(self):
		self.moves = []

	def freeze(self):
		self.moves = tuple(self.moves)

	def __hash__(self):
		hash(self.moves)

	def __repr__(self):
		return str(self.moves)

	def is_valid(self, state):
		return True

	def clean(self):
		pass


class HearthState:
	def __init__(self, game):
		self.game = game

	def clone(self):
		""" Create a deep clone of this game state.
		"""
		game = copy.deepcopy(self.game)
		return HearthState(game)

	def calculate_minion_score(self, minion):
		minionScore = minion.atk + minion.health
		baseScore = minionScore

		if minion.frozen:
			return minion.health

		if minion.taunt:
			minionScore += 2

		if minion.windfury:
			minionScore += minion.getAttack() * 0.5

		if minion.divine_shield:
			minionScore += 1.5 * baseScore

		if minion.spellpower:
			minionScore += minion.spellpower

		if minion.enrage:
			minionScore += 1

		if minion.stealthed:
			minionScore += 1

		if minion.cant_be_targeted_by_opponents:
			minionScore += 1.5 * baseScore

		return minionScore

	def get_score(self, player):
		score = 0

		opponent = self.game.players[1] if self.game.players[0] == player else self.game.players[0]

		if player.playstate == PlayState.WON:
			return math.inf
		elif player.playstate == PlayState.LOST or player.playstate == PlayState.LOSING:
			return -math.inf

		own_hp = player.hero.health + player.hero.armor
		opp_hp = opponent.hero.health + opponent.hero.armor

		score += own_hp - opp_hp

		score += 3 * len(player.hand)
		score -= 3 * len(opponent.hand)

		score += 2 * len(player.field)
		score -= 2 * len(opponent.field)

		score += sum(map(self.calculate_minion_score, player.field))
		score -= sum(map(self.calculate_minion_score, opponent.field))

		return score

	def get_moves(self):

		if self.game is not None:
			if self.game.current_player.playstate != PlayState.PLAYING:
				return []
		valid_moves = []

		for card in self.game.current_player.hand:
			if card.is_playable():
				if card.requires_target():
					for t in range(len(card.targets)):
						valid_moves.append(Move(MOVE.PLAY_CARD, self.game.current_player.hand.index(card), t))
				else:
					valid_moves.append(Move(MOVE.PLAY_CARD, self.game.current_player.hand.index(card), None))

		# Hero Power
		heropower = self.game.current_player.hero.power
		if heropower.is_usable():
			if heropower.requires_target():
				for t in range(len(heropower.targets)):
					valid_moves.append(Move(MOVE.HERO_POWER, None, t))
			else:
				valid_moves.append(Move(MOVE.HERO_POWER, None, None))

		# Minion Attack
		for minion in self.game.current_player.field:
			if minion.can_attack():
				for t in range(len(minion.targets)):
					valid_moves.append(Move(MOVE.MINION_ATTACK, self.game.current_player.field.index(minion), t))

		# Hero Attack
		hero = self.game.current_player.hero
		if hero.can_attack():
			for t in range(len(hero.targets)):
				valid_moves.append(Move(MOVE.HERO_ATTACK, None, t))

		valid_moves.append(Move(MOVE.END_TURN, None, None))

		return valid_moves

	def do_move(self, move: Move):
		""" Update a state by carrying out the given move.
		"""
		try:
			if move.type == MOVE.END_TURN:
				self.game.end_turn()
			elif move.type == MOVE.HERO_POWER:
				heropower = self.game.current_player.hero.power
				if move.target_index is None:
					heropower.use()
				else:
					heropower.use(target=heropower.targets[move.target_index])
			elif move.type == MOVE.PLAY_CARD:
				card = self.game.current_player.hand[move.card_index]
				if move.target_index is None:
					card.play()
				else:
					card.play(target=card.targets[move.target_index])
			elif move.type == MOVE.MINION_ATTACK:
				minion = self.game.current_player.field[move.card_index]
				minion.attack(minion.targets[move.target_index])
			elif move.type == MOVE.HERO_ATTACK:
				hero = self.game.current_player.hero
				hero.attack(hero.targets[move.target_index])
			elif move.type == MOVE.CHOICE:
				raise NotImplemented("Should Implement choice move")
			# self.game.current_player.choice.choose(move.card_index)
			else:
				raise NameError("DoMove ran into unclassified card", move)
		except NameError as e:
			print(e)
			return
