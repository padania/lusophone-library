#!/usr/bin/env python3
"""
Lusophone Library — full editions lookup
Queries Open Library Works/Editions API to retrieve ALL editions of each book.

Usage:
    python3 isbn_lookup.py

Reads: data.json (in same folder as this script)
Output: editions_results.json (in same folder as this script)
"""

import json, time, urllib.request, urllib.parse, re, os, sys
from difflib import SequenceMatcher

# ── Load books from data.json ─────────────────────────────────────────────────
def load_books():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, "data.json")
    if not os.path.exists(path):
        print(f"ERROR: Could not find data.json at {path}")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} books from data.json")
    return data

# ── Language normalisation ────────────────────────────────────────────────────
LANG_MAP = {
    "por":"pt","portuguese":"pt","eng":"en","english":"en",
    "fre":"fr","french":"fr","fra":"fr","ger":"de","german":"de","deu":"de",
    "spa":"es","spanish":"es","ita":"it","italian":"it",
    "dut":"nl","dutch":"nl","nld":"nl","swe":"sv","swedish":"sv",
    "nor":"no","norwegian":"no","fin":"fi","finnish":"fi",
    "pol":"pl","polish":"pl","cat":"ca","catalan":"ca",
    "jpn":"ja","japanese":"ja","chi":"zh","chinese":"zh","zho":"zh",
    "kor":"ko","korean":"ko","ara":"ar","arabic":"ar",
    "heb":"he","hebrew":"he","rus":"ru","russian":"ru",
    "tur":"tr","turkish":"tr","gre":"el","greek":"el",
    "hrv":"hr","croatian":"hr","rum":"ro","romanian":"ro",
    "bul":"bg","bulgarian":"bg","cze":"cs","czech":"cs",
    "hun":"hu","hungarian":"hu","dan":"da","danish":"da",
}

def norm_lang(raw):
    if not raw: return "??"
    raw = raw.strip().lower().split("/")[-1]
    return LANG_MAP.get(raw, raw[:2] if len(raw) >= 2 else "??")

def sim(a, b):
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

def fetch_json(url, timeout=12):
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "LusophoneLibrary/2.0 (catalogue research)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception:
        return None

def find_work(title, author, year=None):
    params = {
        "title": title, "author": author, "limit": 5,
        "fields": "key,title,author_name,first_publish_year"
    }
    url = "https://openlibrary.org/search.json?" + urllib.parse.urlencode(params)
    data = fetch_json(url)
    if not data or not data.get("docs"):
        return None
    best, best_score = None, 0.0
    for doc in data["docs"]:
        t_sim = sim(title, doc.get("title", ""))
        a_sim = max((sim(author, a) for a in (doc.get("author_name") or [])), default=0)
        score = t_sim * 0.6 + a_sim * 0.4
        if year and doc.get("first_publish_year"):
            if abs(doc["first_publish_year"] - year) <= 5:
                score += 0.05
        if score > best_score:
            best_score, best = score, doc
    return best.get("key") if best_score >= 0.45 else None

def fetch_editions(work_key, limit=300):
    url = (f"https://openlibrary.org{work_key}/editions.json"
           f"?fields=isbn_13,isbn_10,publishers,publish_date,languages,by_statement&limit={limit}")
    data = fetch_json(url)
    if not data:
        return []
    editions = []
    for entry in data.get("entries", []):
        isbns = entry.get("isbn_13", []) + entry.get("isbn_10", [])
        if not isbns:
            continue
        langs = entry.get("languages", [])
        if langs:
            raw = langs[0].get("key", "") if isinstance(langs[0], dict) else str(langs[0])
            lang = norm_lang(raw)
        else:
            lang = "??"
        date_str = entry.get("publish_date", "")
        year_m = re.search(r"\b(19|20)\d{2}\b", date_str)
        year = int(year_m.group(0)) if year_m else None
        pubs = entry.get("publishers", [])
        pub = pubs[0] if pubs else None
        by = entry.get("by_statement", "")
        tr_m = re.search(r"translated?\s+by\s+([^;,.]+)", by, re.I)
        tr = tr_m.group(1).strip() if tr_m else None
        ed = {"isbn": isbns[0], "all_isbns": list(set(isbns)), "lang": lang}
        if year: ed["year"] = year
        if pub:  ed["pub"]  = pub
        if tr:   ed["tr"]   = tr
        editions.append(ed)
    return editions

def group_editions(editions):
    grouped = {}
    for ed in editions:
        grouped.setdefault(ed["lang"], []).append(ed)
    for lang in grouped:
        grouped[lang].sort(key=lambda e: e.get("year") or 0, reverse=True)
    return grouped

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    books       = load_books()
    results_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "editions_results.json")

    # Resume if interrupted
    if os.path.exists(results_file):
        with open(results_file) as f:
            results = json.load(f)
        already = len(results)
        print(f"Resuming — {already} already done, {len(books) - already} remaining")
    else:
        results = {}

    done = found = 0

    for i, b in enumerate(books):
        key = f"{b['t']}|{b['a']}"
        if key in results:
            if results[key].get("editions"):
                found += 1
            continue

        print(f"[{i+1:3}/{len(books)}] {b['t'][:46]:<46} {b['a'][:20]:<20}", end=" ", flush=True)

        work_key = find_work(b["t"], b["a"], b.get("y"))
        time.sleep(0.5)

        if not work_key:
            results[key] = {"ol_work_id": None, "editions": {}, "total_editions": 0}
            print("— not found")
        else:
            eds_list = fetch_editions(work_key)
            time.sleep(0.6)
            grouped  = group_editions(eds_list)
            total    = len(eds_list)
            results[key] = {"ol_work_id": work_key, "editions": grouped, "total_editions": total}
            lang_summary = "  ".join(
                f"{lg}:{len(arr)}" for lg, arr in sorted(grouped.items()) if lg != "??"
            )
            print(f"→ {total:3} editions  {lang_summary}")
            if total > 0:
                found += 1

        done += 1
        if done % 10 == 0:
            with open(results_file, "w") as f:
                json.dump(results, f, ensure_ascii=False)

    with open(results_file, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    total = len(results)
    pct   = 100 * found // total if total else 0
    print(f"\n{'─'*60}")
    print(f"Complete: {total} books  |  works found: {found} ({pct}%)")
    print(f"Results saved to: {results_file}")
    print(f"\nSend editions_results.json back and the catalogue will be")
    print(f"patched with all editions data.")

if __name__ == "__main__":
    main()
