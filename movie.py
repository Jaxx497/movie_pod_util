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


@dataclass
class Movie:
    def __init__(self):
        search_str = input("Enter a title: ")
        payload = self.build_raw(search_str)
        self.build_mov(payload)

        # #########
        # DEBUGGING
        ###########
        import pprint as pp

        pp.pprint(payload)

    def build_mov(self, xe: dict[str, str]):
        """
        From a successful search, build Movie obj.
        """
        self.title = xe.get("Title")
        self.year = xe.get("Year")
        self.released = xe.get("Released")
        self.director = xe.get("Director")
        self.writer = xe.get("Writer")
        self.actors = xe.get("Actors")
        self.plot = xe.get("overview")
        self.age_rating = xe.get("Rated")
        self.genre = xe.get("Genre")
        self.budget = xe.get("budget")
        self.box_dom = xe.get("BoxOffice")
        self.box_for = None
        self.box_ww = xe.get("revenue")
        self.country = xe.get("Country")
        self.ratings = Ratings(xe.get("Ratings"), xe.get("imdbVotes"))
        self.imdb_id = xe.get("imdbID")
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

    def build_raw(self, usr_title: str) -> dict[str, str]:
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

            if "$" in str(v):
                merged[k] = int(v.replace("$", "").replace(",", ""))

            if k in ["Actors", "Country", "Genre", "Language", "Writer"]:
                if "," in v:
                    merged[k] = v.split(", ")

        return merged
