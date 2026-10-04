#!/usr/bin/env python3

import argparse
import html
import os
import sys
import time
from datetime import date, datetime, timedelta
from io import BytesIO
from pathlib import Path

import requests
from dotenv import load_dotenv

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    Image,
)

# Load variables from .env
load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

DEFAULT_LANGUAGE = "en-US"
REQUEST_TIMEOUT = 30
CREATOR = "Jedi1010"


# ============================================================
# TERMINAL COLORS
# ============================================================

class Colors:
    RESET = "\033[0m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    BOLD = "\033[1m"


def color(text, colour):
    return f"{colour}{text}{Colors.RESET}"


# ============================================================
# BANNER
# ============================================================

def print_banner():

    banner = r"""
╔═════════════════════════════════════════════════════════╗
║                                                         ║
║     ███╗   ███╗ ██████╗ ██╗   ██╗██╗███████╗            ║
║     ████╗ ████║██╔═══██╗██║   ██║██║██╔════╝            ║
║     ██╔████╔██║██║   ██║██║   ██║██║█████╗              ║
║     ██║╚██╔╝██║██║   ██║╚██╗ ██╔╝██║██╔══╝              ║
║     ██║ ╚═╝ ██║╚██████╔╝ ╚████╔╝ ██║███████╗            ║
║     ╚═╝     ╚═╝ ╚═════╝   ╚═══╝  ╚═╝╚══════╝            ║
║                                                         ║
║              MOVIES & SERIES INFORMATION TOOL           ║
║                                                         ║
║                         Jedi1010                        ║
║                                                         ║
╚═════════════════════════════════════════════════════════╝
"""

    print(color(banner, Colors.BRIGHT_CYAN))


# ============================================================
# TMDB CLIENT
# ============================================================

class TMDBClient:

    def __init__(self, token):

        if not token:
            raise ValueError(
                "TMDB token was not supplied."
            )

        self.token = token

        self.session = requests.Session()

        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "accept": "application/json",
        })

    def get(self, endpoint, params=None):

        url = TMDB_BASE_URL + endpoint

        try:

            response = self.session.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 401:

                raise RuntimeError(
                    "TMDB authentication failed. "
                    "Check your TMDB Read Access Token."
                )

            if response.status_code == 429:

                print(
                    color(
                        "[!] TMDB rate limit reached. Waiting...",
                        Colors.BRIGHT_YELLOW,
                    )
                )

                time.sleep(5)

                response = self.session.get(
                    url,
                    params=params,
                    timeout=REQUEST_TIMEOUT,
                )

            response.raise_for_status()

            return response.json()

        except requests.RequestException as exc:

            print(
                color(
                    f"[!] TMDB request failed: {exc}",
                    Colors.BRIGHT_RED,
                )
            )

            return None


# ============================================================
# GENERAL HELPERS
# ============================================================

def safe(value):

    if value is None:
        return "N/A"

    value = str(value).strip()

    return value if value else "N/A"


def truncate(text, length=500):

    text = safe(text)

    if len(text) <= length:
        return text

    return text[:length - 3] + "..."


