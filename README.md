# Lusophone Library

A personal catalogue of Lusophone literature — fiction, poetry, non-fiction, biography and music from Angola, Mozambique, Cape Verde, Brazil, São Tomé and beyond. Built from shelf photographs taken at **Librairie Portugaise et Brésilienne**, rue Tournefort, Paris.

## Pages

| File | Description |
|------|-------------|
| `index.html` | Browsable catalogue — search, filter by section/genre/access, expand cards for details and buy links |
| `about.html` | Methodology — how the catalogue was built from ~20 shelf photos |
| `suggest.html` | Contribution form — links to GitHub Issues and Bluesky |

## Data

| File | Description |
|------|-------------|
| `data.json` | All 200 catalogue entries as a JSON array. Keys: `s` (section), `t` (title), `a` (author), `c` (country), `y` (year), `g` (genre), `bl` (blurb), `en` (English translation), `aw` (award), `editions` (ISBNs by language), `buy` (retailer keys) |
| `isbn_lookup.py` | Python script that queries the Open Library API to find ISBNs for catalogue entries |
| `editions_results.json` | Output from `isbn_lookup.py` — raw ISBN data returned by Open Library |

## Running locally

The catalogue loads `data.json` via `fetch()`, so it needs a local server:

```bash
cd "Lusophone Library"
python3 -m http.server
# then open http://localhost:8000
```

## isbn_lookup.py

Reads `data.json`, queries the [Open Library API](https://openlibrary.org/dev/docs/api) for each title, and writes found editions and ISBNs to `editions_results.json`.

```bash
python3 isbn_lookup.py
```
