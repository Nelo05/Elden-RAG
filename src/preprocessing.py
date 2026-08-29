import re

URL_LINK_PATTERN = re.compile(r"\[?\[(https?://[^\s]+)\s+([^\]]+)\]\]?")

WIKI_LINK_WITH_TEXT_PATTERN = re.compile(r"\[\[([^|\]]*)\|([^\]]*)\]\]")

WIKI_LINK_PATTERN = re.compile(r"\[\[([^\]]*)\]\]")

HEADER_PATTERN = re.compile(
    r"^(=+)(.+?)\1$",
    flags=re.MULTILINE,
)

LIST_PATTERN = re.compile(
    r"^(\*+)\s*(.*)",
    flags=re.MULTILINE,
)

QUOTE_TEMPLATE_PATTERN = re.compile(
    r"\{\{Цитата.*?\}\}",
    flags=re.DOTALL,
)

ENEMY_TEMPLATE_PATTERN = re.compile(
    r"\{\{Враг.*?\}\}",
    flags=re.DOTALL,
)

ITEMS_TEMPLATE_PATTERN = re.compile(
    r"\|\s*Предметы(?:\d+)?\s*=\s*([^|}]+)",
    flags=re.DOTALL,
)

RESISTANCES_TEMPLATE_PATTERN = re.compile(
    r"\{\{Сопротивления\d?\|([^}]*)\}\}",
    flags=re.DOTALL,
)

DIALOGUES_TEMPLATE_PATTERN = re.compile(
    r"\{\{Диалоги[^}]*?1=([^}]*)\}\}",
    flags=re.DOTALL,
)

REMOVE_PATTERN = re.compile(r"без\|мини\|[^\n]*\n?")

TABLE_PATTERN = re.compile(
    r"\{\| class=\"wikitable\".*?\|\}",
    flags=re.DOTALL,
)

ITEMS_TABLE_ROW_PATTERN = re.compile(
    r"\|-\s*\n"
    r"\|\s*.*?\s*\n"
    r'\|\s*style="[^"]*"\s*\|(.*?)\s*\n'
    r'\|\s*style="[^"]*"\s*\|(.*?)(?=\s*\n\|-|\s*\n\|\})',
    flags=re.DOTALL,
)


def replace_pagename(text: str, title: str) -> str:

    return re.sub(r"{{PAGENAME}}", title, text)


def remove_unwanted_sections(text: str) -> str:

    return text.split("==Галерея==")[0].split("==Видео==")[0]


def clean_html(text: str) -> str:

    text = re.sub(r"<br>", ", ", text)

    return re.sub(r"<[^>]*>", "", text)


def convert_links(text: str) -> str:
    def replace_url(match: re.Match) -> str:
        link_text = match.group(2)
        if "ссылка на" in link_text:
            return ""
        return link_text

    text = URL_LINK_PATTERN.sub(replace_url, text)
    text = WIKI_LINK_WITH_TEXT_PATTERN.sub(r"\2", text)
    text = WIKI_LINK_PATTERN.sub(r"\1", text)
    return text


def convert_to_markdown(text: str) -> str:

    def replace_header(m):

        level = len(m.group(1))

        return f"{'#' * level} {m.group(2).strip()}"

    text = HEADER_PATTERN.sub(replace_header, text)

    def replace_list(m):

        stars = m.group(1)
        indent = "  " * (len(stars) - 1)

        return f"{indent}- {m.group(2)}"

    text = LIST_PATTERN.sub(replace_list, text)

    return text


def replace_enemy_template(match: re.Match) -> str:
    inner = match.group(0)
    m = ITEMS_TEMPLATE_PATTERN.search(inner)
    if not m:
        return "## Краткая информация\n"
    raw = m.group(1).strip()
    items = re.split(r"[,\n]+", raw)
    items = [it.strip() for it in items if it.strip()]
    items = [it for it in items if not it.endswith(":")]
    if not items:
        return "## Краткая информация\n"
    return "## Предметы\n" + "; ".join(items) + "\n\n## Краткая информация\n"


def replace_resistances(match: re.Match) -> str:
    content = match.group(1)
    pairs = content.split("|")
    return ", ".join(pairs)


def replace_dialogues(match: re.Match) -> str:
    content = match.group(1).strip()
    return "## Диалоги\n" + content


def replace_items_table(match: re.Match) -> str:
    table_content = match.group(0)
    rows = ITEMS_TABLE_ROW_PATTERN.findall(table_content)
    if not rows:
        return ""
    result_lines = []
    for title, chance in rows:
        result_lines.append(f"- {title.strip()} - Шанс выпадения: {chance.strip()}")
    return "\n".join(result_lines)


def convert_templates(text: str) -> str:
    text = re.sub(r"'{2,}", "", text)
    text = REMOVE_PATTERN.sub("", text)
    text = QUOTE_TEMPLATE_PATTERN.sub("", text)
    text = ENEMY_TEMPLATE_PATTERN.sub(replace_enemy_template, text)
    text = RESISTANCES_TEMPLATE_PATTERN.sub(replace_resistances, text)
    text = DIALOGUES_TEMPLATE_PATTERN.sub(replace_dialogues, text)
    text = TABLE_PATTERN.sub(replace_items_table, text)

    return text


def preprocess_text(text: str, title: str) -> str:

    text = replace_pagename(text, title)
    text = remove_unwanted_sections(text)
    text = clean_html(text)
    text = convert_links(text)
    text = convert_templates(text)
    text = convert_to_markdown(text)

    return text
