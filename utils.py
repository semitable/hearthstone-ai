from fireplace.game import Game
import random


def random_play(game: Game) -> Game:
	player = game.current_player

	while True:
		heropower = player.hero.power
		if heropower.is_usable() and random.random() < 0.1:
			if heropower.requires_target():
				heropower.use(target=random.choice(heropower.targets))
			else:
				heropower.use()
			continue

		# iterate over our hand and play whatever is playable
		for card in player.hand:
			if card.is_playable() and random.random() < 0.5:
				target = None
				if card.must_choose_one:
					card = random.choice(card.choose_cards)
				if card.requires_target():
					target = random.choice(card.targets)
				card.play(target=target)

				if player.choice:
					choice = random.choice(player.choice.cards)
					player.choice.choose(choice)

				continue

		# Randomly attack with whatever can attack
		for character in player.characters:
			if character.can_attack():
				character.attack(random.choice(character.targets))

		break

	game.end_turn()
	return game
