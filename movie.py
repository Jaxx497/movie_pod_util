import sqlite3
import requests
from creds import BEARER
from dataclasses import dataclass


@dataclass
class Ratings:
    imdb: str = ""
    imdb_v: str = ""
    rt: str = ""
    mc: str = ""

    def __init__(self, ratings, imdb_v):
        """
        Serialize the rating information
        """
        flat: dict[str, str] = {item["Source"]: item["Value"] for item in ratings}

        self.imdb = flat.get("Internet Movie Database")  # type: ignore
        self.imdb_v = imdb_v
        self.rt = flat.get("Rotten Tomatoes")  # type: ignore
        self.mc = flat.get("Metacritic")  # type: ignore


class Movie:
    def __init__(self):
        search_str = input("Enter a title: ")
        payload = self.__build_raw(search_str)
        print("successfully built payload")
        self.__build_mov(payload)
        self.update_db()
        # #########
        # DEBUGGING
        ###########

        # import pprint as pp
        #
        # pp.pprint(payload)

    def __build_mov(self, xe: dict[str, str]):
        """
        From a successful search, build Movie obj.
        """
        self.actors = xe.get("Actors")
        self.age_rating = xe.get("Rated")
        self.box_dom = xe.get("BoxOffice")
        self.box_for = None
        self.box_ww = xe.get("revenue")
        self.budget = xe.get("budget")
        self.country = xe.get("Country")
        self.director = xe.get("Director")
        self.genre = xe.get("Genre")
        self.imdb_id = xe.get("imdbID")
        self.plot = xe.get("overview")
        self.ratings = Ratings(xe.get("Ratings"), xe.get("imdbVotes"))
        self.released = xe.get("Released")
        self.title = xe.get("Title")
        self.writer = xe.get("Writer")
        self.year = xe.get("Year")
        self.runtime = (
            "{}h {:02d}min".format(*divmod(xe.get("runtime"), 60))  # type: ignore
            if xe.get("runtime") is not None
            else None
        )
        self.awards = xe.get("Awards")

        # Calculate foreign box office value
        if self.box_ww is not None and self.box_dom is not None:
            self.box_for = self.box_ww - self.box_dom  # type: ignore

        # Set plot fallback
        if self.plot is None:
            self.plot = xe.get("Plot")

    def __build_raw(self, usr_title: str) -> dict[str, str]:
        """
        From a `usr_title`, search APIs for movie info
        """
        # omdb_res = None
        # if "|" in usr_title:
        #     title, year = usr_title.split(" | ", 1)
        #     print(year)
        #     omdb_req = requests.get(
        #         f"http://www.omdbapi.com/?apikey=8648ed18&t={title}&y={year}",
        #         timeout=(3, 6),
        #     )
        #     omdb_res = omdb_req.json()
        # else:
        omdb_req = requests.get(
            f"http://www.omdbapi.com/?apikey=8648ed18&t={usr_title}",
            timeout=(3, 6),
        )

        omdb_res = omdb_req.json()

        if omdb_res.get("Response") == "False":
            import sys

            print("Bad Input")
            sys.exit(1)

        movie_id = omdb_res.get("imdbID")

        headers = {
            "accept": "application/json",
            "Authorization": BEARER,
        }

        tmdb_req = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US",
            headers=headers,
            timeout=(3, 6),
        )

        tmdb_res = tmdb_req.json()

        merged = {**omdb_res, **tmdb_res}

        for k, v in merged.items():
            if v in ["N/A", 0]:
                merged[k] = None

            elif "$" in str(v) and k != "overview":
                merged[k] = int(v.replace("$", "").replace(",", ""))

            elif k in ["Actors", "Language", "Writer"]:
                if "," in v:
                    merged[k] = v.split(", ")
                else:
                    merged[k] = [v]

        return merged

    def make_template_md(self):
        bad_char = "%:/,.\\[]<>|*?\"'"
        save_title = "".join([c for c in self.title if c not in bad_char]).replace(
            " ", "_"
        )

        with open(f"./md/{save_title}.md", "w", encoding="utf-8") as file:
            file.write(
                f"# [*{self.title}* ({self.year})](https://imdb.com/title/{self.imdb_id})\n"
            )
            file.write(f"\n> {self.plot}")
            file.write("\n")
            file.write("### *General*\n")
            file.write(f"- *Released*: {self.released} ({self.country})\n")
            file.write(f"- *Awards*: {self.awards}\n")
            file.write(f"- *Runtime*: {self.runtime}\n")
            file.write(f"- *Genre*: {self.genre }\n")
            file.write(f"- *Director*: {self.director}\n")

            if self.writer:
                if len(self.writer) > 1:
                    file.write("- *Writers*:\n")
                    for writer in self.writer:
                        file.write(f"\t- {writer}\n")
                else:
                    file.write(f"- *Writer*: {self.writer[0]}\n")

            if self.actors:
                file.write("- *Actors*:\n")
                for actor in self.actors:
                    file.write(f"\t- {actor}\n")

            file.write("\n### *Finances*\n")
            for attribute, title in [
                (self.budget, "Budget"),
                (self.box_dom, "Box Office (D)"),
                (self.box_for, "Box Office (F)"),
                (self.box_ww, "Box Office (\\*)"),
            ]:
                if attribute is not None and attribute is not 0:
                    file.write(f"- *{title}*: ${attribute:,}\n")

            file.write("\n### *Ratings* \n")
            for attribute, agency in [
                (self.ratings.mc, "MetaCritic"),
                (self.ratings.rt, "Rotten Tomatoes"),
                (self.ratings.imdb, "IMDb"),
            ]:
                if attribute is None:
                    continue
                elif agency == "IMDb":
                    file.write(
                        f"- {agency}: {attribute} ({self.ratings.imdb_v})\n"
                    )  # noqa
                else:
                    file.write(f"- {agency}: {attribute}\n")

    def update_db(self):
        CONN = sqlite3.connect("movies.db")
        CURSOR = CONN.cursor()

        try:
            CURSOR.execute(
                "INSERT INTO movies (title, year, budget) VALUES (?, ?, ?)",
                (self.title, self.year, self.budget),
            )

            CONN.commit()
            print(f"Added {self.title} successfully!")
        except:
            print(f"Error: {self.title} already exists.")
        finally:
            CONN.close()
