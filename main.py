import sys
import sqlite3
import argparse
import pprint as pp
from src.template import Template
from src.movie import Movie


############### TODO ###############
# Create config file
# Handle args
# Handle output
####################################


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    TEMP = "\u001b[38;2;145;231;255m"


def db_new():
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

    CURSOR.execute("SELECT * FROM movies")
    output = CURSOR.fetchall()
    CONN.close()

    clean_table = [x for x in output if x[3] is not None]
    sorted_list = sorted(
        clean_table, key=lambda x: x[{"title": 1, "year": 2, "budget": 3}[sort_key]]
    )

    # budgets = [item[3] for item in clean_table]
    #
    # budget_range = max(budgets)

    for i in sorted_list:
        title = i[1]
        year = i[2]
        budget = i[3]
        # yarsh = round((budget / budget_range) * 20)
        print(
            f"{bcolors.FAIL}({year}) {bcolors.OKCYAN}{title[0:35]:<40}${budget:>12,} "
            # + (yarsh * "*")
        )
    print(f"Output: {len(sorted_list)} titles.")


if __name__ == "__main__":
    # db_new()
    parser = argparse.ArgumentParser()

    parser.add_argument("title", help="Search query")
    parser.add_argument("-y", "--year", help="Search year of film")
    parser.add_argument(
        "-o",
        "--output",
        help='Output movie to console ["std"] or markdown file ["md"]',
        choices=["std", "md"],
    )
    parser.add_argument(
        "-d",
        "--database",
        help="Show budget table sorted by key",
        choices=["title", "year", "budget"],
        dest="sort_key",
    )

    args = parser.parse_args()

    mov = None
    # If a year is inserted and not a search title...

    if args.title not in ["qq", "jj", "zz", "!"]:
        # if args.year and not args.title:
        #     print("Unable to complete search without a title")
        #
        # elif args.output and not args.title:
        #     print("Unable to complete output without a title")
        #
        # elif args.title:
        mov = Movie(args.title, args.year)

        # Match OUTPUT options
        match args.output:
            case "std":
                try:
                    pp.pprint(mov.__dict__)
                except:
                    "No video to output"
            case "md":
                print("OUTPUTTING TO MD")
                x = Template(mov)
                x.new_md()
            case _:
                pass

    if args.sort_key is not None:
        db_output(args.sort_key)
