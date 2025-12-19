from asyncio import sleep
from datetime import datetime
import threading
from time import time
import os
import random
import signal
from colorama import Fore
from pygdbmi.gdbcontroller import GdbController
import subprocess
import elo
import gdb
import leaderboard
import log

from matchmaking import find_match
from poke_data import __BattleOutcomeWinner, __BattleBGMs, __BattleBGM_RankOne
from pokemon import gdb_trainerdata, gdb_partydata, rng, trainer
from trainer_database import trainer_database

# currently headless mgba does not work with gdb
# would be a free 5x speed boost but whatever ig
MGBA_PATH: str = "res/mgba/mgba.exe"
ELF_BINARY_PATH: str = "res/pokeemerald.elf"
ELF_LINKER_MAP_PATH: str = "res/pokeemerald.map"
BATTLE_SAVESTATE: str = "res/startbattle_no_animations.ss0"
BATTLE_SCRIPT: str = "res/battle.lua"

GAME_FASTFORWARD: bool = True
FRAME_SIZE: int = 4

if (GAME_FASTFORWARD):
	# fast settings
	AUDIO_SYNC: bool = False
	VIDEO_SYNC: bool = False
	FPS_TARGET: int = 25565
	GAME_VOLUME: int = 0
else:
	# normal speed settings
	AUDIO_SYNC: bool = True
	VIDEO_SYNC: bool = True
	FPS_TARGET: int = 59.7275
	GAME_VOLUME: int = 100


def call_mgba() -> subprocess.Popen:
	settings: str = "-C audioSync={} -C videoSync={} -C fpsTarget={} -C volume={} -C frameSize={}".format(
		(1 if AUDIO_SYNC else 0),
		(1 if VIDEO_SYNC else 0),
		FPS_TARGET,
		GAME_VOLUME,
		FRAME_SIZE
	)

	cmd: str = "{} -g -t \"{}\" {} {}".format(
		MGBA_PATH,
		BATTLE_SAVESTATE,
		settings,
		ELF_BINARY_PATH
	)

	log.debug(cmd)

	return subprocess.Popen(cmd)

_trainerdb: trainer_database = trainer_database()

def write_battle_log(winner: trainer, loser: trainer):
	f = open("dump/battle_log.txt", "a", encoding="utf-16")
	battle_time = datetime.now().timestamp()
	f.write(f"{winner.id}\t{loser.id}\t{battle_time}\n")
	f.close()

def log_trainer_introduction(left: trainer, right: trainer):
	left_card: str = str(f"{left.name} ({int(left.elo)})") 
	right_card: str = str(f"{right.name} ({int(right.elo)})") 
	log.trace(
			"\n----------------------------------------------------------------------------"
		   f"\n{left_card:^36} vs {right_card:^36}"
		   f"\n{Fore.LIGHTBLACK_EX}{left.id}    {right.id}{Fore.RESET}"
			"\n----------------------------------------------------------------------------"
		)

