import requests
from os.path import exists
from bs4 import BeautifulSoup
import json
import re

# Application to search for the availability of items at the Cuyahoga County Public Library via a search term.

search_term = "ps5"
library_url_prefix = f'https://encore.cuyahoga.lib.oh.us/iii/encore/search/C__S{search_term}__P'
query_string = "lang=eng&suite=gold"
changelog_filepath = "changelog.json"
items_filepath = "items.json"


def get_search_url(page_num):
    search_url = f'{library_url_prefix}{page_num}__Orightresult__U__X0?{query_string}'

    return search_url


def get_items(page):
    soup = BeautifulSoup(page, features="html.parser")
    items = soup.find_all(
        "div", {"id":  re.compile(r'resultRecord-.*')})
    item_dict = {}

    for item in items:
        item_title = get_title(item)
        item_status = get_status(item)
        if item_status == "AVAILABLE":
            item_dict[item_title] = item_status

    return item_dict


def get_title(item):
    item_title = item.find("span", {"class": "title"})
    item_title = item_title.text.strip().upper()

    return item_title


def get_status(item):
    item_status = item.find(
        "span", {"class": re.compile(r'item.*Available')})

    if item_status == None:
        item_status = "N/A"
    else:
        item_status = item_status.text.strip().upper()

    return item_status


def get_additional_results(num_pages):
    additional_results = {}
    for page_num in range(1, num_pages):
        current_page_url = get_search_url(str(page_num))
        current_page = requests.get(current_page_url).text
        additional_results = additional_results | get_items(current_page)

    return additional_results


def get_num_pages(page):
    soup = BeautifulSoup(page, features="html.parser")
    page_nums = soup.find_all("a", {"id": re.compile(r'searchPageLink_[0-9]')})
    num_pages = 0

    for page_num in page_nums:
        page_num = page_num.contents[0].lower()
        if page_num != "next":
            num_pages = int(page_num)

    return num_pages


def get_new_items(items_dict):
    old_items_dict = read_items()
    new_items = {}

    for item, status in items_dict.items():
        if item not in old_items_dict:
            new_items[item] = status

    return new_items


def read_items():
    if exists(items_filepath):
        with open(items_filepath, "r") as openfile:
            items_dict = json.load(openfile)
    else:
        items_dict = {}

    return items_dict


def save_file(items_json, filename):
    items_string = json.dumps(items_json)
    with open(filename, "w") as outfile:
        outfile.write(items_string)


def main():
    first_page_url = get_search_url("0")
    first_page = requests.get(first_page_url).text
    num_pages = get_num_pages(first_page)
    items_dict = get_items(first_page)
    additional_results = get_additional_results(num_pages)
    items_dict = items_dict | additional_results
    new_items = get_new_items(items_dict)
    save_file(items_dict, items_filepath)
    save_file(new_items, changelog_filepath)


if __name__ == "__main__":
    main()
