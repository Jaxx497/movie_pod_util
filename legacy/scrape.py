import json
import pprint
import requests

from src.creds import BEARER

strD = dict[str, str]


def main():
    title = input("Enter movie title to rip: ")

    raw_resp = build_raw(title)
    payload = get_info(raw_resp)
    pprint.pprint(payload)
    print()
    make_template_norg(payload)
    make_template_md(payload)


def make_template_norg(payload) -> None:
    title = payload.get("Title")
    year = payload.get("Year")
    released = payload.get("Released")
    country = payload.get("Country")
    budget = payload.get("Budget")

    bad_char = "%:/,.\\[]<>|*?\"'"
    save_title = "".join([c for c in title if c not in bad_char]).replace(" ", "_")

    with open(f"./norg/{save_title}.norg", "w", encoding="utf-8") as file:
        file.write(
            f"* {{https://imdb.com/title/{payload.get('imdb_id')}}}[*{title}* ({year})]\n"
        )
        file.write("\n")
        file.write("*** *General*\n")
        file.write(f"    - /Released/: {released} ({country})\n")
        file.write(f"    - /Runtime/: {payload.get('Runtime')}\n")
        file.write(f"    - /Genre/: {payload.get('Genre')}\n")
        file.write(f"    - /Director/: {payload.get('Director')}\n")

        if len(payload.get("Writer")) > 1:
            file.write("    - /Writers/:\n")
            for writer in payload.get("Writer"):
                file.write(f"\t-- {writer}\n")
        else:
            file.write(f"    - /Writer/: {payload.get('Writer')[0]}\n")

        file.write("\n")
        file.write("*** *Finances*\n")
        file.write(f"    - /Budget/: {budget}\n")
        file.write(f"    - /Box Office (D)/: {payload.get('Box_Dom')}\n")
        file.write(f"    - /Box Office (F)/: {payload.get('Box_For')}\n")
        file.write(f"    - /Box Office (*)/: {payload.get('Box_WW')}\n")

        file.write("\n")

        file.write("*** *Ratings* \n")
        for agency, score in payload.get("Ratings").items():
            if agency == "IMDB":
                file.write(
                    f"    - {agency}: {score} ({payload.get('imdb_Votes')})\n"
                )  # noqa
            else:
                file.write(f"    - {agency}: {score}\n")


def make_template_md(payload):
    title = payload.get("Title")
    year = payload.get("Year")
    released = payload.get("Released")
    country = payload.get("Country")
    budget = payload.get("Budget")

    bad_char = "%:/,.\\[]<>|*?\"'"
    save_title = "".join([c for c in title if c not in bad_char]).replace(" ", "_")

    with open(f"./md/{save_title}.md", "w", encoding="utf-8") as file:
        file.write(
            f"# [*{title}* ({year})](https://imdb.com/title/{payload.get('imdb_id')})\n"
        )
        file.write("\n")
        file.write("### *General*\n")
        file.write(f"- *Released*: {released} ({country})\n")
        file.write(f"- *Runtime*: {payload.get('Runtime')}\n")
        file.write(f"- *Genre*: {payload.get('Genre')}\n")
        file.write(f"- *Director*: {payload.get('Director')}\n")

        if len(payload.get("Writer")) > 1:
            file.write("- *Writers*:\n")
            for writer in payload.get("Writer"):
                file.write(f"\t- {writer}\n")
        else:
            file.write(f"    - *Writer*: {payload.get('Writer')[0]}\n")

        file.write("\n")
        file.write("### *Finances*\n")
        file.write(f"- *Budget*: {budget}\n")
        file.write(f"- *Box Office (D)*: {payload.get('Box_Dom')}\n")
        file.write(f"- *Box Office (F)*: {payload.get('Box_For')}\n")
        file.write(f"- *Box Office (\\*)*: {payload.get('Box_WW')}\n")

        file.write("\n")

        file.write("### *Ratings* \n")
        for agency, score in payload.get("Ratings").items():
            if agency == "IMDB":
                file.write(
                    f"- {agency}: {score} ({payload.get('imdb_Votes')})\n"
                )  # noqa
            else:
                file.write(f"- {agency}: {score}\n")


def get_info(raw: strD) -> strD:
    raw_ratings: strD = raw.get("Ratings")
    ratings = {}
    try:
        for rating in raw_ratings:
            ratings[rating.get("Source")] = rating.get("Value")
        ratings["IMDB"] = ratings.pop("Internet Movie Database")
    except TypeError:
        pass

    if raw.get("budget"):
        log_budget(raw.get("title"), raw.get("budget"))

    glob = {
        "Title": raw.get("title"),
        "Year": raw.get("Year"),
        "Released": raw.get("Released"),
        "Director": raw.get("Director"),
        "Writer": str(raw.get("Writer")).split(", "),
        "Runtime": raw.get("runtime"),
        "Genre": raw.get("Genre"),
        "Budget": raw.get("budget"),
        "Box_Dom": raw.get("BoxOffice"),
        "Box_For": None,
        "Box_WW": raw.get("revenue"),
        "Country": raw.get("Country"),
        "Ratings": ratings,
        "imdb_id": raw.get("imdbID"),
        "imdb_Votes": raw.get("imdbVotes"),
    }

    for key, val in glob.items():
        # if val == "N/A" or val == 0:
        if val in ["N/A", 0]:
            glob[key] = None

    if glob.get("Runtime") is not None:
        glob["Runtime"] = min_to_hr(int(raw.get("runtime")))

    for i in [("budget", "Budget"), ("revenue", "Box_WW")]:
        if raw.get(i[0]) is not None and raw.get(i[0]) != 0:
            glob[i[1]] = f"${glob.get(i[1]):,}"

    if "$" in str(glob.get("Box_WW")) and "$" in str(glob.get("Box_Dom")):
        world = int(glob.get("Box_WW")[1:].replace(",", ""))  # type: ignore
        dom = int(glob.get("Box_Dom")[1:].replace(",", ""))  # type: ignore

        glob["Box_For"] = f"${world - dom:,}"

    return glob


# HAVE TO FIX THIS
def log_budget(title, budget):
    """
    Update Budgets.json
    """
    with open("budgets.json", "r") as file:
        budget_dict = json.load(file)

    bad_char = "%:/,.\\[]<>|*?\"'"
    title = "".join([c for c in title if c not in bad_char]).replace(" ", "_")

    budget_dict.update({title: budget})

    with open("budgets.json", "w+") as file:
        json.dump(budget_dict, file, indent=4)


def build_raw(raw_title: str) -> dict[str, str]:
    """
    Make sure both APIs produce results provided a search value
    """

    omdb_res = None
    if "|" in raw_title:
        title, year = raw_title.split(" | ", 1)
        print(year)
        omdb_req = requests.get(
            f"http://www.omdbapi.com/?apikey=8648ed18&t={title}&y={year}",
            timeout=(3, 6),
        )
        omdb_res = omdb_req.json()
    else:
        omdb_req = requests.get(
            f"http://www.omdbapi.com/?apikey=8648ed18&t={raw_title}", timeout=(3, 6)
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


def min_to_hr(mins):
    hrs = 0
    while mins > 60:
        hrs += 1
        mins -= 60

    return f"{hrs}h {mins}min"


if __name__ == "__main__":
    main()
