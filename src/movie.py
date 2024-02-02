import sys
import requests
import sqlite3
from src.creds import BEARER
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
        self.db_append_mov()

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
        From a `usr_title`, search APIs for movie info
        """

        omdb_req = requests.get(
            f"http://www.omdbapi.com/?apikey=8648ed18&t={title}&y={year}",
            timeout=(3, 6),
        )

        omdb_res = omdb_req.json()

        if omdb_res.get("response") == "false":
            print("The search request failed.\n Please try adjusting the search terms.")
            sys.exit(0)

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

        if merged.get("imdbVotes") is None:
            print("The search request failed.\nPlease try adjusting the search terms.")
            sys.exit(0)

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

    def db_append_mov(self):
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