def parse_iso_date(value):

    if not value:
        return None

    try:

        return datetime.strptime(
            value,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        return None


def format_date(value):

    parsed = parse_iso_date(value)

    if not parsed:
        return "N/A"

    return parsed.strftime("%Y-%m-%d")


def escape_pdf(value):

    return html.escape(
        safe(value)
    )


# ============================================================
# GENRES
# ============================================================

def get_genre_maps(client):

    movie_data = client.get(
        "/genre/movie/list",
        {
            "language": DEFAULT_LANGUAGE
        }
    )

    tv_data = client.get(
        "/genre/tv/list",
        {
            "language": DEFAULT_LANGUAGE
        }
    )

    movie_genres = {}
    tv_genres = {}

    if movie_data:

        for genre in movie_data.get(
            "genres",
            []
        ):

            movie_genres[
                genre["name"].lower()
            ] = genre["id"]

    if tv_data:

        for genre in tv_data.get(
            "genres",
            []
        ):

            tv_genres[
                genre["name"].lower()
            ] = genre["id"]

    return movie_genres, tv_genres


def resolve_genres(
    genre_text,
    movie_genres,
    tv_genres
):

    if not genre_text:
        return None, None

    movie_ids = []
    tv_ids = []

    values = [
        x.strip()
        for x in genre_text.split(",")
        if x.strip()
    ]

    for value in values:

        if value.isdigit():

            genre_id = int(value)

            movie_ids.append(genre_id)
            tv_ids.append(genre_id)

            continue

        key = value.lower()

        if key in movie_genres:

            movie_ids.append(
                movie_genres[key]
            )

        if key in tv_genres:

            tv_ids.append(
                tv_genres[key]
            )

    return (
        list(dict.fromkeys(movie_ids)),
        list(dict.fromkeys(tv_ids))
    )


# ============================================================
# CAST
# ============================================================

def extract_cast(credits):

    cast = credits.get(
        "cast",
        []
    )

    top_cast = []
    male_cast = []
    female_cast = []

    for person in cast:

        name = person.get("name")

        if not name:
            continue

        entry = {
            "name": name,
            "character": safe(
                person.get("character")
            ),
            "gender": person.get("gender"),
            "order": person.get(
                "order",
                9999
            ),
        }

        top_cast.append(entry)

        if person.get("gender") == 2:

            male_cast.append(entry)

        elif person.get("gender") == 1:

            female_cast.append(entry)

    top_cast.sort(
        key=lambda x: x["order"]
    )

    male_cast.sort(
        key=lambda x: x["order"]
    )

    female_cast.sort(
        key=lambda x: x["order"]
    )

    return {
        "top": top_cast[:10],
        "male": male_cast[:5],
        "female": female_cast[:5],
    }


def names_only(cast):

    if not cast:
        return "N/A"

    return ", ".join(
        item["name"]
        for item in cast
    )


# ============================================================
# DETAILS
# ============================================================

def get_details(
    client,
    media_type,
    item_id
):

    endpoint = (
        f"/movie/{item_id}"
        if media_type == "movie"
        else f"/tv/{item_id}"
    )

    return client.get(
        endpoint,
        {
            "language": DEFAULT_LANGUAGE,
            "append_to_response": "credits",
        }
    ) or {}


# ============================================================
# AUDIO LANGUAGE
# ============================================================

def extract_audio_languages(details):

    languages = []

    for language in details.get(
        "spoken_languages",
        []
    ):

        name = language.get(
            "english_name"
        )

        if name:
            languages.append(name)

    if not languages:

        original = details.get(
            "original_language"
        )

        if original:

            languages.append(
                original.upper()
            )

    languages = list(
        dict.fromkeys(languages)
    )

    return (
        ", ".join(languages)
        if languages
        else "N/A"
    )


# ============================================================
# COUNTRY OF ORIGIN
# ============================================================

def extract_origin_country(details):

    countries = []

    for country in details.get(
        "production_countries",
        []
    ):

        name = country.get("name")

        if name:
            countries.append(name)

    if not countries:

        for country in details.get(
            "origin_country",
            []
        ):

            if country:
                countries.append(country)

    countries = list(
        dict.fromkeys(countries)
    )

    return (
        ", ".join(countries)
        if countries
        else "N/A"
    )


# ============================================================
# PRODUCTION COMPANIES
# ============================================================

def extract_production_companies(details):

    companies = []

    for company in details.get(
        "production_companies",
        []
    ):

        name = company.get("name")

        if name:
            companies.append(name)

    companies = list(
        dict.fromkeys(companies)
    )

    return (
        ", ".join(companies)
        if companies
        else "N/A"
    )


# ============================================================
# GENRE NAMES
# ============================================================

def extract_genres(details):

    genres = []

    for genre in details.get(
        "genres",
        []
    ):

        name = genre.get("name")

        if name:
            genres.append(name)

    return (
        ", ".join(genres)
        if genres
        else "N/A"
    )


# ============================================================
# NORMALIZE ITEM
# ============================================================

def normalize_item(
    client,
    item,
    media_type
):

    item_id = item.get("id")

    if not item_id:
        return None

    if media_type == "movie":

        title = item.get("title")

        release_date = item.get(
            "release_date"
        )

        media_label = "Movie"

    else:

        title = item.get("name")

        release_date = item.get(
            "first_air_date"
        )

        media_label = "TV Series"

    parsed_date = parse_iso_date(
        release_date
    )

    if not title or not parsed_date:
        return None

    details = get_details(
        client,
        media_type,
        item_id
    )

    credits = details.get(
        "credits",
        {}
    )

    cast = extract_cast(
        credits
    )

    rating = (
        item.get("vote_average")
        or details.get(
            "vote_average"
        )
    )

    try:

        rating_text = (
            f"{float(rating):.1f}/10"
        )

    except (
        ValueError,
        TypeError
    ):

        rating_text = "N/A"

    poster_path = (
        details.get("poster_path")
        or item.get("poster_path")
    )

    return {

        "id": item_id,

        "media_type": media_type,

        "type": media_label,

        "title": safe(title),

        "release_date": release_date,

        "release_obj": parsed_date,

        "rating": rating_text,

        "genres": extract_genres(
            details
        ),

        "audio_languages":
            extract_audio_languages(
                details
            ),

        "origin_country":
            extract_origin_country(
                details
            ),

        "production_companies":
            extract_production_companies(
                details
            ),

        "overview": truncate(
            details.get(
                "overview"
            )
            or item.get(
                "overview"
            )
        ),

        # TMDB poster path
        "poster_path": poster_path,

        "top_cast": cast["top"],

        "male_cast": cast["male"],

        "female_cast": cast["female"],

        "tmdb_url": (
            "https://www.themoviedb.org/"
            + (
                "movie/"
                if media_type == "movie"
                else "tv/"
            )
            + str(item_id)
        ),
    }


# ============================================================
# DISCOVER
# ============================================================

def discover(
    client,
    media_type,
    mode,
    year=None,
    month=None,
    region=None,
    genre_ids=None,
    pages=1
):

    results = []

    today = date.today()

    if media_type == "movie":

        endpoint = "/discover/movie"

    else:

        endpoint = "/discover/tv"

    for page in range(
        1,
        pages + 1
    ):

        params = {
            "language": DEFAULT_LANGUAGE,
            "sort_by": "popularity.desc",
            "page": page,
        }

        # ----------------------------------------------------
        # RELEASED
        # ----------------------------------------------------

        if mode == "released":

            if media_type == "movie":

                params[
                    "release_date.lte"
                ] = today.isoformat()

                if year:

                    params[
                        "release_date.gte"
                    ] = f"{year}-01-01"

            else:

                params[
                    "first_air_date.lte"
                ] = today.isoformat()

                if year:

                    params[
                        "first_air_date.gte"
                    ] = f"{year}-01-01"

        # ----------------------------------------------------
        # UPCOMING
        # ----------------------------------------------------

        elif mode == "upcoming":

            tomorrow = (
                today
                + timedelta(days=1)
            )

            if media_type == "movie":

                params[
                    "release_date.gte"
                ] = tomorrow.isoformat()

                if year:

                    params[
                        "release_date.lte"
                    ] = f"{year}-12-31"

            else:

                params[
                    "first_air_date.gte"
                ] = tomorrow.isoformat()

                if year:

                    params[
                        "first_air_date.lte"
                    ] = f"{year}-12-31"

        # ----------------------------------------------------
        # YEAR
        # ----------------------------------------------------

        if year:

            if media_type == "movie":

                params["year"] = year

            else:

                params[
                    "first_air_date_year"
                ] = year

        # ----------------------------------------------------
        # MONTH
        # ----------------------------------------------------

        if month:

            if not year:

                raise ValueError(
                    "--month requires --year"
                )

            start = date(
                year,
                month,
                1
            )

            if month == 12:

                end = (
                    date(
                        year + 1,
                        1,
                        1
                    )
                    - timedelta(days=1)
                )

            else:

                end = (
                    date(
                        year,
                        month + 1,
                        1
                    )
                    - timedelta(days=1)
                )

            if media_type == "movie":

                params[
                    "release_date.gte"
                ] = start.isoformat()

                params[
                    "release_date.lte"
                ] = end.isoformat()

            else:

                params[
                    "first_air_date.gte"
                ] = start.isoformat()

                params[
                    "first_air_date.lte"
                ] = end.isoformat()

        # ----------------------------------------------------
        # REGION
        # ----------------------------------------------------

        if region:

            region = region.upper()

            if media_type == "movie":

                params["region"] = region

            else:

                params[
                    "with_origin_country"
                ] = region

        # ----------------------------------------------------
        # GENRES
        # ----------------------------------------------------

        if genre_ids:

            params["with_genres"] = ",".join(
                str(x)
                for x in genre_ids
            )

        data = client.get(
            endpoint,
            params
        )

        if not data:
            continue

        for item in data.get(
            "results",
            []
        ):

            normalized = normalize_item(
                client,
                item,
                media_type
            )

            if normalized:

                results.append(
                    normalized
                )

    return results


# ============================================================
# FILTER
# ============================================================

def filter_results(
    results,
    year=None,
    month=None
):

    output = []

    for item in results:

        release_date = item[
            "release_obj"
        ]

        if year:

            if release_date.year != year:
                continue

        if month:

            if release_date.month != month:
                continue

        output.append(item)

    return output


# ============================================================
# SORT
# ============================================================

def sort_results(results):

    return sorted(
        results,
        key=lambda x: (
            x["release_obj"],
            x["title"].lower()
        )
    )


# ============================================================
# TERMINAL OUTPUT
# ============================================================

def print_item(
    item,
    number
):

    print()

    print(
        color(
            "━" * 75,
            Colors.BRIGHT_BLUE
        )
    )

    print(
        color(
            f"[{number}] {item['title']}",
            Colors.BRIGHT_WHITE
        )
    )

    print(
        color(
            "Type            : ",
            Colors.BRIGHT_CYAN
        )
        + item["type"]
    )

    print(
        color(
            "Release Date    : ",
            Colors.BRIGHT_CYAN
        )
        + format_date(
            item["release_date"]
        )
    )

    print(
        color(
            "Rating          : ",
            Colors.BRIGHT_CYAN
        )
        + item["rating"]
    )

    print(
        color(
            "Genres          : ",
            Colors.BRIGHT_CYAN
        )
        + item["genres"]
    )

    print(
        color(
            "Audio Language  : ",
            Colors.BRIGHT_CYAN
        )
        + item["audio_languages"]
    )

    print(
        color(
            "Origin Country  : ",
            Colors.BRIGHT_CYAN
        )
        + item["origin_country"]
    )

    print(
        color(
            "Production      : ",
            Colors.BRIGHT_CYAN
        )
        + item["production_companies"]
    )

    print(
        color(
            "Main Actors     : ",
            Colors.BRIGHT_CYAN
        )
        + names_only(
            item["male_cast"]
        )
    )

    print(
        color(
            "Main Actresses  : ",
            Colors.BRIGHT_CYAN
        )
        + names_only(
            item["female_cast"]
        )
    )

    print(
        color(
            "Top Cast        : ",
            Colors.BRIGHT_CYAN
        )
        + names_only(
            item["top_cast"]
        )
    )

    print(
        color(
            "Overview        : ",
            Colors.BRIGHT_CYAN
        )
    )

    print(item["overview"])

    print(
        color(
            "TMDB            : ",
            Colors.BRIGHT_CYAN
        )
        + item["tmdb_url"]
    )


def display_results(
    results,
    title
):

    print()

    print(
        color(
            f"╔══ {title} ══╗",
            Colors.BRIGHT_MAGENTA
        )
    )

    if not results:

        print(
            color(
                "No results found.",
                Colors.BRIGHT_YELLOW
            )
        )

        return

    for index, item in enumerate(
        results,
        start=1
    ):

        print_item(
            item,
            index
        )


# ============================================================
# PDF STYLES
# ============================================================

def build_pdf_styles():

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitleCustom",
            parent=styles["Title"],
            fontSize=22,
            leading=26,
            alignment=TA_CENTER,
            textColor=colors.HexColor(
                "#00B8D9"
            ),
            spaceAfter=10,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CreatorCustom",
            parent=styles["Normal"],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor(
                "#7C4DFF"
            ),
            spaceAfter=15,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ItemTitleCustom",
            parent=styles["Heading2"],
            fontSize=15,
            leading=18,
            textColor=colors.HexColor(
                "#1565C0"
            ),
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SmallCustom",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor(
                "#222222"
            ),
        )
    )

    styles.add(
        ParagraphStyle(
            name="OverviewCustom",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor(
                "#333333"
            ),
            spaceBefore=6,
        )
    )

    return styles


