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

from agent import RandomAgent, MonteCarloAgent, GameStateAgent, Agent


def setup_game() -> (Game, (Agent, Agent)):
	agent1 = MonteCarloAgent(CardClass.WARRIOR)
	agent2 = GameStateAgent(CardClass.PALADIN)

	print(agent1.player, " vs ", agent2.player)

	game = Game(players=(agent1.player, agent2.player))

	agent1.game = game
	agent2.game = game

	game.start()

	return game, (agent1, agent2)


def main():
	game, agents = setup_game()

	agents[0].play_mulligan()
	agents[1].play_mulligan()

	agent_playing = None

	try:
		while True:
			agent_playing = agents[0] if agents[0].is_playing() else agents[1]
			game.log("{} thinking...".format(agent_playing.get_name()))
			time_start = time.time()
			agent_playing.play_turn()
			game.log("{} took {} seconds".format(agent_playing.get_name(), time.time() - time_start))


	except GameOver:
		print("{} ({}) won".format(agent_playing.name, agent_playing.player.hero))
		try:
			score[agent_playing.player.name] = score[agent_playing.player.name] + 1
		except KeyError:
			score[agent_playing.player.name] = 1


if __name__ == "__main__":

	score = dict()

	cards.db.initialize()
	for _ in range(10):
		main()
		print(score)
