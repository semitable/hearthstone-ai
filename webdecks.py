import json
import pickle
import random

import requests
from fireplace import cards
from hearthstone.enums import CardClass


class TempoStorm:
    snapshot_url = 'https://tempostorm.com/api/snapshots/findOne'
    deck_url = 'https://tempostorm.com/api/decks/findOne'

    def get_snapshot(self):
        payload = {"filter": """
		{  
		   "where":{  
			  "slug":"2017-04-23",
			  "snapshotType":"standard"
		   },
		   "include":[  
			  {  
				 "relation":"deckTiers",
				 "scope":{  
					"include":[  
					   {  
						  "relation":"deck",
						  "scope":{  
							 "fields":[  
								"id",
								"name",
								"slug",
								"playerClass"
							 ],
							 "include":{  
								"relation":"slugs",
								"scope":{  
								   "fields":[  
									  "linked",
									  "slug"
								   ]
								}
							 }
						  }
					   },
					   {  
						  "relation":"deckTech",
						  "scope":{  
							 "include":[  
								{  
								   "relation":"cardTech",
								   "scope":{  
									  "include":[  
										 {  
											"relation":"card",
											"scope":{  
											   "fields":[  
												  "name",
												  "photoNames"
											   ]
											}
										 }
									  ]
								   }
								}
							 ]
						  }
					   }
					]
				 }
			  },
			  
			  {  
				 "relation":"votes",
				 "scope":{  
					"fields":[  
					   "direction",
					   "authorId"
					]
				 }
			  },
			  {  
				 "relation":"slugs",
				 "scope":{  
					"fields":[  
					   "linked",
					   "slug"
					]
				 }
			  }
		   ]
		}
		"""}
        r = requests.get(self.snapshot_url, params=payload)

        decks = r.json()

        deck_ids = []
        for d in decks['deckTiers']:
            deck_ids.append(d['deck']['id'])

        return deck_ids

    def get_deck(self, id):

        deck_filter = {
            "where": {
                "id": id
            },
            "fields": [
                "id",
                "createdDate",
                "name",
                "description",
                "playerClass",
                "premium",
                "dust",
                "heroName",
                "authorId",
                "deckType",
                "isPublic",
                "chapters",
                "youtubeId",
                "gameModeType",
                "isActive",
                "isCommentable"
            ],
            "include": [
                {
                    "relation": "cards",
                    "scope": {
                        "include": "card",
                        "scope": {
                            "fields": [
                                "id",
                                "name",
                                "cardType",
                                "cost",
                                "dust"
                            ]
                        }
                    }
                },
                {
                    "relation": "matchups",
                    "scope": {
                        "fields": [
                            "forChance",
                            "deckName",
                            "className"
                        ]
                    }
                },
                {
                    "relation": "votes",
                    "fields": [
                        "id",
                        "direction",
                        "authorId"
                    ]
                }
            ]
        }

        payload = {"filter": json.dumps(deck_filter)}
        r = requests.get(self.deck_url, params=payload)
        json_deck = r.json()

        player_class = CardClass[json_deck['playerClass'].upper()]

        deck = []
        for c in json_deck['cards']:
            quantity = c['cardQuantity']
            try:
                cls = cards.db[c['card']['hearthstoneId']]
            except:

                try:
                    cls = cards.db[cards.filter(name=c['card']['name'])[0]]
                except:
                    print("Not found: {}".format(c['card']['name']))
                    return player_class, None
            # print("{} x{}".format(cls, c['cardQuantity']))

            for _ in range(quantity):
                deck.append(cls.id)

        if len(deck) != 30:
            return player_class, None

        return player_class, deck


class DeckGenerator:
    def __init__(self, tempostorm=TempoStorm()):
        try:
            self.deck_db = pickle.load(open("deck_db.p", "rb"))
        except:
            self.deck_db = dict()

            for player_class in CardClass:
                self.deck_db[player_class] = []

            all_decks = tempostorm.get_snapshot()
            for d in all_decks:
                player_class, deck = tempostorm.get_deck(d)
                if deck is None:
                    continue
                self.deck_db[player_class].append(deck)

            pickle.dump(self.deck_db, open("deck_db.p", "wb"))

    def get_random_deck(self, player_class):
        return random.choice(self.deck_db[player_class])


if __name__ == "__main__":
    deck_generator = DeckGenerator()

    print(deck_generator.generate_deck(CardClass.WARRIOR))