# ============================================================
# DOWNLOAD TMDB POSTER
# ============================================================

def get_poster_image(item):

    poster_path = item.get(
        "poster_path"
    )

    if not poster_path:
        return None

    url = (
        TMDB_IMAGE_BASE_URL
        + poster_path
    )

    try:

        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        image = Image(
            BytesIO(response.content),
            width=45 * mm,
            height=67.5 * mm,
        )

        return image

    except requests.RequestException as exc:

        print(
            color(
                (
                    f"[!] Poster download failed "
                    f"for {item.get('title', 'Unknown')}: "
                    f"{exc}"
                ),
                Colors.BRIGHT_YELLOW,
            )
        )

        return None


# ============================================================
# PDF ITEM TABLE
# ============================================================

def pdf_item_table(
    item,
    styles
):

    rows = [

        [
            Paragraph(
                "<b>Type</b>",
                styles["SmallCustom"]
            ),
            Paragraph(
                escape_pdf(
                    item["type"]
                ),
                styles["SmallCustom"]
            ),
        ],

        [
            Paragraph(
                "<b>Release Date</b>",
                styles["SmallCustom"]
            ),
            Paragraph(
                escape_pdf(
                    format_date(
                        item["release_date"]
                    )
                ),
                styles["SmallCustom"]
            ),
        ],

        [
            Paragraph(
                "<b>Rating</b>",
                styles["SmallCustom"]
            ),
            Paragraph(
                escape_pdf(
                    item["rating"]
                ),
                styles["SmallCustom"]
            ),
        ],

        [
            Paragraph(
                "<b>Genres</b>",
                styles["SmallCustom"]
            ),
            Paragraph(
                escape_pdf(
                    item["genres"]
                ),
                styles["SmallCustom"]
            ),
        ],

        [
            Paragraph(
                "<b>Audio Language</b>",
                styles["SmallCustom"]
            ),
            Paragraph(
                escape_pdf(
                    item["audio_languages"]
                ),
                styles["SmallCustom"]
            ),
        ],

        [
            Paragraph(
                "<b>Origin Country</b>",
                styles["SmallCustom"]
            ),
            Paragraph(
                escape_pdf(
                    item["origin_country"]
                ),
                styles["SmallCustom"]
            ),
        ],

        [
            Paragraph(
                "<b>Production Companies</b>",
                styles["SmallCustom"]
            ),
            Paragraph(
                escape_pdf(
                    item["production_companies"]
                ),
                styles["SmallCustom"]
            ),
        ],

        [
            Paragraph(
                "<b>Main Actors</b>",
                styles["SmallCustom"]
            ),
            Paragraph(
                escape_pdf(
                    names_only(
                        item["male_cast"]
                    )
                ),
                styles["SmallCustom"]
            ),
        ],

        [
            Paragraph(
                "<b>Main Actresses</b>",
                styles["SmallCustom"]
            ),
            Paragraph(
                escape_pdf(
                    names_only(
                        item["female_cast"]
                    )
                ),
                styles["SmallCustom"]
            ),
        ],

        [
            Paragraph(
                "<b>Top Cast</b>",
                styles["SmallCustom"]
            ),
            Paragraph(
                escape_pdf(
                    names_only(
                        item["top_cast"]
                    )
                ),
                styles["SmallCustom"]
            ),
        ],

        [
            Paragraph(
                "<b>TMDB</b>",
                styles["SmallCustom"]
            ),
            Paragraph(
                escape_pdf(
                    item["tmdb_url"]
                ),
                styles["SmallCustom"]
            ),
        ],
    ]

    info_table = Table(
        rows,
        colWidths=[
            40 * mm,
            90 * mm,
        ]
    )

    info_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor(
                    "#E3F2FD"
                ),
            ),

            (
                "BACKGROUND",
                (1, 0),
                (1, -1),
                colors.HexColor(
                    "#FAFAFA"
                ),
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.35,
                colors.HexColor(
                    "#B0BEC5"
                ),
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
        ])
    )

    # --------------------------------------------------------
    # POSTER
    # --------------------------------------------------------

    poster = get_poster_image(
        item
    )

    if poster:

        poster.hAlign = "CENTER"

        poster_table = Table(
            [[poster]],
            colWidths=[
                48 * mm
            ],
        )

        poster_table.setStyle(
            TableStyle([

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
            ])
        )

        combined = Table(
            [[
                poster_table,
                info_table,
            ]],
            colWidths=[
                50 * mm,
                130 * mm,
            ],
        )

        combined.setStyle(
            TableStyle([

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
            ])
        )

        return combined

    # --------------------------------------------------------
    # NO POSTER AVAILABLE
    # --------------------------------------------------------

    return info_table


