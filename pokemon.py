from dataclasses import dataclass, field
import json
import os
import random
import shutil
from typing import Any
import uuid

import requests

import log
import names
from poke_data import __BattleEnvironments, __BattleTransitions, __TrainerClasses, __ai_flag, __ev_order, __BattleBGMs, get_trainer_pic_id
import strings
from utils import to_charmap_index

# default ai flags for a trainer
DEFAULT_TRAINER_AI_FLAGS: int = __ai_flag.AI_FLAG_SMART_TRAINER | __ai_flag.AI_FLAG_PREDICTION | __ai_flag.AI_FLAG_KNOW_OPPONENT_PARTY
# max char array size for a trainer's name ingame
TRAINER_NAME_LENGTH: int = 10
MAX_TRAINER_ITEMS: int = 4
# chance of a shiny = 1 / SHINY_ODDS
SHINY_ODDS: int = 40
PLAYER_COUNT: int = 500

@dataclass
class rng:
	a: int = 0
	b: int = 0
	c: int = 0
	ctr: int = 0

@dataclass
class trainermon:
	nickname: str = ""
	evs: list[int] = field(default_factory=lambda: [])
	iv: int = 0xffffffff
	moves: list[int] = field(default_factory=lambda: [])
	species: int = 1
	item: int = 0
	ability: int = 0
	level: int = 1
	ball: int = 1
	friendship: int = 0xff
	nature: int = 0
	gender: int = 0
	shiny: bool = True

	def json_serialize(self):
		return json.dumps(
			self,
			default=lambda o: o.__dict__
			)

@dataclass
class trainer:
	# not saved to wram
	id: uuid.uuid4 = uuid.uuid4()
	battles: int = 0
	wins: int = 0
	losses: int = 0
	elo: float = 1000
	league: str = ""
	rank: int = 0
	# unix timestamp
	last_match: int = 0
	trainer_class: int = 0
	battle_environment: int = 0
	battle_transition: int = 0
	battle_music: str = "BATTLE_BGM_HOENN_TRAINER"
	
	gender = 0
	aiflags: int = DEFAULT_TRAINER_AI_FLAGS
	party: list[trainermon] = field(default_factory = lambda: [])
	items: list[int] = field(default_factory = lambda: [])
	trainer_pic: int = 0
	name: str = "dummy"
	party_size: int = 0

#
#	GDB-specific helper functions
#
def __trainer_info(side: str, data: trainer) -> str:
	"""formats trainer info into a string that can be parsed by gdb"""
	return str(
		f"set {side}->trainerClass = {data.trainer_class}\n"
		f"set {side}->trainerPic = {data.trainer_pic}\n"
		f"set {side}->trainerBackPic = {2 if data.gender == 0 else 3} \n"
		f"set {side}->partySize = {data.party_size}\n"
		f"set {side}->aiFlags = {data.aiflags}\n"
	)

def __trainer_name_string(side: str, data: trainer) -> str:
	"""formats trainer name into a string that can be parsed by gdb"""
	name_idx: int = 0
	ret: str = str()
	for c in data.name:
		ret += f"set {side}->trainerName[{name_idx}] = {to_charmap_index(c)}\n"
		name_idx += 1

		if (name_idx > TRAINER_NAME_LENGTH):
			break
		
	# add null terminator
	ret += str(f"set {side}->trainerName[{name_idx}] = -1\n")
	return ret

def __poke_ev_data(side: str, party_idx: int, data: list[int]):
	"""formats pokemon's ev data into a string that can be parsed by gdb"""
	if (party_idx >= 6):
		log.critical("attempted to write ev data for pokemon outside of max party size")
		return ""
	
	return str(
		f"set {side}EVData[{party_idx * 6 + __ev_order.EV_HP}] = {data[__ev_order.EV_HP]}\n"
		f"set {side}EVData[{party_idx * 6 + __ev_order.EV_ATK}] = {data[__ev_order.EV_ATK]}\n"
		f"set {side}EVData[{party_idx * 6 + __ev_order.EV_DEF}] = {data[__ev_order.EV_DEF]}\n"
		f"set {side}EVData[{party_idx * 6 + __ev_order.EV_SPEED}] = {data[__ev_order.EV_SPEED]}\n"
		f"set {side}EVData[{party_idx * 6 + __ev_order.EV_SPATK}] = {data[__ev_order.EV_SPATK]}\n"
		f"set {side}EVData[{party_idx * 6 + __ev_order.EV_SPDEF}] = {data[__ev_order.EV_SPDEF]}\n"
		f"set {side}->party[{party_idx}].ev = {side}EVData[{party_idx * 6}]\n"
	)

