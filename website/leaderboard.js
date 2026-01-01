import { read_file, comparer, len, timestamp_diff } from "./utility.js";

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
}

function read_dump_data()
{
	read_file("trainers.json", function(file)
		{
			var data = JSON.parse(file);
			var change = false

			var table = document.getElementById("leaderboard");
			var i = 0;
			for (const [key, value] of Object.entries(data))
			{
				var row = document.getElementById("pidx" + i);

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
			
			if (selected_header && change)
			{
				sort_table(table, false)
			}
		}
	)

	read_file("summary.json", function(file)
		{
			var data = JSON.parse(file);

			var table = document.getElementById("battle-log")
			if (table)
			{
				var body = table.tBodies[0]
				
				body.innerHTML = ""

				for (const [key, value] of Object.entries(data).reverse())
				{
					var row = body.insertRow()
					var date = new Date(value.timestamp * 1000);
					add_cell_text(row, date.toLocaleTimeString())
					add_cell_text(row, value.left_name)
					add_cell_text(row, value.winner_side == 1 ? "W" : "L")
					add_cell_text(row, Math.round(value.left_elo_delta))
					add_cell_text(row, value.left_rank_delta)

					add_cell_text(row, value.right_name)
					add_cell_text(row, value.winner_side == 2 ? "W" : "L")
					add_cell_text(row, Math.round(value.right_elo_delta))
					add_cell_text(row, value.right_rank_delta)
				}
			}
		}
	)
}

read_dump_data()