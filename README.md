# Movies & Series Information Report

A Python command-line tool that uses the **TMDB API** to collect movie and TV series information and generate a structured PDF report.

The tool can search for movies and TV series based on type, release status, year, month, region, genre, and number of pages.

## Features

* 🎬 Movie information
* 📺 TV series information
* 🔎 Search by release status
* 📅 Filter by year
* 🗓️ Filter by month
* 🌍 Filter by country/region
* 🎭 Filter by genre
* 📄 Generate PDF reports
* 🖼️ Download movie and series poster images
* ⚡ Command-line interface
* 🔐 TMDB API token stored through an environment variable

## Example Output

```text
$ python3 mov_ser_report.py --type movies --status upcoming --year 2026

============================================================
       MOVIE & SERIES INFORMATION REPORT
============================================================

[+] TMDB API connection established
[+] Content type: Movies
[+] Status: Upcoming
[+] Year: 2026
[+] Pages: 1

[*] Searching TMDB...
[*] Processing results...

[+] Movies found: 20

------------------------------------------------------------
1. Example Movie Title
------------------------------------------------------------
Title        : Example Movie Title
Release Date : 2026-03-15
Rating       : 7.8
Votes        : 1250
Genre        : Action, Adventure
Language     : English
Overview     : Example movie description...

------------------------------------------------------------
2. Another Movie
------------------------------------------------------------
Title        : Another Movie
Release Date : 2026-04-20
Rating       : 7.4
Votes        : 892
Genre        : Drama, Thriller
Language     : English
Overview     : Example movie description...

[*] Downloading poster images...
[+] Poster images processed

[*] Generating PDF report...
[+] PDF report generated successfully

============================================================
Report saved to:
movie_series_report.pdf
============================================================
```

## Requirements

* Python 3.9 or newer
* TMDB Read Access Token
* Internet connection

Python packages:

```text
requests>=2.31,<3
reportlab>=4.0,<5
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Jedi1010/mov_ser_report.git
cd mov_ser_report
```

### 2. Create a virtual environment

Recommended on Kali Linux:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## TMDB API Token

This project requires a **TMDB API Read Access Token**.

Do not put your personal API token directly into the Python source code or upload it to GitHub.

### Set the token on Kali Linux

```bash
export TMDB_TOKEN='YOUR_TMDB_READ_ACCESS_TOKEN'
```

Check that it is available:

```bash
echo $TMDB_TOKEN
```

You can also create a `.env` file for your local environment, but do **not** commit it to GitHub.

Example:

```text
TMDB_TOKEN=YOUR_TMDB_READ_ACCESS_TOKEN
```

## Usage

Show the available commands:

```bash
python3 mov_ser_report.py --help
```

### Generate an upcoming movie report

```bash
python3 mov_ser_report.py --type movies --status upcoming
```

### Search movies for a specific year

```bash
python3 mov_ser_report.py --type movies --status released --year 2026
```

### Search TV series

```bash
python3 mov_ser_report.py --type series --status released --year 2026
```

### Search both movies and series

```bash
python3 mov_ser_report.py --type both --status both --year 2026
```

### Search a specific month

The month option requires a year.

```bash
python3 mov_ser_report.py --type movies --year 2026 --month 10
```

### Search by region

For example, United Arab Emirates:

```bash
python3 mov_ser_report.py --type movies --region AE
```

United States:

```bash
python3 mov_ser_report.py --type movies --region US
```

United Kingdom:

```bash
python3 mov_ser_report.py --type movies --region GB
```

### Search by genre

```bash
python3 mov_ser_report.py --type movies --genre Action
```

### Search multiple pages

```bash
python3 mov_ser_report.py --type movies --status upcoming --pages 5
```

### Specify an output PDF

```bash
python3 mov_ser_report.py \
    --type movies \
    --status upcoming \
    --year 2026 \
    --output upcoming_movies.pdf
```

## Command-Line Options

| Option     | Description                                      |
| ---------- | ------------------------------------------------ |
| `--type`   | `movies`, `series`, or `both`                    |
| `--status` | `released`, `upcoming`, or `both`                |
| `--year`   | Filter by release/air year                       |
| `--month`  | Filter by month, 1–12                            |
| `--region` | ISO country/region code such as `US`, `GB`, `AE` |
| `--genre`  | Filter by genre                                  |
| `--pages`  | Number of TMDB result pages, 1–5                 |
| `--output` | Output PDF filename                              |

For the complete list of options:

```bash
python3 mov_ser_report.py --help
```

## Example Workflow

```bash
git clone https://github.com/Jedi1010/mov_ser_report.git
cd mov_ser_report

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

export TMDB_TOKEN='YOUR_TMDB_READ_ACCESS_TOKEN'

python3 mov_ser_report.py \
    --type both \
    --status upcoming \
    --year 2026 \
    --pages 3 \
    --output movie_series_report.pdf
```

The generated PDF will be saved in the current directory.

## Project Structure

```text
mov_ser_report/
│
├── mov_ser_report.py
├── requirements.txt
├── README.md
├── DISCLAIMER.md
├── SECURITY.md
├── CONTRIBUTING.md
├── LICENSE
├── .gitignore
└── .env.example
```

## API

This project uses the **TMDB API** to retrieve movie and TV series information.

TMDB data is provided by TMDB.

This product uses the TMDB API but is not endorsed or certified by TMDB.

## Security

Never publish your TMDB API token in:

* Python source code
* GitHub repositories
* README files
* Screenshots
* Public posts
* Error logs

Use an environment variable instead:

```bash
export TMDB_TOKEN='YOUR_TMDB_READ_ACCESS_TOKEN'
```

If you accidentally publish your token, revoke or rotate it through your TMDB account.

## Disclaimer

This project is provided for informational and educational purposes.

The developer does not guarantee the accuracy, completeness, or availability of information returned by third-party services.

Users are responsible for complying with:

* TMDB API terms and policies
* Applicable laws and regulations
* Third-party service requirements
* Any applicable copyright and licensing requirements

See [`DISCLAIMER.md`](DISCLAIMER.md) for additional information.

## Contributing

Contributions, bug reports, and improvements are welcome.

Before submitting changes:

1. Fork the repository.
2. Create a new branch.
3. Make your changes.
4. Test the application.
5. Commit your changes.
6. Create a pull request.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License.

See [`LICENSE`](LICENSE) for the complete license text.

## Author

**Jedi1010**

GitHub:

https://github.com/Jedi1010

## Acknowledgements

Thanks to **TMDB** for providing the API used by this project.

---

**Important:** You must provide your own TMDB Read Access Token to use the application. Do not share or commit your private token.