def main():
	log.__initLoggerFile()

	global _trainerdb
	battle_count: int = 0
	
	while (1):
		__gBattleEnvironment: int = 0
		__gBattleTransition: int = 0
		__gBattleMusic: int = 0
		__gRngValue: rng = rng()
		
		_trainerdb.deserialize_json()
		_trainerdb.recalculate("dump/battle_log.txt")
		leaderboard.update_html(_trainerdb)
		log.log_level = log.level.TRACE

		battle_count += 1

		# basic matchmaking
		# finds two trainers inside of the database with similar elo
		trainer_left, trainer_right = find_match(_trainerdb)

		# set the battle details to right trainer's preferred settings
		__gBattleEnvironment = trainer_right.battle_environment
		__gBattleTransition = trainer_right.battle_transition
		if (trainer_right.rank == 1):
			__gBattleMusic = __BattleBGM_RankOne
		else:
			__gBattleMusic = __BattleBGMs.get(trainer_right.battle_music, __BattleBGMs["BATTLE_BGM_HOENN_TRAINER"])
		__gRngValue.a = random.randint(0, 0xffffffff)
		__gRngValue.b = random.randint(0, 0xffffffff)
		__gRngValue.c = random.randint(0, 0xffffffff)
		__gRngValue.ctr = random.randint(0, 0xffffffff)
		in_battle: bool = True
		
		log_trainer_introduction(trainer_left, trainer_right)

		game_proc = call_mgba()
		debugger = GdbController(["arm-none-eabi-gdb.exe", "--interpreter=mi3"], 2)
		gdb.write_command(debugger, f'file {ELF_BINARY_PATH}\ntarget remote :2345', 1)
		gdb.write_command(debugger,
# set battle rng
			f"set gRngValue.a = {__gRngValue.a}\n"
			f"set gRngValue.b = {__gRngValue.b}\n"
			f"set gRngValue.c = {__gRngValue.c}\n"
			f"set gRngValue.ctr = {__gRngValue.ctr}\n"

# set my custom variables
			"set $outcome = 0\n"
			f"set gBattleMusic = {__gBattleMusic}\n"
			f"set gBattleTransition = {__gBattleTransition}\n"
			f"set gTrainerLeftTrainerBackPicID = {4 if trainer_left.gender == 0 else 5}\n"
			f"set gTrainerRightTrainerPicID = {trainer_right.trainer_pic}\n"

# __attribute__((section(".sbss"))) bool32 gTrainerInitDone
			"watch gTrainerInitDone\n"
			"commands\n"
			f"{gdb_trainerdata(0, trainer_left)}\n"
			f"{gdb_trainerdata(1, trainer_right)}\n"
			f"{gdb_partydata(0, trainer_left)}\n"
			f"{gdb_partydata(1, trainer_right)}\n"
			"c\n"
			"end\n"

# void InitBattleBgsVideo(void)
			"break InitBattleBgsVideo\n"
			"commands\n"
			f"set gBattleEnvironment = {__gBattleEnvironment}\n"
			"c\n"
			"end\n"

# __attribute__((section(".sbss"))) u8 gBattleOutcome
			"watch gBattleOutcome if gBattleOutcome > 0\n"
			"commands\n"
			"set $outcome = gBattleOutcome\n"
			"end\n"

			"c", 
			timeout = 0.5
			)
		
		while (in_battle):
			# veery hacky way of figuring out the battle winner
			# i hate using gdb
			response: list[dict] = gdb.write_command(debugger, "p/x $outcome", 5)

			if game_proc.poll() is not None:
				# assume game_process is terminated willingly
				in_battle = False
				break

			if (len(response) == 0): continue

			payload = response[1].get("payload", "")

			if (type(payload) is str):
				try:
					int(payload.rsplit("0x")[1])
				except IndexError:
					continue
				except ValueError:
					log.trace("something went wrong")
					in_battle = False
					os.kill(game_proc.pid, signal.SIGTERM)
					break

				result: int = int(payload.rsplit("0x")[1])

				match result:
					case __BattleOutcomeWinner.BATTLE_OUTCOME_WINNER_LEFT:
						end_battle(trainer_left, trainer_right)
						pass
					case __BattleOutcomeWinner.BATTLE_OUTCOME_WINNER_RIGHT:
						end_battle(trainer_right, trainer_left)
						pass
					case __BattleOutcomeWinner.BATTLE_OUTCOME_WINNER_DRAW:
						pass
				
				in_battle = False
				os.kill(game_proc.pid, signal.SIGTERM)
			else:
				sleep(1)

def end_battle(winner: trainer, loser: trainer):
	global _trainerdb
	elo.calc_game_results(winner, loser)
	_trainerdb.serialize_json()
	write_battle_log(winner, loser)

def test():
	_trainerdb: trainer_database = trainer_database()
	_trainerdb.deserialize_json()
	
	_trainer: trainer = _trainerdb.random_trainer()

if (__name__ == "__main__"):
	main()