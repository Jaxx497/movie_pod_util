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
    print(mov)
    output_db()


def output_db():
    CONN = sqlite3.connect("movies.db")
    CURSOR = CONN.cursor()

    CURSOR.execute("SELECT * FROM movies")
    output = CURSOR.fetchall()
    CONN.close()

    yapo = [x for x in output if x[2] is not None]
    sorte_list = sorted(yapo, key=lambda x: x[2])

    for i in sorte_list:
        title = i[0]
        budget = i[2]
        print(f"  {bcolors.OKCYAN}{title[0:35]:<40}{bcolors.WARNING}${budget:>12,}")


if __name__ == "__main__":
    main()
