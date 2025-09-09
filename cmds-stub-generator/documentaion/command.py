"""
Parse command documentation
"""

import urllib.request
import tempfile
import hashlib
import typing
import bs4
import os

from dataclasses import dataclass
from bs4 import BeautifulSoup


class Flag(typing.NamedTuple):
    name_long: str
    name_short: str
    arg_type: str
    description: str

    query: bool
    edit: bool
    create: bool
    multi_use: bool


class DocsString(typing.NamedTuple):
    undoable: bool
    queryable: bool
    editable: bool


@dataclass
class CommandDocumentation:
    docstring: DocsString
    flags: tuple[Flag, ...]
    examples: str | None

    obsolete: bool = False
    obsolete_message: str | None = None

    def get_query_flags(self) -> list[Flag]:
        return [flag for flag in self.flags if flag.query]

    def get_create_flags(self) -> list[Flag]:
        return [flag for flag in self.flags if flag.create]

    def get_edit_flags(self) -> list[Flag]:
        return [flag for flag in self.flags if flag.edit]


def get_html(url: str, use_cache: bool = True) -> str:  # TODO: Flip use_cache to false, this is only for initial development
    cache_path: None | str = None
    if use_cache:
        cache_path = os.path.join(tempfile.gettempdir(), "cmds_stub_generator_cache", hashlib.md5(url.encode()).hexdigest() + ".html")
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                return f.read()

    with urllib.request.urlopen(url) as response:
        text = response.read()

        if cache_path:
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, "wb") as f:
                f.write(text)

        return text


def parse_docstring(soup: BeautifulSoup) -> DocsString:
    synopsis_tag = soup.find("p", id="synopsis")
    hflags_tag = soup.find("a", {"name": "hFlags"})
    hflags_h2 = hflags_tag.find_parent("h2") if hflags_tag else None

    # Collect all elements between synopsis_tag and hflags_tag
    doc_parts = []
    current = synopsis_tag
    while current and current != hflags_h2:
        current = current.find_next_sibling()
        if current and current != hflags_h2:
            doc_parts.append(str(current))

    if not doc_parts:
        return DocsString(False, False, False)

    # doc_html = "<br/>".join(doc_parts)
    # doc_text = BeautifulSoup(doc_html, "html.parser").get_text(separator=" ", strip=True)

    undoable_queryable_editable_doc = doc_parts[0]  # '<p>aaf2fcp is <b>NOT undoable</b>, <b>NOT queryable</b>, and <b>NOT editable</b>.</p>'

    # Check if command is undoable, queryable & editable
    undoable = "NOT undoable" not in undoable_queryable_editable_doc
    queryable = "NOT queryable" not in undoable_queryable_editable_doc
    editable = "NOT editable" not in undoable_queryable_editable_doc

    return DocsString(
        undoable,
        queryable,
        editable
    )


def extract_flags(soup: BeautifulSoup) -> typing.Generator[Flag, None, None]:
    for tr_flag in soup.find_all("tr", bgcolor="#EEEEEE"):
        if not isinstance(tr_flag, bs4.Tag):
            raise ValueError(f"Expected a Tag element got {type(tr_flag)}")

        children = tr_flag.find_all("td", recursive=False)
        if not len(children) == 3:
            raise ValueError(f"Expected 3 children elements but got {len(children)}\n{tr_flag}")

        td_name, td_type, td_property = children

        if not isinstance(td_name, bs4.Tag) or not isinstance(td_property, bs4.Tag):
            raise TypeError(f"Expected a Tag, got {type(td_name)}")

        # Name
        b_name_long, b_name_short = td_name.find_all("b", recursive=True)
        name_long = b_name_long.get_text(strip=True)
        name_short = b_name_short.get_text(strip=True)

        # Argument Types
        arg_type = td_type.get_text(strip=True)

        # Properties
        create = td_property.find("img", alt="create") is not None
        query = td_property.find("img", alt="query") is not None
        edit = td_property.find("img", alt="edit") is not None
        multi_use = td_property.find("img", alt="multiuse") is not None

        # Description
        description = ""
        if tr_flag.next_sibling is not None:
            if tr_desc := tr_flag.next_sibling.next_sibling:
                description = tr_desc.get_text(strip=True)

        yield Flag(
            name_long,
            name_short,
            arg_type,
            description,
            query,
            edit,
            create,
            multi_use
        )


def extract_examples(soup: BeautifulSoup) -> str | None:
    a_example_header = soup.find("a", {"name": "hExamples"})
    if a_example_header:
        pre_examples = a_example_header.find_next("pre")
        if pre_examples:
            return pre_examples.get_text(strip=True)

    return None


def is_obsolete(soup: BeautifulSoup) -> bool:
    """ 
    Check if the command is obsolete 
    """
    # Look in the header for the word Obsolete
    h1_tag = soup.find("h1")
    return h1_tag is not None and "Obsolete" in h1_tag.get_text()


def get_obsolete_message(soup: BeautifulSoup) -> str:
    """
    Get the obsolete message for the command
    """
    # The obsolete message text is placed directly in the body tag
    body = soup.find("body")
    if isinstance(body, bs4.Tag):
        texts: list[str] = []
        for child in body.children:
            # Skip banner and toolbar
            if isinstance(child, bs4.element.Tag):
                if child.get("id") == "banner":
                    continue
                element_class = child.get("class") or []
                if "toolbar" in element_class:
                    continue

            if isinstance(child, bs4.element.Tag):
                texts.append(child.get_text(separator=" ", strip=True))
            elif isinstance(child, str) and child.strip():
                texts.append(child.strip())

        full_text = " ".join(texts).strip()
        if full_text:
            return full_text

    return "This command is obsolete."


def parse_html(html: str) -> CommandDocumentation:
    soup = BeautifulSoup(html, "html.parser")

    obsolete = is_obsolete(soup)
    obsolete_message = get_obsolete_message(soup) if obsolete else None

    return CommandDocumentation(
        parse_docstring(soup),
        flags=tuple(extract_flags(soup)),
        examples=extract_examples(soup),
        obsolete=obsolete,
        obsolete_message=obsolete_message
    )


def get_info(url: str) -> CommandDocumentation:
    html = get_html(url)
    return parse_html(html)
