from dataclasses import dataclass, field
from datetime import datetime
import json
import os
import random
import shutil
import uuid
from elo import calc_game_results
import elo
import log
import names
from poke_data import get_rand_trainer_class, get_trainer_pic_id
from pokemon import construct_trainer_json, trainer, trainermon
import utils


@dataclass
class trainer_database:
	trainer_count: int = 0
	db: list = field(default_factory=lambda: [])

	def deserialize_json(self):
		trainers_json = open("dump/trainers.json", "r", encoding = "utf-8")
		self.db: dict = json.load(trainers_json, object_hook = dict[str, trainer])
		self.trainer_count = len(self.db)
	
	def serialize_json(self):
		trainers_json = open("dump/trainers.json", "w")
		json.dump(self.db, trainers_json)
		trainers_json.close()
		shutil.copy("dump/trainers.json", "website/trainers.json")
	
	def __trainer_struct_from_list_obj(self, entry: list):
		_temp: trainer = trainer()
		_temp.name = entry.get("name", "dummy")
		_temp.id = entry.get("id", 0)
		_temp.battles = entry.get("battles", 0)
		_temp.wins = entry.get("wins", 0)
		_temp.losses = entry.get("losses", 0)
		_temp.elo = entry.get("elo", 1000)
		_temp.league = entry.get("league", "")
		_temp.rank = entry.get("rank", 0)
		_temp.last_match = entry.get("last_match", 0)
		_temp.trainer_class = entry.get("trainer_class", 0)
		_temp.battle_environment = entry.get("battle_environment", 0)
		_temp.battle_transition = entry.get("battle_transition", 0)
		_temp.battle_music = entry.get("battle_music", "")
		_temp.gender = entry.get("gender", 0)
		_temp.aiflags = entry.get("aiflags", 0)
		_temp.trainer_pic = entry.get("trainer_pic", 0)
		_temp.party = entry.get("party", [])
		_temp.party_size = min(6, len(_temp.party))
		return _temp

	def __trainer_set_from_struct_obj(self, idx: int, entry: trainer):
		self.db[idx] = construct_trainer_json(entry)

	def random_trainer(self) -> trainer:
		entry: list = self.db[str(random.randint(0, self.trainer_count - 1))]
		log.debug(entry)
		return self.__trainer_struct_from_list_obj(entry)

	def trainer_from_uuid(self, uuid: str):
		for i in self.db.values():
			if i["id"] == uuid:
				return self.__trainer_struct_from_list_obj(i)
		return None
	
	def update_trainer(self, uuid: str, new_data: trainer):
		idx: int = self.find_trainer_index(uuid)
		self.__trainer_set_from_struct_obj(idx, new_data)
	
	# returns -1 if no trainer with uuid is found
	def find_trainer_index(self, uuid: str) -> int:
		for i in self.db:
			if self.db[i]["id"] == uuid:
				return i
		return -1
	
	def rank_trainers(self, elo_file):
		elo_file.seek(0)
		elos: dict[int, float] = json.load(elo_file)
		sorted_elos = sorted(elos.items(), key=lambda kv: kv[1], reverse = True)
		rank: int = 1
		for id, elo in sorted_elos:
			index = self.find_trainer_index(id)
			self.db[index]["rank"] = rank
			rank += 1
	
	def recalculate(self, log_path: str):
		if (os.path.isfile(log_path) == False):
			log.critical("attempted to recalculate db elo with invalid battle log file!\n\t^~~ file does not exist")
			return
		battle_log = open(log_path, "r+", encoding = "utf-16")
		elo_json = open(elo.ELO_FILE, "r+", encoding = "utf-8")
		

		for player in self.db.values():
			# if you would like to set a value for all trainers in your database, this is where you would do it
			player["battles"] = 0
			player["wins"] = 0
			player["losses"] = 0
			player["elo"] = 1000

		elos: dict[int, float] = {}
		while split := battle_log.readline().rsplit():
			if (len(split) < 2): continue
			winner_uuid: str = split[0]
			loser_uuid: str = split[1]

			# get trainers from database
			winner = self.find_trainer_index(winner_uuid)
			loser = self.find_trainer_index(loser_uuid)

			new_elos: tuple[trainer, trainer] = calc_game_results(
				self.trainer_from_uuid(winner_uuid),
				self.trainer_from_uuid(loser_uuid),
				True
			)
			if (len(split) >= 3):
				timestamp: float = float(split[2])
			else:
				timestamp = 0

			self.db[winner]["last_match"] = timestamp
			self.db[winner]["elo"] = new_elos[0].elo
			self.db[winner]["league"] = new_elos[0].league
			self.db[winner]["battles"] = new_elos[0].battles
			self.db[winner]["wins"] = new_elos[0].wins
			elos[new_elos[0].id] = new_elos[0].elo

			self.db[loser]["last_match"] = timestamp
			self.db[loser]["elo"] = new_elos[1].elo
			self.db[loser]["league"] = new_elos[1].league
			self.db[loser]["battles"] = new_elos[1].battles
			self.db[loser]["losses"] = new_elos[1].losses
			elos[new_elos[1].id] = new_elos[1].elo

			#log.debug(f"winner: {winner_uuid}\nloser: {loser_uuid}")
		
		# scuffed method of calculating player rank
		
		json.dump(elos, elo_json)
		self.rank_trainers(elo_json)
		elo_json.close()

		self.serialize_json()