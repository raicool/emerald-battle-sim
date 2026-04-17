const r_page_theme = document.getElementById("page-theme")

const MARKDOWN_THEME_LIGHT = "github-markdown-light.css"
const MARKDOWN_THEME_DARK = "github-markdown.css"

if (r_page_theme.nodeName == "LINK")
{
	r_page_theme.setAttribute("href", MARKDOWN_THEME_DARK)
}