import maya.cmds

import re

import logging
import typing

from .. import resources

logger = logging.getLogger(__name__)

PATTERN_SYNOPSIS_PREFIX = re.compile(r"Synopsis: \w+(?: \[flags\])?")
PATTRERN_BRACKETS = re.compile(r"\[([A-Za-z. ]+)\]")
PATTERN_PARENS = re.compile(r"\([^)]*\)")


TYPE_MAP = resources.load("type_conversion.jsonc")
BUILTIN_TYPES = {"str", "int", "float", "bool"}


class Argument(typing.NamedTuple):
    name: str
    argument_type: str | None = None
    default: str | None = None


def _type_lookup(type_str: str) -> str | None:
    if type_str in BUILTIN_TYPES:
        return type_str

    return TYPE_MAP.get(type_str)


def default_arg() -> list[Argument]:
    return [Argument("*args")]


def get_commands() -> list[str]:
    return [x for x in dir(maya.cmds) if not x.startswith("_") and callable(getattr(maya.cmds, x))]


def get_positional_args(command: str) -> list[Argument]:
    try:
        help_str: str = maya.cmds.help(command)
    except RuntimeError as e:
        return default_arg()

    help_lines = help_str.splitlines()

    synopsis = next((x for x in help_lines if x.startswith("Synopsis:")), None)
    if not synopsis:
        return default_arg()  # Could not determine, allow any args

    # Remove the prefix from the synopsis:
    arg_str = PATTERN_SYNOPSIS_PREFIX.sub("", synopsis).strip().lower()
    if not arg_str:
        return []  # No positional args

    # render command currently contains a comment inside parens, remove it
    if "(" in arg_str:
        logger.warning(f"Removing comment in parentheses from arg type for command '{command}': \"{arg_str}\"")
        arg_str = PATTERN_PARENS.sub("", arg_str).strip()

    if "[...]" in arg_str:  # Used in setAttr as Name[...], where it takes name then Any
        arg_str = arg_str.replace("[...]", " any...")

    # Args may or may not be encapsulated in brackets: [String], [Int...]
    # From what I could find the brackets seems to have no affect on the meaning
    # Remove the brackets for easier parsing, some are nested so repeat a few times
    arg_str_raw = arg_str
    for _ in range(5):
        if "[" not in arg_str:
            break
        arg_str = PATTRERN_BRACKETS.sub(r"\1", arg_str).strip()
    else:
        logger.warning(f"Could not fully remove brackets from arg string for command '{command}': {arg_str_raw}")

    if " " not in arg_str:  # Single type
        # Single argument, e.g. 'String' or 'Int'
        if valid_type := _type_lookup(arg_str):
            return [Argument("arg", valid_type, default="...")]

        # Single argument or list of arguments, e.g. 'String...' or 'Int...'
        if arg_str.endswith("..."):
            if valid_type := _type_lookup(arg_str[0:-3]):
                if valid_type != "Any":
                    valid_type = f"Sequence[{valid_type}]|{valid_type}"
                return [Argument("*args", valid_type)]

    else:  # Multiple type
        args = arg_str.split()

        if "..." not in arg_str:
            # Single types only e.g. String Int Float
            # Make each one be its own argument
            arguments: list[Argument] = []
            for i, arg in enumerate(args):
                valid_type = _type_lookup(arg)
                if not valid_type:
                    logger.warning(f"Could not determine positional arg type for command '{command}': unknown type '{arg}'")
                arguments.append(Argument(f"arg{i+1}", valid_type, default="..."))

            return arguments

        else:  # '...' in arg_str:
            listable_types = set()
            single_types = set()

            for arg in args:
                valid_type = _type_lookup(arg.strip("."))
                if not valid_type:
                    logger.warning(f"Could not determine positional arg type for command '{command}': unknown type '{arg}'")
                    return default_arg()

                if arg.endswith("..."):
                    listable_types.add(valid_type)
                else:
                    single_types.add(valid_type)

            arguments: list[Argument] = []
            for i, arg_type in enumerate(single_types):
                arguments.append(Argument(f"arg{i+1}", arg_type, default="..."))
            if listable_types:
                listable_type = "|".join(listable_types)
                if listable_type != "Any":
                    listable_type = f"Sequence[{listable_type}]|{listable_type}"
                arguments.append(Argument("*args", listable_type))

            return arguments

    logger.warning(f"Could not determine positional args for command '{command}': {arg_str}")

    return default_arg()
