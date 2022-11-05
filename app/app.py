import requests
from os.path import exists
from bs4 import BeautifulSoup
import json
import re


def get_search_url(page_num):
    search_url = f'{library_url_prefix}{page_num}__Orightresult__U__X0?{query_string}'

    return search_url


def get_library_url_prefix():
    if exists("library_url_prefix.txt"):
        library_file = open("library_url_prefix.txt", "r")
        library_url_prefix = library_file.read()
    else:
        library_url_prefix = "FILE NOT FOUND"

    return library_url_prefix


def get_games(page):
    soup = BeautifulSoup(page, features="html.parser")
    games = soup.find_all(
        "div", {"id":  re.compile(r'resultRecord-.*')})
    game_dict = {}

    for game in games:
        game_title = get_title(game)
        game_status = get_status(game)
        game_dict[game_title] = game_status

    return game_dict


def get_title(game):
    game_title = game.find(
        "span", {"class": "title"})
    game_title = game_title.text.strip().upper()

    return game_title


def get_status(game):
    game_status = game.find(
        "span", {"class": re.compile(r'item.*Available')})

    if game_status == None:
        game_status = "N/A"
    else:
        game_status = game_status.text.strip().upper()

    return game_status


def get_additional_results(num_pages):
    for page_num in range(num_pages):
        current_page_url = get_search_url(str(page_num))
        current_page = requests.get(current_page_url).text
        additional_results = get_games(current_page)

    return additional_results


def get_num_pages(page):
    soup = BeautifulSoup(page, features="html.parser")
    page_nums = soup.find_all('a', {'id': re.compile(r'searchPageLink_[0-9]')})
    num_pages = 0

    for page_num in page_nums:
        page_num = page_num.contents[0].lower()
        if page_num != "next":
            num_pages = int(page_num)

    return num_pages


def read_games():
    if exists("games.json"):
        with open('games.json', 'r') as openfile:
            games_dict = json.load(openfile)
    else:
        games_dict = {}

    return games_dict


def save_games(games_dict):
    games_string = json.dumps(games_dict)
    with open("games.json", "w") as outfile:
        outfile.write(games_string)


def save_changelog(changelog):
    changelog_string = json.dumps(changelog)
    with open("changelog.json", "w") as outfile:
        outfile.write(changelog_string)


library_url_prefix = get_library_url_prefix()

if library_url_prefix != "FILE NOT FOUND":
    query_string = "lang=eng&suite=gold"
    first_page_url = get_search_url("0")
    first_page = requests.get(first_page_url).text
    games_dict = get_games(first_page)

    num_pages = get_num_pages(first_page)
    additional_results = get_additional_results(num_pages)
    games_dict = games_dict | additional_results

    old_games_dict = read_games()
    new_games = {}

    for game, status in games_dict.items():
        if game in old_games_dict:
            if status != old_games_dict[game] and status == "AVAILABLE":
                new_games[game] = status

    save_games(games_dict)
    save_changelog(new_games)
else:
    print("No library_url_prefix.txt file found. Please add this file with the proper URL prefix and try running again.")
