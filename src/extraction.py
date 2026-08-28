from typing import Optional

import requests


def _fetch_api(url: str, params: dict) -> dict:

    full_params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        **params,
    }
    resp = requests.get(url, params=full_params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"MediaWiki API error: {data['error']['info']}")
    return data


def get_wikitext(title: str, url: str) -> Optional[dict[str, str]]:

    params = {
        "prop": "revisions",
        "rvprop": "content",
        "titles": title,
    }
    data = _fetch_api(url, params)
    pages = data.get("query", {}).get("pages", [])

    if not pages or "missing" in pages[0]:
        print(f"Page '{title}' not found.")
        return None

    page = pages[0]
    return {
        "title": page["title"],
        "text": page["revisions"][0]["content"],
    }


def get_category_members(category: str, url: str) -> list[str]:

    all_members = []
    continue_token = None
    while True:
        params = {
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": "max",
        }
        if continue_token:
            params["cmcontinue"] = continue_token

        data = _fetch_api(url, params)
        members = data.get("query", {}).get("categorymembers", [])

        if not members:
            break

        for page in members:
            if page["ns"] == 0:
                all_members.append(page["title"].replace(" ", "_"))

        continue_token = data.get("continue", {}).get("cmcontinue")
        if not continue_token:
            break

    return all_members
