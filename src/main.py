import time
import logging
import requests
import pyodbc
from bs4 import BeautifulSoup, Comment
from geopy.geocoders import Nominatim
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

from prompts import (chain_league, parser_league, 
    chain_club, parser_club,
    chain_ClubWebsite, parser_ClubWebsite, 
    chain_ClubOfficialAndContact, parser_ClubOfficialAndContact)

from sql_queries import (
    insert_league_with_divisions, add_location_and_club,
    add_club_details, add_movement_and_division_club
)

# Shared models
from prompts import League, Division, ClubWebsite, Club, ClubOfficialAndContact, SocialMedia, Location, ContactInfo

# ——— HTTP Session & Rate‐Limit ———
session = requests.Session()

def fetch_wikipedia_page(url):
    try:
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        logger.info(f"Fetched {url}")
        return BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None

def clean_wikipedia_page(soup):
    content = soup.find('div', id='mw-content-text')
    if not content:
        return None, None
    pieces = []
    for el in content.descendants:
        if el.name=='a' and el.has_attr('href'):
            t = el.get_text(strip=True)
            h = el['href']
            if t:
                pieces.append(f"{t} ({h})")
        elif el.string and el.string.strip():
            pieces.append(el.string.strip())
    title = soup.find('h1').get_text(strip=True)
    return title, "\n".join(pieces)

# ——— LangChain wrapper ———
def run_chain(chain, parser, payload):
    resp = chain.invoke(payload)
    return parser.invoke(resp)

# ——— URL / HTML helpers ———
def ensure_url(url):
    u = url.strip()
    return u if u.startswith("http") else "https://" + u

def load_and_clean_html(url):
    try:
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tag in soup(['script','style','noscript']):
            tag.decompose()
        for c in soup.find_all(string=lambda s:isinstance(s,Comment)):
            c.extract()
        return soup.prettify()
    except Exception as e:
        logger.error(f"Error loading {url}: {e}")
        return None

# ——— Data‐Cleaning Helpers ———
def clean_social_media_data(ws, cm):
    fields = ["Facebook","Twitter","Instagram","TikTok","YouTube","Linkedin"]
    data = {f: getattr(ws.social_media, f, None) or getattr(cm.social_media, f, None) for f in fields}
    return SocialMedia(**data)

def clean_location_data(cm, oc) -> Location:
    fields = ["AddressLine1","AddressLine2","Town","County","PostCode","Country","CountryCode"]
    data = {f: getattr(oc.location, f, None) or getattr(cm.location, f, None) for f in fields}
    return Location(**data)

def clean_contact_info_data(ws, oc):
    merged, seen = [], set()
    def add(ci: ContactInfo):
        key=(ci.contact_label,ci.email,ci.phone)
        if key not in seen:
            seen.add(key); merged.append(ci)
    for ci in oc.contact_info: add(ci)
    for ci in ws.contact_info: add(ci)
    return merged

def geocode_location_as_string(loc):
    parts = [loc.AddressLine1, loc.AddressLine2, loc.Town, loc.County, loc.PostCode, loc.Country]
    addr = ", ".join(p.strip() for p in parts if p and p.strip())
    if not addr:
        return None
    geo = Nominatim(user_agent="club_locator_app")
    try:
        place = geo.geocode(addr)
        time.sleep(1)
        return f"{place.latitude},{place.longitude}" if place else None
    except:
        return None


# ——— Workflow Functions ———
def process_league_url(url):
    soup = fetch_wikipedia_page(url)
    if not soup:
        return None
    name, text = clean_wikipedia_page(soup)
    if not text:
        return None
    league_model = run_chain(chain_league, parser_league, name, text)
    insert_league_with_divisions(league_model, league_model.website_link or "")
    return league_model

def process_club(club, league_model, max_len = 300000):
    # generate wiki link
    page = (club.get("wiki_page") or "").strip()
    if not page:
        return
    
    name = club.get("club_name","Unknown")
    wiki_url = f"https://en.wikipedia.org/wiki/{page}"
    soup = fetch_wikipedia_page(wiki_url)
    
    if not soup:
        return
    _, ctext = clean_wikipedia_page(soup)
    ctext = ctext[:max_len]
    club_model = run_chain(chain_club, parser_club, name, ctext)

    # homepage + official pages
    home_html = load_and_clean_html(ensure_url(club_model.website_link))
    if not home_html:
        return

    ws_model = run_chain(chain_ClubWebsite, parser_ClubWebsite, home_html) if home_html else None
    urls = ws_model.urls_of_interest if ws_model else None
    raw = []

    for attr in ("contact_page_url", "club_officials_url"):
        vals = getattr(urls, attr) or []
        if isinstance(vals, str):
            vals = [vals]
        for u in vals:
            h = load_and_clean_html(ensure_url(u))
            if h:
                raw.append(h)
    
    combined_html = "\n<hr/>".join(raw)

    oc_model = run_chain(chain_ClubOfficialAndContact, parser_ClubOfficialAndContact, combined_html) if raw else None

    # clean/merge
    cleaned_social = clean_social_media_data(ws_model, club_model) if ws_model else club_model.social_media
    clean_loc = clean_location_data(club_model, oc_model) if oc_model else club_model.location
    clean_contact = clean_contact_info_data(ws_model, oc_model) if (ws_model and oc_model) else []
    coord_str = geocode_location_as_string(clean_loc)

    cid = add_location_and_club(clean_loc, club_model, ws_model, coord_str)
    add_club_details(ws_model, cleaned_social, clean_contact, cid)
    add_movement_and_division_club(cid, club_model)

def process_divisions_in_league(league_model: League):
    for div in league_model.divisions:
        clubs = div.club or []
        with ThreadPoolExecutor(max_workers=10) as exec_club:
            futures = [exec_club.submit(process_club, c, league_model) for c in clubs]
            for _ in as_completed(futures):
                pass  

# ——— Main ———
if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=5) as exec_league:
        futures = [exec_league.submit(process_league_url, url) for url in league_links]
        for fut in as_completed(futures):
            lm = fut.result()
            if lm:
                process_divisions_in_league(lm)