# ============================================================
# CREATE PDF
# ============================================================

def create_pdf(
    results,
    output,
    report_title
):

    styles = build_pdf_styles()

    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=report_title,
        author=CREATOR,
    )

    story = []

    story.append(
        Paragraph(
            escape_pdf(report_title),
            styles[
                "ReportTitleCustom"
            ],
        )
    )

    story.append(
        Paragraph(
            f"Created by {CREATOR}",
            styles[
                "CreatorCustom"
            ],
        )
    )

    story.append(
        Paragraph(
            f"Generated: {date.today().isoformat()}",
            styles[
                "SmallCustom"
            ],
        )
    )

    story.append(
        Spacer(
            1,
            10
        )
    )

    for index, item in enumerate(
        results,
        start=1
    ):

        block = []

        block.append(
            Paragraph(
                escape_pdf(
                    f"{index}. {item['title']}"
                ),
                styles[
                    "ItemTitleCustom"
                ],
            )
        )

        block.append(
            pdf_item_table(
                item,
                styles
            )
        )

        block.append(
            Spacer(
                1,
                6
            )
        )

        block.append(
            Paragraph(
                "<b>Overview</b>",
                styles[
                    "SmallCustom"
                ],
            )
        )

        block.append(
            Paragraph(
                escape_pdf(
                    item["overview"]
                ),
                styles[
                    "OverviewCustom"
                ],
            )
        )

        block.append(
            Spacer(
                1,
                12
            )
        )

        story.append(
            KeepTogether(
                block
            )
        )

    story.append(
        Spacer(
            1,
            15
        )
    )

    story.append(
        Paragraph(
            (
                "Data provided by TMDB. "
                "This product uses the TMDB API "
                "but is not endorsed or certified "
                "by TMDB."
            ),
            styles[
                "SmallCustom"
            ],
        )
    )

    document.build(
        story
    )


