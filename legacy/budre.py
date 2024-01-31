import json


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    TEMP = "\u001b[38;2;145;231;255m"


def main():
    with open("budgets.json", "r") as f:
        raw_data = json.load(f)

        sorted_list = {
            title: budget
            for title, budget in sorted(raw_data.items(), key=lambda item: item[1])
        }

        for title, budget in sorted_list.items():
            title = title.replace("_", " ")
            print(f"  {bcolors.OKCYAN}{title[0:35]:<40}{bcolors.WARNING}${budget:>12,}")
        print()


if __name__ == "__main__":
    main()
