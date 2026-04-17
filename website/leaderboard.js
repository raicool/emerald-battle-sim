import { read_file, comparer, pokemon, timestamp_diff } from "./utility.js";

const BOX_SPRITE_URL = "https://raw.githubusercontent.com/msikma/pokesprite/master/pokemon-gen7x/"
const LEAGUE_SPRITE_URL = "https://raw.githubusercontent.com/msikma/pokesprite/master/items/ball/"

var selected_header

document.querySelectorAll('th').forEach(th => th.addEventListener('click', (() => 
{
	selected_header = th;
	const table = th.closest('table');
	sort_table(table);
})));


function sort_table(table, switch_mode = true)
{
	const tbody = table.querySelector('tbody');
	Array.from(tbody.querySelectorAll('tr'))
		.sort(comparer(Array.from(selected_header.parentNode.children).indexOf(selected_header), switch_mode ? comparer.asc = !comparer.asc : comparer.asc))
		.forEach(tr => tbody.appendChild(tr));
}

setInterval(read_dump_data, 5000) // 5 second interval

function add_cell_text(row, text)
{
	const cell = row.insertCell();

	// Append a text node to the cell
	const node = document.createTextNode(text);
	cell.appendChild(node);
    return node;
}

function add_cell_image(row, src, _class)
{
	const cell = row.insertCell();

	// Append a text node to the cell
	const img = document.createElement("img");
    img.setAttribute("src", src);
    img.setAttribute("class", _class);
	cell.appendChild(img);
    return img;
}

function add_cell_element(row, element_tag)
{
	const cell = row.insertCell();

	// Append a text node to the cell
	const e = document.createElement(element_tag);
	cell.appendChild(e);
    return e;
}

function read_dump_data()
{
	read_file("trainers.json", function(file)
		{
			var data = JSON.parse(file);

			var table = document.getElementById("leaderboard");

			var i = 0;
            if (ready)
            {
                update_trainer_rows(data)
            }
            else
            {
                setup_trainer_rows(table, data)
            }
			
			if (selected_header)
			{
				sort_table(table, false);
			}
		}
	)

	read_file("summary.json", function(file)
		{
			var data = JSON.parse(file);

			var table = document.getElementById("battle-log");
			if (table)
			{
				var body = table.tBodies[0];
				
				body.innerHTML = "";

				for (const [, value] of Object.entries(data).reverse())
				{
					var row = body.insertRow();
					var date = new Date(value.timestamp * 1000);
					add_cell_text(row, date.toLocaleTimeString());
					add_cell_text(row, value.left_name);
					add_cell_text(row, value.winner_side == 1 ? "W" : "L");
					add_cell_text(row, `${Math.round(value.left_elo_final)} (${Math.round(value.left_elo_delta)})`);
					add_cell_text(row, value.left_rank_delta);

					add_cell_text(row, value.right_name);
					add_cell_text(row, value.winner_side == 2 ? "W" : "L");
					add_cell_text(row, `${Math.round(value.right_elo_final)} (${Math.round(value.right_elo_delta)})`);
					add_cell_text(row, value.right_rank_delta);
				}
			}
		}
	)
}

function update_trainer_rows(data)
{
    var i = 0;
    for (const [key, value] of Object.entries(data))
    {
        const row = document.getElementById("pidx" + i);
        if (value.hasOwnProperty("last_match"))
        {
            row.children[0].innerHTML = timestamp_diff(value.last_match)
        }

        if (value.hasOwnProperty("rank"))
        {
            if (row.children[1].innerHTML != value.rank)
            {
                row.children[1].innerHTML = value.rank;
                change = true
            }
        }

        if (value.hasOwnProperty("elo"))
        {
            row.children[12].innerHTML = Math.round(value.elo);
        }

        i++;
    }
}

var ready = false;
function setup_trainer_rows(table, data)
{
    var body = table.tBodies[0];
	body.innerHTML = "";

    var i = 0;
    for (const [, value] of Object.entries(data))
    {
        var row = body.insertRow();
        row.id = "pidx" + i;

        add_cell_text(row, timestamp_diff(value.last_match));

        add_cell_text(row, value.rank);

        var trainer_img = add_cell_image(row, `sprites/mugshot/${value.trainer_pic}.png`, "mugshot");
        trainer_img.setAttribute("class", "mugshot");

        var trainer_name = add_cell_element(row, "a");
        trainer_name.innerHTML = value.name;
        trainer_name.setAttribute("href", `player.html?id=${value.id}`)

        add_cell_image(row, LEAGUE_SPRITE_URL + `${value.league}.png`);

        var tid = add_cell_element(row, "code");
        tid.innerHTML = value.id;
        tid.setAttribute("class", "code");

        const party = value.party;
        for (const pkmn of party)
        {
            var img = add_cell_image(
                row, 
                `${BOX_SPRITE_URL}${pkmn.shiny ? "shiny/" : "regular/"}${pokemon[pkmn.species].toLowerCase()}.png`
            );
            img.setAttribute("class", "p");
            img.parentNode.setAttribute("class", "image");
        }

        add_cell_text(row, Math.round(value.elo));
        const wl_ratio = value.wins / (value.wins + value.losses);
        add_cell_text(row, value.wins);
        add_cell_text(row, value.losses);
        add_cell_text(row, Math.round(100 * wl_ratio) + "%");
        add_cell_text(row, value.battles);

        i++;
    }
    ready = true;
}

read_dump_data();