# ============================================================
# COMMAND-LINE ARGUMENTS
# ============================================================

def build_parser():

    parser = argparse.ArgumentParser(
        description=(
            "Jedi1010 Movie & Series "
            "Information Tool"
        )
    )

    parser.add_argument(
        "--type",
        choices=[
            "movies",
            "series",
            "both"
        ],
        default="both",
        help=(
            "Media type: "
            "movies, series, or both."
        ),
    )

    parser.add_argument(
        "--status",
        choices=[
            "released",
            "upcoming",
            "both"
        ],
        default="both",
        help=(
            "released, upcoming, or both."
        ),
    )

    parser.add_argument(
        "--year",
        type=int,
        help="Year to search."
    )

    parser.add_argument(
        "--month",
        type=int,
        choices=range(1, 13),
        help=(
            "Month 1-12. "
            "Requires --year."
        ),
    )

    parser.add_argument(
        "--region",
        help=(
            "ISO 3166-1 country code, "
            "for example US, GB, AE, IN."
        ),
    )

    parser.add_argument(
        "--genre",
        help=(
            "Comma-separated genres, "
            "for example Action,Comedy."
        ),
    )

    parser.add_argument(
        "--pages",
        type=int,
        default=1,
        choices=range(1, 6),
        help=(
            "Number of TMDB pages "
            "to retrieve (1-5)."
        ),
    )

    parser.add_argument(
        "--output",
        default="movie_series_report.pdf",
        help="PDF output filename."
    )

    return parser


