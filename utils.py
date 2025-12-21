from collections import namedtuple
import json
import os

from res import charmap

def load_json(path: str, mode: str = "w+") -> dict:
	with open(path, mode, encoding='utf-8') as f:
		if (os.stat(path).st_size > 0):
			return json.load(f)
		else:
			return {}
	
def _json_object_hook(d): return namedtuple('trainermon', d.keys())(*d.values())
def json2obj(data): return json.loads(data, object_hook=_json_object_hook)

# returns -1 if not found
def to_charmap_index(char: int) -> int:
	for character in charmap.map.items():
		if character[0] == ord(char):
			return character[1]
	return -1