def gdb_trainerdata(side: int, data: trainer) -> str:
	side: str = "gTrainerLeft" if (side == 0) else "gTrainerRight"

	return str(
		__trainer_name_string(side, data) +
		__trainer_info(side, data)
	)

def gdb_partydata(side: int, data: trainer) -> str:
	trainer_side_variable: str = "gTrainerLeft" if (side == 0) else "gTrainerRight"
	ret: str = str()
	
	party = data.party
	random.shuffle(party)

	for i in range(data.party_size):
		poke_ptr: str = f"{trainer_side_variable}->party[{i}]"

		# set the ev array
		ret += __poke_ev_data(trainer_side_variable, i, party[i].evs)

		move_idx: int = 0
		for move in party[i].moves:
			if move_idx > 3:
				break
			ret += str(f"set {poke_ptr}.moves[{move_idx}] = {move}\n")
			move_idx += 1
		
		ret += str(
				f"set {poke_ptr}.heldItem = {party[i].item + 2}\n"
				f"set {poke_ptr}.ability = {party[i].ability}\n"
				f"set {poke_ptr}.species = {party[i].species}\n"
				f"set {poke_ptr}.lvl = {party[i].level}\n"
				f"set {poke_ptr}.ball = {party[i].ball}\n"
				f"set {poke_ptr}.friendship = {party[i].friendship}\n"
				f"set {poke_ptr}.nature = {party[i].nature}\n"
				f"set {poke_ptr}.gender = {party[i].gender}\n"
				f"set {poke_ptr}.isShiny = {1 if party[i].shiny else 0}\n"
			)
	return ret

def __decide(set: dict, attribute: str, default: str = "") -> Any:
	if (attribute in set):
		if (type(set[attribute]) is list):
			set[attribute] = random.choice(set[attribute])
	else:
		set[attribute] = default
	return set[attribute]

def generate_pkmn(pkmn_database: dict) -> trainermon:
	which_pkmn: tuple = random.choice(list(pkmn_database.items()))
	pokemon_name: str = which_pkmn[0]

	if ("Deoxys" in pokemon_name):
		pokemon_name = "Deoxys-Normal"

	log.trace("i choose you, " + pokemon_name + "!")

	tier = random.choice(list(which_pkmn[1].items()))
	set: dict = random.choice(list(tier[1].items()))[1]

	#log.trace("\tset will be: " + set)

	move: list = list([0, 0, 0, 0])
	move_idx: int = 0
	for _data in set["moves"]:
		if (type(_data) is list):
			_data = random.choice(_data)
		
		if ("Hidden Power" in _data):
			_data = "Hidden Power"

		move[move_idx] = strings.move_name.index(_data)

		log.trace("\t\t" + strings.move_name[move[move_idx]])
		move_idx += 1
	
	log.trace("\t\t\t" + __decide(set, "item", "No Item"))

	# if no ability is set, the game will decide which ability the pokemon gets based on mon's personality values
	# personality trait will stay the same as long as the pokemon's checksum remains the same, so the randomly chosen
	# ability will stay the same for every battle
	__decide(set, "ability", "None")
	__decide(set, "nature", "Hardy")
	__decide(set, "evs")

	_evs: list[int] = [0, 0, 0, 0, 0, 0]
	for stat in set["evs"]:
		value: int = set["evs"][stat]
		match stat:
			case "hp": _evs[__ev_order.EV_HP] = value
			case "atk": _evs[__ev_order.EV_ATK] = value
			case "def": _evs[__ev_order.EV_DEF] = value
			case "spe": _evs[__ev_order.EV_SPEED] = value
			case "spa": _evs[__ev_order.EV_SPATK] = value
			case "spd": _evs[__ev_order.EV_SPDEF] = value
	log.trace(_evs)

	return trainermon(
		species = strings.pokemon.index(pokemon_name),
		moves = move,
		shiny = random.randint(0, SHINY_ODDS) == 0,
		level = 100,
		item = strings.item.index(set["item"]),
		ability = strings.ability.index(set["ability"]),
		evs = _evs,
		ball = random.randint(0, 26),
		nature = strings.nature.index(set["nature"])
	)