# ============================================================
# MAIN
# ============================================================

def main():

    print_banner()

    parser = build_parser()

    args = parser.parse_args()

    # TMDB token is loaded from .env by load_dotenv()
    token = os.environ.get(
        "TMDB_TOKEN"
    )

    if not token:

        print(
            color(
                "[!] TMDB_TOKEN is not set.",
                Colors.BRIGHT_RED
            )
        )

        print()

        print(
            color(
                "Set it in your .env file:",
                Colors.BRIGHT_YELLOW
            )
        )

        print()

        print(
            color(
                "TMDB_TOKEN=YOUR_TOKEN",
                Colors.BRIGHT_GREEN
            )
        )

        sys.exit(1)

    if args.month and not args.year:

        parser.error(
            "--month requires --year"
        )

    if args.year and args.year < 1900:

        parser.error(
            "Invalid year."
        )

    try:

        client = TMDBClient(
            token
        )

    except ValueError as exc:

        print(
            color(
                str(exc),
                Colors.BRIGHT_RED
            )
        )

        sys.exit(1)

    print(
        color(
            "[+] Connecting to TMDB...",
            Colors.BRIGHT_GREEN
        )
    )

    print(
        color(
            "[+] Loading genres...",
            Colors.BRIGHT_GREEN
        )
    )

    movie_genres, tv_genres = (
        get_genre_maps(client)
    )

    movie_genre_ids, tv_genre_ids = (
        resolve_genres(
            args.genre,
            movie_genres,
            tv_genres
        )
    )

    media_types = []

    # ========================================================
    # MEDIA TYPE
    # ========================================================

    if args.type in (
        "movies",
        "both"
    ):

        media_types.append(
            "movie"
        )

    if args.type in (
        "series",
        "both"
    ):

        media_types.append(
            "tv"
        )

    statuses = []

    if args.status in (
        "released",
        "both"
    ):

        statuses.append(
            "released"
        )

    if args.status in (
        "upcoming",
        "both"
    ):

        statuses.append(
            "upcoming"
        )

    all_results = []

    # ========================================================
    # SEARCH
    # ========================================================

    for media_type in media_types:

        for status in statuses:

            display_type = (
                "MOVIES"
                if media_type == "movie"
                else "SERIES"
            )

            print(
                color(
                    (
                        f"[+] Searching "
                        f"{display_type} "
                        f"({status})..."
                    ),
                    Colors.BRIGHT_YELLOW
                )
            )

            genre_ids = (
                movie_genre_ids
                if media_type == "movie"
                else tv_genre_ids
            )

            try:

                results = discover(
                    client=client,
                    media_type=media_type,
                    mode=status,
                    year=args.year,
                    month=args.month,
                    region=args.region,
                    genre_ids=genre_ids,
                    pages=args.pages,
                )

                all_results.extend(
                    results
                )

            except ValueError as exc:

                print(
                    color(
                        f"[!] {exc}",
                        Colors.BRIGHT_RED
                    )
                )

    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    unique = {}

    for item in all_results:

        key = (
            item["media_type"],
            item["id"]
        )

        unique[key] = item

    all_results = list(
        unique.values()
    )

    # ========================================================
    # FILTER
    # ========================================================

    all_results = filter_results(
        all_results,
        year=args.year,
        month=args.month,
    )

    # ========================================================
    # SORT
    # ========================================================

    all_results = sort_results(
        all_results
    )

    # ========================================================
    # DISPLAY
    # ========================================================

    display_results(
        all_results,
        "SEARCH RESULTS"
    )

    print()

    print(
        color(
            "═" * 75,
            Colors.BRIGHT_CYAN
        )
    )

    print(
        color(
            f"Total results: {len(all_results)}",
            Colors.BRIGHT_GREEN
        )
    )

    # ========================================================
    # PDF
    # ========================================================

    if all_results:

        print(
            color(
                "[+] Creating PDF report...",
                Colors.BRIGHT_YELLOW
            )
        )

        create_pdf(
            all_results,
            args.output,
            "Jedi1010 - Movie & Series Report"
        )

        print(
            color(
                "[+] PDF created successfully:",
                Colors.BRIGHT_GREEN
            )
        )

        print(
            color(
                str(
                    Path(
                        args.output
                    ).resolve()
                ),
                Colors.BRIGHT_CYAN
            )
        )

    else:

        print(
            color(
                "[!] No results to export.",
                Colors.BRIGHT_YELLOW
            )
        )


if __name__ == "__main__":
    main()
