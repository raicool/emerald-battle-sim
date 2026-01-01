from dataclasses import dataclass
from datetime import datetime
import json
import os
import shutil
import uuid

from pokemon import trainer
from trainer_database import trainer_database

SUMMARY_FILE: str = "dump/summary.json"

@dataclass
class summary:
	timestamp: float

	left_uuid: uuid.uuid4
	left_name: str
	left_elo_delta: float
	left_rank_delta: int


	right_uuid: uuid.uuid4
	right_name: str
	right_elo_delta: float
	right_rank_delta: int

	winner_side: int

	def __init__(self, left: trainer, right: trainer):
		self.left_elo_delta = left.elo
		self.left_rank_delta = left.rank
		self.right_elo_delta = right.elo
		self.right_rank_delta = right.rank
		self.left_uuid = left.id
		self.left_name = left.name
		self.right_uuid = right.id
		self.right_name = right.name
	
	def finalize(self, left: trainer, right: trainer, side: int):
		self.timestamp = datetime.now().timestamp()
		self.left_elo_delta -= left.elo
		self.left_rank_delta -= left.rank
		self.right_elo_delta -= right.elo
		self.right_rank_delta -= right.rank
		self.winner_side = side

		self.serialize()

	def serialize(self):
		battle_log = open(SUMMARY_FILE, "a+", encoding = "utf-8")
		battle_log.seek(0)

		log_list: list[dict] = []

		if (os.stat(SUMMARY_FILE).st_size > 0):
			log_list = json.load(battle_log)
			battle_log.seek(0)
			battle_log.truncate()

		log_list.append({
			"timestamp": self.timestamp,
			"left_uuid": self.left_uuid,
			"left_name": self.left_name,
			"left_elo_delta": self.left_elo_delta,
			"left_rank_delta": self.left_rank_delta,
			"right_uuid": self.right_uuid,
			"right_name": self.right_name,
			"right_elo_delta": self.right_elo_delta,
			"right_rank_delta": self.right_rank_delta,
			"winner_side": self.winner_side
		})

		json.dump(log_list, battle_log)
		battle_log.close()
		shutil.copy(SUMMARY_FILE, "website/html/summary.json")


if __name__ == "__main__":
	_trainerdb: trainer_database = trainer_database()
	_trainerdb.deserialize_json()
	
	_trainer_left: trainer = _trainerdb.random_trainer()
	_trainer_right: trainer = _trainerdb.random_trainer()
	battle: summary = summary(_trainer_left, _trainer_right)

	battle.finalize(_trainer_left, _trainer_right, 0)
	battle.serialize()