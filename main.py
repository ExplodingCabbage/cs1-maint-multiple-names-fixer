from typing import Optional
import urllib.parse
import requests
import wikitextparser
from conf import api_key

def find_book(title: str, author_list_str: str) -> Optional[dict]:
    """
    Given a book's title and author list as it appears on Wikipedia, find it on Google Books, and
    return it as a dict. Returns None if not found on Google Books.
    """
    search_term = urllib.parse.quote_plus(title.replace(':', ''))
    q_api_key = urllib.parse.quote_plus(api_key)
    url = f'https://www.googleapis.com/books/v1/volumes?key={q_api_key}q=intitle:{search_term}'
    print(f"Searching: {url}")
    books = requests.get(url).json()['items']

    for book in books:
        if book['volumeInfo']['title'].lower() not in title.lower():
            continue
        if any(
            author.split()[-1] not in author_list_str for author in book['volumeInfo']['authors']
        ):
            continue
        return book


def rewrite_cite_book(cite: wikitextparser.Template) -> None:
    """
    Modifies the give `cite book` template in place to fix the author list, raising an exception
    if it fails.
    """
    print("Attempting to rewrite:", cite)
    title = cite.get_arg('title').value
    authors = cite.get_arg('author').value
    assert title, 'no title'
    assert authors, 'no authors'
    assert authors.count(',') > 1, 'no more than 1 comma'
    cite.del_arg('author')
    for argument in cite.arguments:
        arg_name = argument.name
        if arg_name.startswith('author') or arg_name.startswith('first') or arg_name.startswith('last'):
            raise Exception(f"Unexpected argument: {arg_name}")

    g_book = find_book(title, authors)
    for i, author in enumerate(g_book['volumeInfo']['authors'], 1):
        first, last = author.split()
        cite.set_arg(f"first{i}", first)
        cite.set_arg(f"last{i}", last)


def rewrite_bad_cites_on_page(wikitext: str) -> str:
    page = wikitextparser.parse(wikitext)
    book_cites = [template for template in page.templates if template.name.lower() == 'cite book']
    for cite in book_cites:
        author = cite.get_arg('author')
        if author and author.value.count(',') > 1:
            print('rewriting:', cite)
            rewrite_cite_book(cite)
    return page.string
