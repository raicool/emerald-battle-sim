from datetime import datetime
from enum import IntEnum
import json
import math
import log
from pokemon import trainer
import utils

# ELO SYSTEM SETTINGS
# max difference between player elos
ELO_FILE: str = "dump/elo.json"
MATCHMAKING_ELO_DIFFERENCE_MAX: float = 50
K_FACTOR: float = 60
DECREASE_RATE: float = 0.2
INCREASE_RATE: float = 0.7
MAX_GAIN: float = 128
MAX_LOSS: float = -45
MIN_GAIN: float = 4
MIN_LOSS: float = -1
GAIN_CURVE: float = 2.1
LOSS_CURVE: float = 0.85

# reduces amount of elo that players lose against players that have less
# games than PLACEMENT_MATCHES 
SMURF_GAME_LOSSRATE: float = 0.85
PLACEMENT_MATCHES: int = 4

leagues: dict[float, str] = {
	0: "poke",
	1100: "great",
	1200: "ultra",
	1300: "premier",
	1400: "master",
	1500: "beast"
}

def __set_elo(_trainer: trainer, delta: float):
	_trainer.elo += delta
	for elo_min, league in leagues.items():
		if (_trainer.elo >= elo_min):
			_trainer.league = league
	_trainer.battles += 1


def calc_game_results(winner: trainer, loser: trainer, recalc: bool = False) -> tuple[trainer, trainer]:
	if (recalc == False):
		elo_dict: dict = utils.load_json(ELO_FILE)

	# calculate the chances of either player winning
	winner_chance: float = 1 / (1 + math.pow(10, (loser.elo - winner.elo) / 400))
	loser_chance: float = 1 / (1 + math.pow(10, (winner.elo - loser.elo) / 400))
	winner_gain = min(MAX_GAIN, max(MIN_GAIN, (K_FACTOR * (INCREASE_RATE - (winner_chance ** GAIN_CURVE)))))
	
	# this is bugged but i want this to be in sync with my spreadsheet
	# winner.battles + loser.battles > PLACEMENT_MATCHES
	# SHOULD BE
	# winner.battles + loser.battles < PLACEMENT_MATCHES
	if (winner.battles < PLACEMENT_MATCHES and winner.battles + loser.battles > PLACEMENT_MATCHES * 2):
		#log.debug("placement match")
		winner_gain *= 1.25
	
	loser_loss = max(MAX_LOSS, min(MIN_LOSS, K_FACTOR * (DECREASE_RATE - (loser_chance ** LOSS_CURVE))))
	if (winner.battles < PLACEMENT_MATCHES or loser.battles < PLACEMENT_MATCHES):
		#log.debug("pillow")
		loser_loss *= 0.5
	
	__set_elo(winner, winner_gain)
	winner.wins += 1

	__set_elo(loser, loser_loss)
	loser.losses += 1

	if (recalc == False):
		match_timestamp: int = datetime.now().timestamp()
		winner.last_match = match_timestamp
		loser.last_match = match_timestamp
		elo_dict[str(winner.id)] = winner.elo
		elo_dict[str(loser.id)] = loser.elo
		elo_dict["last_update"] = match_timestamp

		file = open(ELO_FILE, "w")
		json.dump(elo_dict, file)
		file.close()
	
	return tuple([winner, loser])

# tester
if __name__ == "__main__":
	_test_trainer_winner = trainer()
	_test_trainer_loser = trainer()

	_test_trainer_winner.elo = 1000
	_test_trainer_loser.elo = 1028
	_test_trainer_loser.battles = 1
	_test_trainer_loser.wins = 1

	log.log_level = log.level.DEBUG

	log.debug("\n"
		 "----------------------------------------\n"
		 "              before match\n"
		f"winner elo:{_test_trainer_winner.elo}\n"
		f"loser elo:{_test_trainer_loser.elo}\n"
		 "----------------------------------------\n"
		)
	
	calc_game_results(_test_trainer_winner, _test_trainer_loser)

	log.debug("\n"
		 "----------------------------------------\n"
		 "               after match\n"
		f"winner elo:{_test_trainer_winner.elo}\n"
		f"loser elo:{_test_trainer_loser.elo}\n"
		 "----------------------------------------\n"
		)
	pass
