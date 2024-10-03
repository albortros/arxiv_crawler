"""
Usage: python fetch_arxiv.py config_filename
add -d for debugging (log beginning of each stage)
"""

import json
import os
import sys
from datetime import datetime

import feedparser
import pandas as pd

import database_manipulation as dbmanip


def _convert_time(val):
    """Changes the date-time string format"""
    date = datetime.strptime(val,'%Y-%m-%dT%H:%M:%SZ')
    return date.strftime("%Y-%m-%d %H:%M:%S")

def _remove_newlines(val):
    """Strips line breaks from the title string"""
    return val.replace('\n  ', ' ')

def _join_authors(val):
    """Makes a single string as the author list"""
    return ', '.join([val[i]['name'] for i in range(len(val))])

def query_arxiv_org(query_input):
    """Search for query items on arXiv and return the list of results"""

    # Construct elements of the query string sent to arxiv.org:
    # Base api query url
    base_url = 'https://export.arxiv.org/api/query?'
    # each search item
    with open(query_input) as file:
        search_keywords = file.readlines()
    # some options
    start = 0
    max_results = 50 # see arXiv API for max result limits
    sorting_order = '&sortBy=submittedDate&sortOrder=descending'

    result_list = []

    # search for the keywords/authors one by one
    for search_query in search_keywords:
        query = f'search_query={search_query.rstrip()}&start={start}&max_results={max_results}'

        d = feedparser.parse(base_url+query+sorting_order) # actual querying

        for entry in d.entries:
            dic_stored = {}
            dic_stored['id'] = entry.id.split('/')[-1].split('v')[0]
            dic_stored['author_list'] = _join_authors(entry.authors)
            dic_stored['title'] = _remove_newlines(entry.title)
            dic_stored['arxiv_primary_category'] = entry.arxiv_primary_category['term']
            dic_stored['published'] = _convert_time(entry.published)
            dic_stored['link'] = entry.link
            result_list.append(dic_stored)

    return result_list


def main():
    """
    Usage: python fetch_arxiv.py config_filename
    """

    debug_mode = bool('-d' in sys.argv)

    # read config file
    config_file = sys.argv[1]
    assert os.path.exists(config_file), "Config file not found."
    with open(config_file) as c_f:
        configs = json.load(c_f)

    if debug_mode:
        print('Beginning query: ', datetime.now())
    result_list = query_arxiv_org(configs['query_input'])
    if debug_mode:
        print('Query successful: ', datetime.now())

    # create a new empty data frame if failed to read an existing DB with the same name
    try:
        old_db = pd.read_pickle(configs['db_output'])
    except FileNotFoundError:
        old_db = pd.DataFrame()
    
    new_db = pd.DataFrame(result_list)
    updated_db = dbmanip.update_database(old_db, new_db)
    if debug_mode:
        print('Database updated: ', datetime.now())

    pd.to_pickle(updated_db, configs['db_output'])
    if debug_mode:
        print('pkl written: ', datetime.now())

    dbmanip.create_html(updated_db, configs['html_output'])
    print(f"Done writing {configs['html_output']}: ", datetime.now())


if __name__ == '__main__':
    main()
