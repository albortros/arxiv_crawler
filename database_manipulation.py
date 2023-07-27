import codecs
import datetime
import os

import bs4
import pandas as pd


def update_database(df1, df2):
    df3 = pd.concat([df1, df2], sort=True)
    df3.drop_duplicates(subset=['id'], inplace=True, keep='last')  # could be done more efficiently?
    cols = ['title', 'author_list', 'published', 'arxiv_primary_category', 'id', 'link']
    df3 = df3[cols]  # reorder columns
    return df3.sort_values(by=['published'], ascending=False)


def create_html(df, filename): 
    """ add some arguments to get decent output, but shouldn't really be in here """
    pd.set_option('display.max_rows', len(df))
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_colwidth', None)
    df['link'] = df['link'].apply(_make_clickable)  # make hyperlinks clickable
    # df['author_list'] = df['author_list'].apply(_make_utf8) #set correct encoding for html
    df.to_html(filename, escape=False, index=False, justify='left')
    pd.reset_option('display.max_rows')
    pd.reset_option('display.max_columns')
    pd.reset_option('display.max_colwidth')

    with codecs.open(filename, 'r', encoding='utf8') as inf:
        txt = inf.read()
    soup = bs4.BeautifulSoup(txt, 'html5lib')

    metatag = soup.new_tag('meta')
    metatag.attrs['http-equiv'] = 'Content-Type'
    metatag.attrs['content'] = 'text/html; charset=utf-8'
    soup.head.append(metatag)

    mathjaxtag2 = soup.new_tag('script')
    mathjaxtag2.attrs['type'] = 'text/javascript'
    mathjaxtag2.attrs['src'] = 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.0/MathJax.js?config=TeX-AMS-MML_HTMLorMML'
    soup.head.insert(1, mathjaxtag2)
    mathjaxtag1 = soup.new_tag('script')
    mathjaxtag1.attrs['type'] = 'text/x-mathjax-config'
    mathjaxtag1.append(r"MathJax.Hub.Config({tex2jax: {inlineMath: [['$','$'], ['\\(','\\)']]}});")
    soup.head.insert(1, mathjaxtag1)

    csstag = soup.new_tag('link')
    csstag.attrs['rel'] = "stylesheet"
    csstag.attrs['href'] = "/static/table_style.css"
    soup.head.append(csstag)

    titletag = soup.new_tag('title')
    titletag.string = 'arXiv crawler'
    soup.head.append(titletag)

    if os.path.isfile('favicon_input.html'):
        with open('favicon_input.html') as f:
            linktags = bs4.BeautifulSoup(f, 'html5lib')
        for l in linktags.head.children:
            soup.head.append(l)

    soup.body.insert(0, f'Last updated {datetime.datetime.now()}')

    with codecs.open(filename, "w", encoding='utf8') as outf:
        outf.write(str(soup))


def _make_clickable(val):
    # target _blank to open new window
    return f'<a target="_blank" href="{val}">{val}</a>'
