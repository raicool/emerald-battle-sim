import elo
import log
from pokemon import trainer
from trainer_database import trainer_database


def find_match(database: trainer_database, self_battle_enable: bool = False, self_trainer_id: str = "") -> tuple[trainer, trainer]:
	matchmaking: bool = True
	attempts: int = 1
	range = elo.MATCHMAKING_ELO_DIFFERENCE_MAX

	# simulate a ranked matchmaking system
	if (self_battle_enable == False):
		while (1):
			trainer_left: trainer = database.random_trainer()
			if (trainer_left.id != self_trainer_id):
				break
	else:
		trainer_left: trainer = database.trainer_from_uuid(self_trainer_id)


	while (matchmaking):
		trainer_right: trainer = database.random_trainer()
        
		if (trainer_left.id == trainer_right.id):
			log.trace("avoiding ditto battle!")
			continue

		if (abs(trainer_left.elo - trainer_right.elo) < range and trainer_right.id != self_trainer_id):
			matchmaking = False
			break
		else:
			attempts += 1
			if (attempts > range):
				range += elo.MATCHMAKING_ELO_DIFFERENCE_MAX
	
	return trainer_left, trainer_right