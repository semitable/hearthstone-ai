#!/usr/bin/env python

import logging
from fireplace import cards
from fireplace.exceptions import GameOver
from fireplace.game import Game
from fireplace.player import Player
from fireplace.utils import random_draft
from hearthstone.enums import CardClass, CardType, PlayState
from webdecks import DeckGenerator
import time

from agent import RandomAgent, MonteCarloAgent, GameStateAgent


def setup_game() -> "Game":
	deck_generator = DeckGenerator()

	deck1 = deck_generator.get_random_deck(CardClass.PALADIN)
	deck2 = deck_generator.get_random_deck(CardClass.WARRIOR)

	player1 = Player("Player1", deck1, CardClass.PALADIN.default_hero)
	player2 = Player("Player2", deck2, CardClass.WARRIOR.default_hero)

	game = Game(players=(player1, player2))
	game.start()
	return game


def main():
	game = setup_game()

	agents = {}

	agents[game.players[0]] = MonteCarloAgent(game, game.players[0])
	agents[game.players[1]] = GameStateAgent(game, game.players[1])

	for _, agent in agents.items():
		agent.play_mulligan()

	try:
		while True:
			# time.sleep(1)
			agents[game.current_player].play_turn()
	except GameOver:
		for _, agent in agents.items():
			if agent.player.playstate == PlayState.LOST:
				print("{} ({}) lost".format(agent.name, agent.player.hero))
			else:
				print("{} ({}) won".format(agent.name, agent.player.hero))
				score[agent.player.name] = score[agent.player.name] + 1


if __name__ == "__main__":
	logging.getLogger('fireplace').setLevel('WARNING')
	score = dict()
	score['Player1'] = 0
	score['Player2'] = 0

	cards.db.initialize()
	for _ in range(100):
		main()
		print(score)
