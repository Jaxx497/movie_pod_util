from typing import Any
import requests
import configparser
import sqlite3

# from src.creds import BEARER
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


#################################


class Movie:
    def __init__(self, search_str: str, year: str = ""):
        """
        Create a new instance of a Movie type. A successful movie call
        (having a title, year, and budget) will be appended to the database.

        Parameters
        ----------
        `search_str (str)` : Search query to use in API call
        `year (str)` : (Optional) Specify year of film queried
        """
        payload = self.__build_raw(search_str, year)
        self.__build_mov(payload)
        self.db_add_movie()

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

    def __build_raw(self, title: str, year: str) -> dict[str, str]:
        """
        From a `usr_title` and (optional) `year`, search APIs for movie info
        """
        config = configparser.ConfigParser()
        config.read("config.ini")

        def __get_omdb(title: str, year: str) -> dict[str, str]:
            """
            Retrieve OMDb API response
            """
            omdb_req = requests.get(
                f"http://www.omdbapi.com/?apikey={config.get('API_KEYS', 'omdb')}&t={title}&y={year}",
                timeout=(3, 6),
            )

            if omdb_req.json().get("Response") == "False":
                kill()
            return omdb_req.json()

        def __get_tmdb(imdb_id: str) -> dict[str, str]:
            """
            Retrieve TMDb API response
            """
            tmdb_api = f"https://api.themoviedb.org/3/movie/{imdb_id}?language=en-US"

            headers = {
                "accept": "application/json",
                "Authorization": config.get("API_KEYS", "tmdb"),
            }
            tmdb_req = requests.get(
                tmdb_api,
                headers=headers,
                timeout=(3, 6),
            )

            return tmdb_req.json()

        def kill():
            """
            End program if search yields null.
            """
            import sys

            print("The search request failed.\n Please try adjusting the search terms.")
            sys.exit(0)

        omdb = __get_omdb(title, year)
        tmdb = __get_tmdb(omdb["imdbID"])
        merged: dict[str, Any] = {**omdb, **tmdb}

        if merged.get("imdbVotes") is None:
            kill()

        for k, v in merged.items():
            if v in ["N/A", 0]:
                merged[k] = None

            elif k in ["BoxOffice"]:
                merged[k] = int(v.replace("$", "").replace(",", ""))

            elif k in ["Actors", "Language", "Writer"]:
                if "," in v:
                    merged[k] = v.split(", ")
                else:
                    merged[k] = [v]

        return merged

    def output_std(self) -> dict[str, str]:
        return self.__dict__

    def output_md(self) -> str:
        bad_char = "%:/,.\\[]<>|*?\"'"
        save_title = "".join(
            [c for c in self.title if c not in bad_char]  # type: ignore
        ).replace(" ", "_")

        try:
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
                    if attribute is not None and attribute != 0:
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
            file.close()
            return f"Successfully wrote file to `./md/{save_title}.md`"
        except Exception:
            return f"Could not create markdown file.\nException: {Exception}"

    def db_add_movie(self):
        CONN = sqlite3.connect("movies.db")
        CURSOR = CONN.cursor()

        try:
            CURSOR.execute(
                "INSERT INTO movies (imdb_id, title, year, budget) VALUES (?, ?, ?, ? )",
                (self.imdb_id, self.title, self.year, self.budget),
            )

            CONN.commit()
            print(f"Added {self.title} successfully!")
        except Exception as e:
            print(f"Error: {e}.")
        finally:
            CONN.close()
