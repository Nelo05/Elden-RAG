import re
from typing import Optional

import mwparserfromhell
import requests
from langchain_core.documents import Document


class MediaWikiLoader:

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def load(self, url: str) -> list[Document]:
        api_url, title = self._parse_url(url)

        if title.lower().startswith("категория:"):
            category = title[len("категория:") :].strip()
            return self._load_category(
                category=category,
                api_url=api_url,
            )

        document = self._load_page(
            title=title,
            api_url=api_url,
        )

        return [document] if document else []

    def _load_page(
        self,
        title: str,
        api_url: str,
    ) -> Optional[Document]:

        page = self._get_wikitext(
            title=title,
            api_url=api_url,
        )

        if page is None:
            return None

        text = self._clean(
            text=page["text"],
            title=page["title"],
        )

        if not text.strip():
            return None

        return Document(
            page_content=text,
            metadata={
                "title": page["title"],
                "source": self._get_page_url(
                    api_url=api_url,
                    title=page["title"],
                ),
            },
        )

    def _load_category(
        self,
        category: str,
        api_url: str,
    ) -> list[Document]:

        titles = self._get_category_members(
            category=category,
            api_url=api_url,
        )

        documents = []

        for title in titles:
            document = self._load_page(
                title=title,
                api_url=api_url,
            )

            if document is not None:
                document.metadata["category"] = category
                documents.append(document)

        return documents

    def _parse_url(self, url: str) -> tuple[str, str]:

        url = url.rstrip("/")

        if "/wiki/" not in url:
            raise ValueError(f"Unsupported MediaWiki URL: {url}")

        base_url, title = url.split("/wiki/", maxsplit=1)

        title = title.replace("_", " ")
        api_url = f"{base_url}/api.php"

        return api_url, title

    def _fetch_api(
        self,
        api_url: str,
        params: dict,
    ) -> dict:

        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            **params,
        }

        response = requests.get(
            api_url,
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()

        data = response.json()

        if "error" in data:
            raise RuntimeError(f"MediaWiki API error: {data['error']['info']}")

        return data

    def _get_wikitext(
        self,
        title: str,
        api_url: str,
    ) -> Optional[dict[str, str]]:

        data = self._fetch_api(
            api_url=api_url,
            params={
                "prop": "revisions",
                "rvprop": "content",
                "titles": title,
            },
        )

        pages = data.get("query", {}).get("pages", [])

        if not pages:
            return None

        page = pages[0]
        revisions = page.get("revisions", [])

        if not revisions:
            return None

        return {
            "title": page["title"],
            "text": revisions[0]["content"],
        }

    def _get_category_members(
        self,
        category: str,
        api_url: str,
    ) -> list[str]:

        members = []
        continue_token = None

        while True:
            params = {
                "list": "categorymembers",
                "cmtitle": f"Category:{category}",
                "cmlimit": "max",
            }

            if continue_token:
                params["cmcontinue"] = continue_token

            data = self._fetch_api(
                api_url=api_url,
                params=params,
            )

            for page in data.get("query", {}).get("categorymembers", []):
                if page["ns"] == 0:
                    members.append(page["title"])

            continue_token = data.get("continue", {}).get("cmcontinue")

            if not continue_token:
                break

        return members

    def _get_page_url(
        self,
        api_url: str,
        title: str,
    ) -> str:

        base_url = api_url.removesuffix("/api.php")

        return f"{base_url}/wiki/{title.replace(' ', '_')}"

    def _clean(
        cls,
        text: str,
        title: str,
    ) -> str:

        def has_image_extension(filename: str) -> bool:
            return bool(
                re.search(
                    r"\.(jpg|jpeg|png|gif|bmp|webp|svg|tiff?|ico|avif)",
                    filename,
                    re.IGNORECASE,
                )
            )

        text = re.split(
            r"^==\s*(?:Галерея|Видео)\s*==\s*$",
            text,
            maxsplit=1,
            flags=re.MULTILINE | re.IGNORECASE,
        )[0]

        text = re.sub(
            r"\{\{\s*PAGENAME\s*\}\}",
            title,
            text,
            flags=re.IGNORECASE,
        )
        parsed_text = mwparserfromhell.parse(text)

        for tag in parsed_text.filter_tags():
            tag.wiki_markup = None

        for wikilink in parsed_text.filter_wikilinks()[::-1]:
            original = str(wikilink)
            inner = original[2:-2]
            parts = inner.split("|")

            if len(parts) == 1:
                replacement = parts[0]
            elif len(parts) == 2 and not parts[0].lower().startswith(
                ("файл:", "file:")
            ):
                replacement = parts[1]
            else:
                replacement = ""

            parsed_text.replace(wikilink, replacement)

        for external_link in parsed_text.filter_external_links()[::-1]:
            replacement = ""

            if external_link.title and "ссылка на" not in str(external_link.title):
                replacement = str(external_link.title)

            parsed_text.replace(
                external_link,
                replacement,
            )

        for template in parsed_text.filter_templates()[::-1]:
            if any(str(param.name).strip().lower() == "t" for param in template.params):
                t_value = " "
                values = []
                for param in template.params:
                    key = str(param.name).strip()
                    value = str(param.value).strip()
                    if key.lower() == "t":
                        t_value = value
                    values.append(value)
                replacement = f"## {t_value}\n\n" + "\n\n".join(values)
                parsed_text.replace(
                    template,
                    replacement,
                )
                continue

            pairs = []
            for param in template.params:
                if not param.showkey:
                    continue
                key = str(param.name).strip()
                value = str(param.value).strip()
                if value not in ("", ".") and not has_image_extension(value):
                    pairs.append(f"{key}: {value}")
            parsed_text.replace(
                template,
                "\n".join(pairs) + "\n\n" if pairs else "",
            )

        text = str(parsed_text)
        text = re.sub(
            r"<br\s*/?s*>",
            "\n",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"(<li/>)+",
            lambda m: ("  " * (m.group(0).count("<li/>") - 1) + "- "),
            text,
        )

        text = re.sub(r"<[^>]+>", "", text)

        text = re.sub(
            r"^(={2,6})(.*?)\1\s*$",
            lambda m: ("#" * len(m.group(1)) + " " + m.group(2).strip()),
            text,
            flags=re.MULTILINE,
        )

        text = text.replace("[]", "")
        text = text.replace("\xa0", " ")
        text = "## Карточка страницы\n\n" + text
        text = text.replace("|-|", "")

        text = re.sub(
            r"(?<![=])=(?=\n|$)",
            "\n\n",
            text,
        )
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text
