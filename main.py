from creds import BEARER
from dataclasses import dataclass
from os import walk
import requests


@dataclass
class InfoBuild:
    def __init__(self):
        something = input("Enter a title: ")
        x = build_raw(something)
        print(x)

        def build_raw(usr_title: str) -> dict[str, str]:
            omdb_res = None

            if "|" in usr_title:
                title, year = usr_title.split(" | ", 1)
                print(year)
                omdb_req = requests.get(
                    f"http://www.omdbapi.com/?apikey=8648ed18&t={title}&y={year}",
                    timeout=(3, 6),
                )
                omdb_res = omdb_req.json()
            else:
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

            return {**omdb_res, **tmdb_res}


@dataclass
class Ratings:
    imdb: str = ""
    imdb_v: str = ""
    rt: str = ""
    mc: str = ""


@dataclass
class Movie:
    title: str
    year: int
    released: str
    director: str
    writer: str
    runtime: str
    genre: str
    budget: str
    box_dom: str
    box_for: str
    box_ww: str
    country: str
    ratings: Ratings


def main():
    InfoBuild()


if __name__ == "__main__":
    main()
