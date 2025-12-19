function get_url_param(sParam)
{
	var sPageURL = window.location.search.substring(1);
	var sURLVariables = sPageURL.split('&');
	for (var i = 0; i < sURLVariables.length; i++) 
	{
		var sParameterName = sURLVariables[i].split('=');
		if (sParameterName[0] == sParam) 
		{
			return sParameterName[1];
		}
	}
}

function read_file(file, callback) 
{
	var rawFile = new XMLHttpRequest();

	rawFile.overrideMimeType("application/json");
	rawFile.open("GET", file, true);
	rawFile.onreadystatechange = function() 
	{
		if (rawFile.readyState === 4 && rawFile.status == 200) 
		{
			callback(rawFile.responseText);
		}
	}
	rawFile.send(null);
}

var player_id = get_url_param("id");
var player_count = 0;

Object.size = function(obj) 
{
	var size = 0, key;
	for (key in obj)
	{
		if (obj.hasOwnProperty(key)) size++;
	}
	return size;
};

read_file("trainers.json", function(file)
{
	var data = JSON.parse(file);
	player_count = Object.size(data);
	
	for (const [key, value] of Object.entries(data))
	{
		if (value.hasOwnProperty("id"))
		{
			if (value.id == player_id)
			{
				set_data(value);
				return;
			}
		}
	}
});

function set_data(data)
{
	var trainer_class = document.getElementById("trainer-class");
	var trainer_name = document.getElementById("trainer-name");
	var trainer_points = document.getElementById("trainer-points");
	var trainer_rank = document.getElementById("trainer-rank");
	var trainer_wins = document.getElementById("trainer-wins");
	var trainer_losses = document.getElementById("trainer-losses");

	trainer_class.src = "sprites/" + data.trainer_pic + ".png";
	trainer_name.innerHTML = data.name;
	trainer_points.innerHTML = data.elo;
	trainer_rank.innerHTML = data.rank + " / " + player_count;
	trainer_wins.innerHTML = data.wins;
	trainer_losses.innerHTML = data.losses;
	trainer_class.scale = 4;
}