def fetch_sets() -> dict:
	log.trace("fetching smogon gen 3 sets")
	response = requests.get("https://pkmn.github.io/smogon/data/sets/gen3.json")
	return response.json()

def construct_trainer_json(_trainer: trainer):
	_json: dict = {}
	_json["id"] = str(_trainer.id)
	_json["name"] = _trainer.name
	_json["battles"] = _trainer.battles
	_json["wins"] = _trainer.wins
	_json["losses"] = _trainer.losses
	_json["elo"] = _trainer.elo
	_json["last_match"] = _trainer.last_match
	_json["trainer_class"] = _trainer.trainer_class
	_json["battle_environment"] = _trainer.battle_environment
	_json["battle_transition"] = _trainer.battle_transition
	_json["battle_music"] = _trainer.battle_music
	_json["gender"] = _trainer.gender
	_json["aiflags"] = _trainer.aiflags
	_json["trainer_pic"] = _trainer.trainer_pic
	pkmn_list_json: list[str] = []
	for pkmn in _trainer.party:
		pkmn_list_json.append(str(pkmn.json_serialize()))
	_json["party"] = pkmn_list_json
	return _json

def backup():
	if (os.path.exists("dump_old")):
		shutil.rmtree("dump_old")
	os.mkdir("dump_old")
	
	allfiles = os.listdir("dump")
	for f in allfiles:
		src_path = os.path.join("dump", f)
		dst_path = os.path.join("dump_old", f)
		os.rename(src_path, dst_path)

def main():
	log.log_level = log.level.DEBUG
	if (os.path.exists("dump") == False):
		os.mkdir("dump")
	backup()
	json_response = fetch_sets()
	trainers_json = open("dump/trainers.json", "w+")
	trainers_txt = open("dump/trainers.txt", "w+")
	trainer_mons_txt = open("dump/trainer_mons.txt", "w+")

	trainers: dict = {}
	for _ in range(PLAYER_COUNT):
		gender: int = random.randint(0, 1)
		test_trainer: trainer = trainer()

		test_trainer.id = uuid.uuid4()
		test_trainer.party_size = 6
		test_trainer.trainer_class = random.randint(0, __TrainerClasses.TRAINER_CLASS_COUNT - 1)
		test_trainer.gender = random.randint(0, 1)
		test_trainer.trainer_pic = get_trainer_pic_id(test_trainer.trainer_class, test_trainer.gender, test_trainer.id)
		test_trainer.battle_environment = random.randint(0, __BattleEnvironments.BATTLE_ENVIRONMENT_RAYQUAZA - 1)
		test_trainer.battle_transition = random.randint(0, __BattleTransitions.B_TRANSITION_COUNT - 1)
		test_trainer.battle_music = random.choice(list(__BattleBGMs.keys()))
		test_trainer.gender = random.randint(0, 1)
		test_trainer.aiflags = DEFAULT_TRAINER_AI_FLAGS

		if (gender == 0):
			test_trainer.name = random.choice(names.male)
		else:
			test_trainer.name = random.choice(names.female)

		for i in range(6):
			new_pkmn = generate_pkmn(json_response)
			test_trainer.party.append(new_pkmn)
		
		trainers[_] = construct_trainer_json(test_trainer)
		trainers_txt.write("{}\t{}\t{}\n".format(
			trainers[_]["id"],
			trainers[_]["name"],
			trainers[_]["trainer_class"]
		))
		trainer_mons_txt.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
			trainers[_]["id"],
			test_trainer.party[0].species,
			test_trainer.party[1].species,
			test_trainer.party[2].species,
			test_trainer.party[3].species,
			test_trainer.party[4].species,
			test_trainer.party[5].species,
		))

	json.dump(trainers, trainers_json)
	trainers_json.close()
	trainers_txt.close()
	trainers_json.close()

if __name__ == "__main__":
	main()
#	_trainerdb: trainer_database = trainer_database()
#	_trainerdb.deserialize_json()
#	_trainerdb.recalculate("dump/battle_log.txt")
	pass
