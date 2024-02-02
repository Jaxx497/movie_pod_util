from src.movie import Movie


class Template:
    movie: Movie

    def __init__(self, movie) -> None:
        self.movie = movie
        pass

    def new_md(self) -> None:
        bad_char = "%:/,.\\[]<>|*?\"'"
        save_title = "".join(
            [c for c in self.movie.title if c not in bad_char]  # type: ignore
        ).replace(" ", "_")

        try:
            with open(f"./md/{save_title}.md", "w", encoding="utf-8") as file:
                file.write(
                    f"# [*{self.movie.title}* ({self.movie.year})](https://imdb.com/title/{self.movie.imdb_id})\n"
                )
                file.write(f"\n> {self.movie.plot}")
                file.write("\n")
                file.write("### *General*\n")
                file.write(
                    f"- *Released*: {self.movie.released} ({self.movie.country})\n"
                )
                file.write(f"- *Awards*: {self.movie.awards}\n")
                file.write(f"- *Runtime*: {self.movie.runtime}\n")
                file.write(f"- *Genre*: {self.movie.genre }\n")
                file.write(f"- *Director*: {self.movie.director}\n")

                if self.movie.writer:
                    if len(self.movie.writer) > 1:
                        file.write("- *Writers*:\n")
                        for writer in self.movie.writer:
                            file.write(f"\t- {writer}\n")
                    else:
                        file.write(f"- *Writer*: {self.movie.writer[0]}\n")

                if self.movie.actors:
                    file.write("- *Actors*:\n")
                    for actor in self.movie.actors:
                        file.write(f"\t- {actor}\n")

                file.write("\n### *Finances*\n")
                for attribute, title in [
                    (self.movie.budget, "Budget"),
                    (self.movie.box_dom, "Box Office (D)"),
                    (self.movie.box_for, "Box Office (F)"),
                    (self.movie.box_ww, "Box Office (\\*)"),
                ]:
                    if attribute is not None and attribute != 0:
                        file.write(f"- *{title}*: ${attribute:,}\n")

                file.write("\n### *Ratings* \n")
                for attribute, agency in [
                    (self.movie.ratings.mc, "MetaCritic"),
                    (self.movie.ratings.rt, "Rotten Tomatoes"),
                    (self.movie.ratings.imdb, "IMDb"),
                ]:
                    if attribute is None:
                        continue
                    elif agency == "IMDb":
                        file.write(
                            f"- {agency}: {attribute} ({self.movie.ratings.imdb_v})\n"
                        )  # noqa
                    else:
                        file.write(f"- {agency}: {attribute}\n")
            file.close()
            print(f"Successfully wrote file to `./md/{save_title}.md`")
        except:
            print("Could not create markdown file.")
