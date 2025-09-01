""" 
Functions for fetching & parsing the Maya cmds documentation index
"""

import urllib.request
import typing
import bs4

from bs4 import BeautifulSoup


class CmdsCommandPage(typing.NamedTuple):
    command: str
    url: str


def get_docs_url(version: int, page: str) -> str:
    if not page.lower().endswith('.html'):
        page += '.html'

    return f"https://help.autodesk.com/cloudhelp/{version}/ENU/Maya-Tech-Docs/CommandsPython/{page}"


def get_index_url(version: int) -> str:
    return get_docs_url(version, "index_all")


def get_index_html(version: int) -> str:
    """ 
    Get the raw HTML of the index page
    """
    url = get_index_url(version)
    with urllib.request.urlopen(url) as response:
        return response.read().decode('utf-8')


def get_commands(version: int) -> list[CmdsCommandPage]:
    """
    Fetches and parses the Maya cmds documentation index for the given version.
    Returns a list of command names & urls.
    """
    html = get_index_html(version)

    commands: list[CmdsCommandPage] = []

    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all('a'):
        if not isinstance(a, bs4.element.Tag):
            raise TypeError(f"Expected a Tag element, got {type(a)}")

        command = a.get_text(strip=True)

        relative_url = a.get('href')
        if not isinstance(relative_url, str):
            raise TypeError(f"Expected a string, got {type(relative_url)}")

        absolute_url = get_docs_url(version, relative_url)

        commands.append(CmdsCommandPage(command=command, url=absolute_url))

    return commands
