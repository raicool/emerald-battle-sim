import elo
import log
from pokemon import trainer
from trainer_database import trainer_database


def find_match(database: trainer_database) -> tuple[trainer, trainer]:
    matchmaking: bool = True
    attempts: int = 1
    range = elo.MATCHMAKING_ELO_DIFFERENCE_MAX

    # simulate a ranked matchmaking system

    trainer_left: trainer = database.trainer_from_uuid("9d331366-be96-47ce-a667-754ecbe7cb54")
    #trainer_left: trainer = database.random_trainer()
    while (matchmaking):
        trainer_right: trainer = database.random_trainer()

        if (trainer_left.id == trainer_right.id):
            log.trace("avoiding ditto battle!")
            continue

        if (abs(trainer_left.elo - trainer_right.elo) < range):
            matchmaking = False
            break
        else:
            attempts += 1
            if (attempts > range):
                range += elo.MATCHMAKING_ELO_DIFFERENCE_MAX
    
    return trainer_left, trainer_right