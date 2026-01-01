const get_cell_value = (tr, idx) => tr.children[idx].innerText || tr.children[idx].textContent;

export const comparer = (idx, asc) => (a, b) => ((v1, v2) => 
	v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2) ? v1 - v2 : v1.toString().localeCompare(v2)
	)(get_cell_value(asc ? a : b, idx), get_cell_value(asc ? b : a, idx));

export function read_file(file, callback) 
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

export function len(obj) 
{
    var size = 0, key;
    for (key in obj)
    {
        if (obj.hasOwnProperty(key)) size++;
    }
    return size;
};

// returns a string comparison between the given timestamp with the current time
export function timestamp_diff(timestamp_unix)
{
    var second_diff = (Date.now() / 1000) - timestamp_unix;

    if (second_diff < 60) 
    {
        return Math.round(second_diff) + " seconds ago";
    } 
    else if (second_diff < 3600) 
    {
        return Math.round(second_diff / 60) + " minutes ago";
    } 
    else if (second_diff < 86400) 
    {
        return Math.round(second_diff / 3600) + " hours ago";
    } 
    else if (second_diff < 2620800) 
    {
        return Math.round(second_diff / 86400) + " days ago";
    } 
    else if (second_diff < 31449600) 
    {
        return Math.round(second_diff / 2620800) + " months ago";
    } 
    else 
    {
        return "-";
    }
}