import sqlite3
import argparse
import pprint as pp
from src.movie import Movie


class bcolors:
    DEFAULT = "\033[1;37m"
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    TEMP = "\u001b[38;2;145;231;255m"


def init():
    """
    Initialize working directory with new database, markdown folder, and config file.
    """

    import os
    import sys
    from pathlib import Path

    try:
        path = Path("md/")
        if not path.exists():
            path.mkdir(parents=True)
            print(f"Directory '{path}' created.")
        else:
            print(f"Directory '{path}' already exists.")
    except Exception as e:
        print(f"Error: {e}")

    try:
        CONN = sqlite3.connect("movies.db")
        CURSOR = CONN.cursor()

        CURSOR.execute(
            """CREATE TABLE movies (
            imdb_id TEXT UNIQUE,
            title TEXT NOT NULL,
            year TEXT NOT NULL,
            budget INTEGER NOT NULL
            ) """
        )

        CONN.commit()
        CONN.close()
        print("Successfully created database!")
    except Exception as e:
        print(f"Error: {e}")

    if not os.path.exists("config.ini"):
        with open("config.ini", "w") as f:
            f.write("[API_KEYS]")
            f.write("omdb = ")
            f.write("tmdb = ")
        f.close()
        print("`config.ini` has been created.\nMake sure to insert API data")
        sys.exit(1)


def db_output(sort_key: str) -> None:
    """
    Output a list of movies and their budgets, ordered by name or budget.

    Parameters
    ----------
    `sort_key`: Key to determine how to sort the output table.

    "budget" (default) -> Sort by budget, ascending
    "year" -> Sort by year, ascending
    "title" -> Sort by title, alphabetical
    """
    CONN = sqlite3.connect("movies.db")
    CURSOR = CONN.cursor()

    CURSOR.execute(f"SELECT * FROM movies ORDER BY {sort_key}")
    sorted_list = CURSOR.fetchall()
    CONN.close()

    max_bud = max(sorted_list, key=lambda x: x[3])[3]

    for i in sorted_list:
        title = i[1]
        year = i[2]
        budget = i[3]

        yarsh = round((budget / max_bud) * 20)
        print(
            f"{bcolors.FAIL}({year}) {bcolors.OKCYAN}{title[0:35]:<40}{bcolors.WARNING}${budget:>12,} "
            + (yarsh * "*")
        )
    print(f"Output: {bcolors.DEFAULT}{len(sorted_list)} titles.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("title", help="Search query")
    parser.add_argument("-y", "--year", help="Search year of film")
    parser.add_argument(
        "-o", "--output", action="store_true", help="Display movie info in console"
    )
    parser.add_argument(
        "-md", "--markdown", action="store_true", help="Publish movie in markdown file"
    )

    parser.add_argument(
        "-db",
        "--database",
        help="Show budget table sorted by key",
        choices=["title", "year", "budget"],
        dest="sort_key",
    )

    args = parser.parse_args()

    final_output = None

    if args.title == "init":
        init()

    elif args.title not in ["qq", "jj", "zz", "!"]:
        mov = Movie(args.title, args.year)

        final_output = mov.output_std() if args.output else None
        if args.markdown:
            print("OUTPUTTING TO MD")
            final_output = mov.output_md()

    if args.sort_key:
        db_output(args.sort_key)

    if args.output:
        pp.pprint(final_output)
