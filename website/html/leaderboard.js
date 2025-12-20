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

setInterval
(
	function()
	{
		read_file("trainers.json", function(file)
		{
			var data = JSON.parse(file);
			var player_count = len(data);

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
					row.children[1].innerHTML = value.rank;
				}

				if (value.hasOwnProperty("elo"))
				{
					row.children[12].innerHTML = Math.round(value.elo);
				}

				i++;
			}
			
			if (selected_header)
			{
				sort_table(table, false)
			}
		}
	)
	},
	1000 // 1 second interval
)