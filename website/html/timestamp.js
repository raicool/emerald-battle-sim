
output = document.getElementById("output" + document.currentScript.getAttribute("idx"));

// finding the difference in total seconds between two dates
second_diff = (Date.now() / 1000) - document.currentScript.getAttribute("last_match");

// showing the relative timestamp.
if (second_diff < 60) {
    output.innerHTML = Math.round(second_diff) + " seconds ago.";
} else if (second_diff < 3600) {
    output.innerHTML = Math.round(second_diff / 60) + " minutes ago.";
} else if (second_diff < 86400) {
    output.innerHTML = Math.round(second_diff / 3600) + " hours ago.";
} else if (second_diff < 2620800) {
    output.innerHTML = Math.round(second_diff / 86400) + " days ago.";
} else if (second_diff < 31449600) {
    output.innerHTML = Math.round(second_diff / 2620800) + " months ago.";
} else {
    output.innerHTML = "-";
}