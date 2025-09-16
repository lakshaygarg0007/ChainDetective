import requests
from typing import List, Dict

FBI_WANTED_FEED = "https://api.fbi.gov/wanted/v1/list"  # public feed (paginated)

def check_fbi_most_wanted(name: str) -> List[Dict]:
    """
    Search FBI Wanted feed for entries that match 'name' (case-insensitive).
    Returns a list of matching entries (possibly empty).
    """
    matches = []
    page = 1
    page_size = 20

    # fetch pages until none left or we find something reasonable
    while True:
        params = {"page": page, "pageSize": page_size}
        r = requests.get(FBI_WANTED_FEED, params=params, timeout=10)
        if r.status_code != 200:
            # fallback: return empty and log status
            print("FBI API error:", r.status_code, r.text[:300])
            return matches

        data = r.json()
        items = data.get("items") or data.get("results") or []
        if not items:
            break

        for it in items:
            # different fields may contain names; check title and aliases
            title = it.get("title", "")
            aliases = it.get("aliases", []) or it.get("subjects", [])
            combined = " ".join([title] + [str(a) for a in aliases])
            if name.lower() in combined.lower():
                matches.append(it)

        # stop if no next page
        if len(items) < page_size:
            break
        page += 1

        # safety: don't loop forever
        if page > 10:
            break

    return matches
