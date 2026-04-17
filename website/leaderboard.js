import { read_file, comparer, timestamp_diff } from "./utility.js";
import { pokemon, move_name, item, nature, ability } from "./constants.js";

const BOX_SPRITE_URL = "https://raw.githubusercontent.com/msikma/pokesprite/master/pokemon-gen7x/"
const LEAGUE_SPRITE_URL = "https://raw.githubusercontent.com/msikma/pokesprite/master/items/ball/"

var selected_header

document.querySelectorAll('th').forEach(th => th.addEventListener('click', (() => 
{
	selected_header = th;
	const table = th.closest('table');
	sort_table(table);
})));

var tooltip = document.createElement("div")
tooltip.setAttribute("style", "padding: 8px; min-width: 256px; min-height: 256px; position: fixed; background-color: rgba(70, 72, 77, 0.78); color: rgb(255, 255, 255); font-size: 16px; font-family: consolas,monospace")
document.body.appendChild(tooltip)

const move = (e) => 
{
    var x = e.pageX
    var y = e.pageY;
    //set left and top of div based on mouse position
    tooltip.style.left = x + "px";
    tooltip.style.top = (y + 16) + "px";
};

document.addEventListener("mousemove", (e) => 
{
    move(e);
});


function sort_table(table, switch_mode = true)
{
	const tbody = table.querySelector('tbody');
	Array.from(tbody.querySelectorAll('tr'))
		.sort(comparer(Array.from(selected_header.parentNode.children).indexOf(selected_header), switch_mode ? comparer.asc = !comparer.asc : comparer.asc))
		.forEach(tr => tbody.appendChild(tr));
}

setInterval(read_dump_data, 5000) // 5 second interval

function add_cell_text(row, text, sort_val = text)
{
	// Append a text node to the cell
	const [node, ] = add_cell_element(row, "a", sort_val)

    node.innerHTML = text

    return node;
}

function add_cell_image(row, src, _class, sort_val = null)
{
	// Append a text node to the cell
	const [img, ] = add_cell_element(row, "img", sort_val)

    img.setAttribute("src", src);
    img.setAttribute("class", _class);
    
    return img;
}

function add_cell_element(row, element_tag, sort_val = null)
{
	const cell = row.insertCell();

	// Append a text node to the cell
	const e = document.createElement(element_tag);

    if (sort_val != null)
    {
        cell.setAttribute("sort_val", sort_val);
    }

	cell.appendChild(e);
    return [e, cell];
}

function add_pkmn_image(row, src, pkmn_data, sort_val = null)
{
    const [img, cell] = add_cell_element(row, "img", sort_val);

    img.setAttribute("class", "p");
    img.setAttribute("src", src)
    cell.setAttribute("class", "image");

    img.onmouseover = function() 
    { 
        tooltip.style.visibility = "visible"
        tooltip.innerHTML = 
        "<pre>"+
            `${pokemon[pkmn_data.species]} Level: ${pkmn_data.level}\n`+
            `Shiny: ${pkmn_data.shiny ? "Yes" : "No"}\n`+
            `Item: ${item[pkmn_data.item + 3]}\n`+
            `Ability: ${ability[pkmn_data.ability]}\n`+
            `Nature: ${nature[pkmn_data.nature]}\n`+
            "Moves:\n"+
            `    ${move_name[pkmn_data.moves[0]]}\n`+
            `    ${move_name[pkmn_data.moves[1]]}\n`+
            `    ${move_name[pkmn_data.moves[2]]}\n`+
            `    ${move_name[pkmn_data.moves[3]]}`+
        "</pre>"
    }

    img.onmouseout = function() 
    { 
        tooltip.style.visibility = "hidden"
        tooltip.innerHTML = ""
    }

    return img;
}

function read_dump_data()
{
	read_file("../dump/trainers.json", function(file)
		{
			var data = JSON.parse(file);

			var table = document.getElementById("leaderboard");

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

	read_file("../dump/summary.json", function(file)
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

        add_cell_text(row, timestamp_diff(value.last_match), value.last_match);

        add_cell_text(row, value.rank);

        var trainer_img = add_cell_image(row, `sprites/mugshot/${value.trainer_pic}.png`, "mugshot", value.trainer_class);
        trainer_img.setAttribute("class", "mugshot");

        var [trainer_name, ] = add_cell_element(row, "a");
        trainer_name.innerHTML = value.name;
        trainer_name.setAttribute("href", `player.html?id=${value.id}`)

        add_cell_image(row, LEAGUE_SPRITE_URL + `${value.league}.png`);

        var [tid, ] = add_cell_element(row, "code");
        tid.innerHTML = value.id;
        tid.setAttribute("class", "code");

        const party = value.party;
        for (const pkmn of party)
        {
            add_pkmn_image(
                row, 
                `${BOX_SPRITE_URL}${pkmn.shiny ? "shiny/" : "regular/"}${pokemon[pkmn.species].toLowerCase()}.png`,
                pkmn
            );
        }

        add_cell_text(row, Math.round(value.elo));
        const wl_ratio = value.wins / (value.wins + value.losses);
        add_cell_text(row, value.wins);
        add_cell_text(row, value.losses);
        add_cell_text(row, Math.round(100 * wl_ratio) + "%");
        add_cell_text(row, value.battles);
        add_cell_text(row, value.win_streak);

        i++;
    }
    ready = true;
}

read_dump_data();