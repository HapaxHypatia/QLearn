from bs4 import BeautifulSoup
import cssutils


def update_styles(html, replacements):
  for old, new in replacements.items():
    html = html.replace(old, new)
  return html


def inline_css(html, css):
    soup = BeautifulSoup(html, "html.parser")
    sheet = cssutils.parseString(css)

    for rule in sheet:
        if rule.type == rule.STYLE_RULE:
            for element in soup.select(rule.selectorText):
                element["style"] = (element.get("style","") + ";" + rule.style.cssText)
    return str(soup)
