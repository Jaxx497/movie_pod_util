from dataclasses import dataclass
from movie import Movie
import pprint as pp
import sqlite3


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


def main():
    mov = Movie()
    print(mov.__dict__)
    output_db()
    mov.make_template_md()


def output_db(sort_key: str = "budget") -> None:
    """
    Output a list of movies and their budgets, ordered by name or budget.

    Parameters
    ----------

    sort_key : Key which determines how the output is sorted.
    Default value = "budget"
    """
    CONN = sqlite3.connect("movies.db")
    CURSOR = CONN.cursor()

    CURSOR.execute("SELECT * FROM movies")
    output = CURSOR.fetchall()
    CONN.close()

    clean_table = [x for x in output if x[2] is not None]
    sorted_list = []

    match sort_key:
        case "title":
            sorted_list = sorted(clean_table, key=lambda x: x[0])

        case "budget":
            sorted_list = sorted(clean_table, key=lambda x: x[2])

    for i in sorted_list:
        title = i[0]
        year = i[1]
        budget = i[2]
        print(
            f" ({year}) {bcolors.OKCYAN}{title[0:35]:<40}{bcolors.WARNING}${budget:>12,}"
        )
    print(f"Output {len(sorted_list)} titles.")


if __name__ == "__main__":
    main()
