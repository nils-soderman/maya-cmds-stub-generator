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


class ReturnValue(typing.NamedTuple):
    type: str
    description: str


@dataclass
class Flag:
    name_long: str
    name_short: str
    arg_type: str | None
    description: str

    query: bool
    edit: bool
    create: bool
    multi_use: bool

    def is_query_only(self) -> bool:
        return self.query and not self.edit and not self.create


@dataclass
class CommandDocumentation:
    undoable: bool
    queryable: bool
    editable: bool

    description: str
    returns: list[ReturnValue]

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


def get_command_description(soup: BeautifulSoup) -> str:
    """
    """
    body = soup.find("body")
    if isinstance(body, bs4.Tag):
        return_header = body.find("a", {"name": "hReturn"})
        synopsis_tag = soup.find("p", id="synopsis")
        return_header_parent = return_header.find_parent() if isinstance(return_header, bs4.Tag) else None
        if not return_header_parent:
            return ""

        synopsis_found = False
        return_string = ""
        num_found_tags = 0
        for child in body.children:
            if child == return_header_parent:
                break

            if child == synopsis_tag:
                synopsis_found = True
                continue

            if not synopsis_found:
                continue

            if isinstance(child, bs4.element.Tag):
                num_found_tags += 1
                if num_found_tags == 1:
                    continue
                text = child.get_text(separator=" ", strip=True)
                if child.name == "i":
                    if text.startswith("*") or text.endswith("*"):
                        text = f"<i>{text}</i>"
                    else:
                        text = f"*{text}*"
                elif child.name == "b":
                    if text.startswith("*") or text.endswith("*"):
                        text = f"<b>{text}</b>"
                    else:
                        text = f"**{text}**"
                elif child.name == "p":
                    text = f"{text}\n"
                elif child.name == "br":
                    text = "\n"
                return_string += " " + text
            elif isinstance(child, str) and child.strip():
                return_string += " " + child.replace("\n", " ").strip()
        
        return_string = return_string.replace("\n ", "\n")
        return_string = return_string.replace(" \n", "\n")

        return return_string.strip()

    return ""


def get_return_values(soup: BeautifulSoup) -> list[ReturnValue]:
    return_a = soup.find("a", {"name": "hReturn"})
    if isinstance(return_a, bs4.Tag):
        return_h2 = return_a.find_parent()
        if not isinstance(return_h2, bs4.Tag):
            raise ValueError("Could not find return header")

        return_table = return_h2.find_next_sibling()
        # This table has 2 columns, type and description
        if not isinstance(return_table, bs4.Tag):
            raise ValueError("Could not find return value")

        # Either a table or single paragraph
        if return_table.name == "p":
            return [ReturnValue(return_table.get_text(strip=True), "")]
        elif return_table.name == "table":
            return_values: list[ReturnValue] = []
            for tr in return_table.find_all("tr"):
                if not isinstance(tr, bs4.Tag):
                    raise ValueError(f"Expected a Tag element got {type(tr)}")

                tds = tr.find_all("td", recursive=False)
                if len(tds) != 2:
                    continue

                type_td, desc_td = tds
                type_text = type_td.get_text("", strip=True)
                desc_text = desc_td.get_text(strip=True)
                return_values.append(ReturnValue(type_text, desc_text))

            return return_values
        else:
            raise ValueError(f"Expected a paragraph or table, got {return_table.name}")

    return []


def get_undoable_queryable_editable(soup: BeautifulSoup) -> tuple[bool, bool, bool]:
    synopsis_tag = soup.find("p", id="synopsis")

    # Check if command is undoable, queryable & editable
    undoable_queryable_editable_doc = ""  # '<p>aaf2fcp is <b>NOT undoable</b>, <b>NOT queryable</b>, and <b>NOT editable</b>.</p>'
    if isinstance(synopsis_tag, bs4.Tag):
        if next_sibling := synopsis_tag.find_next_sibling():
            undoable_queryable_editable_doc = str(next_sibling.get_text(separator=" ", strip=True))

    undoable = "NOT undoable" not in undoable_queryable_editable_doc
    queryable = "NOT queryable" not in undoable_queryable_editable_doc
    editable = "NOT editable" not in undoable_queryable_editable_doc

    return undoable, queryable, editable


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
        if not arg_type:
            arg_type = None

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

    undoable, queryable, editable = get_undoable_queryable_editable(soup)

    return CommandDocumentation(
        undoable=undoable,
        queryable=queryable,
        editable=editable,
        description=get_command_description(soup),
        returns=get_return_values(soup),
        flags=tuple(extract_flags(soup)),
        examples=extract_examples(soup),
        obsolete=obsolete,
        obsolete_message=obsolete_message,
    )


def get_info(url: str) -> CommandDocumentation:
    html = get_html(url)
    return parse_html(html)
