from datetime import datetime
from enum import IntEnum
import utils
from pokemon import trainer, trainermon
import strings
from trainer_database import trainer_database

class __site_theme(IntEnum):
	DARK = 0
	LIGHT = 1

THEME: int = __site_theme.LIGHT
BOX_SPRITE_URL: str = "https://raw.githubusercontent.com/msikma/pokesprite/master/pokemon-gen7x/"
LEAGUE_SPRITE_URL: str = "https://raw.githubusercontent.com/msikma/pokesprite/master/items/ball/"

HTML_HEADER = f"""\
<!DOCTYPE html>
<html>
	<head>
		<meta name="viewport" content="width=device-width, initial-scale=1">
		<link rel="stylesheet" href="{"github-markdown-light.css" if THEME == __site_theme.LIGHT else "github-markdown.css"}">
		<link rel="stylesheet" href="pokesprite-docs.css">
        <script type="module" src="utility.js"></script>
		<style>
			.markdown-body {{
				box-sizing: border-box;
				min-width: 200px;
				max-width: 980px;
				margin: 0 auto;
				padding: 45px;
			}}

			@media (max-width: 767px) {{
				.markdown-body {{
					padding: 15px;
				}}
			}}
		</style>
	</head>
	<body style="margin:0px; padding:0px;">
		<div class="markdown-body" style="max-width:100%;">
"""


HTML_TRAILER = """\
		</div">
	</body>
</html>
"""
def __table_header_button(label: str, sort: bool = False) -> str:
	return str(
		f"<th{" class=\"order\"" if sort == True else ""}>"
			f"{label}"
		"</th>"
	)

def __table_data_trainer_name(_trainer: trainer):
	player_page: str = f"player.html?id={str(_trainer["id"])}"
	return str(
		"<td>"
			+f"<a href=\"{player_page}\">{_trainer["name"]}</a>"
		+"</td>"
	)

def __table_data_pokemon_boxsprite(party: list[str]) -> str:
	value: str = str()
	for mon_data in party:
		_pkmn: trainermon = utils.json2obj(mon_data)
		_mon_name: str = strings.pokemon[_pkmn.species].lower()

		value += f"<td class=image><img class=p src=\"{BOX_SPRITE_URL}{"shiny/" if _pkmn.shiny else "regular/"}{_mon_name}.png\"></td>"
	return value

def __table_body_trainerdata(_database: trainer_database) -> str:
	value: str = str()
	
	idx: int = 0
	for _trainer in _database.db.values():
		if (_trainer["wins"] + _trainer["losses"] > 0):
			wl_ratio: float = _trainer["wins"] / (_trainer["wins"] + _trainer["losses"]) * 100
			wl_ratio = round(wl_ratio, 3)
		else:
			wl_ratio: float = 0
		
		value += str(
			f"<tr id=\"pidx{idx}\" class=header>"
				+"<td style=\"width: 20%\">"
				+"</td>" 
				+f"<td>{_trainer.get("rank", "-")}</td>" # Rank
				+f"<td><img src=\"sprites/mugshot/{_trainer["trainer_pic"]}.png\" class=mugshot></td>" # Class
				+__table_data_trainer_name(_trainer) # Name
				+f"<td class=image><img class=p src=\"{LEAGUE_SPRITE_URL}{_trainer["league"]}.png\"></td>" # League
				+f"<td><code>{_trainer.get("id", "-")}</code></td>" # UUID
				+__table_data_pokemon_boxsprite(_trainer["party"]) # Party
				+f"<td>{int(_trainer.get("elo", -1))}</td>" # Points
				+f"<td>{_trainer.get("wins", "-")}</td>" # Wins
				+f"<td>{_trainer.get("losses", "-")}</td>" # Losses
				+f"<td>{wl_ratio}%</td>" # Win %
				+f"<td>{_trainer.get("battles", "-")}</td>" # Battles
			+"</tr>"
		)
		idx += 1
	return value

def update_html(_database: trainer_database):
	html: str = HTML_HEADER

	html += str(
		"<div>"
			+"<table class=\"pokesprite\" id=\"leaderboard\" style=\"table-layout: fixed;\">"
				+"<caption>"
					+"<header>"
    					+"Emerald Battle Simulator Leaderboard"
					+"</header>"
					+f"<i>as of {datetime.now()}</i>"
 				+"</caption>"
				+"<thead>"
					+"<tr>"
						+__table_header_button("Last Match", True)
						+__table_header_button("Rank", True)
						+__table_header_button("Class")
						+__table_header_button("Name", True)
						+__table_header_button("League")
						+__table_header_button("UUID", True)
						+__table_header_button("") # party mon 1
						+__table_header_button("") # party mon 2
						+__table_header_button("") # party mon 3
						+__table_header_button("") # party mon 4
						+__table_header_button("") # party mon 5
						+__table_header_button("") # party mon 6
						+__table_header_button("Points", True)
						+__table_header_button("Wins", True)
						+__table_header_button("Losses", True)
						+__table_header_button("Win %", True)
						+__table_header_button("Battles", True)
					+"</tr>"
				+"</thead>"
				+"<tbody>"
					+__table_body_trainerdata(_database)
				+"</tbody>"
			+"</table>"
			+"<script type=\"module\" src=\"leaderboard.js\"></script>"
		+"</div>"
	)

	html += HTML_TRAILER

	with open("website/html/leaderboard.html", "w+") as lb_file:
		lb_file.write(html)
		lb_file.close()

if (__name__ == "__main__"):
	__trainerdb: trainer_database = trainer_database()
	__trainerdb.deserialize_json()
	update_html(__trainerdb)