import maya.cmds

import re

import logging
import typing

logger = logging.getLogger(__name__)

PATTERN_SYNOPSIS_PREFIX = re.compile(r"Synopsis: \w+(?: \[flags\])?")
PATTRERN_BRACKETS = re.compile(r"\[([A-Za-z. ]+)\]")
PATTERN_PARENS = re.compile(r"\([^)]*\)")

TYPE_MAP = {
    "String": "str",
    "Int": "int",
    "Float": "float",
    "on|off": "bool",
    "Script": "str|__t.Callable",
    "Name": "str",
    "Time": "str|float",
    "Angle": "float|str",
    "Length": "float|str",
}


class Argument(typing.NamedTuple):
    name: str
    argument_type: str | None = None
    default: str | None = None


def default_arg() -> list[Argument]:
    return [Argument("*args")]


def get_commands() -> set[str]:
    return set(dir(maya.cmds))


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
    arg_str = PATTERN_SYNOPSIS_PREFIX.sub("", synopsis).strip()
    if not arg_str:
        return []  # No positional args

    # render command currently contains a comment inside parens, remove it
    if "(" in arg_str:
        logger.warning(f"Removing comment in parentheses from arg type for command '{command}': \"{arg_str}\"")
        arg_str = PATTERN_PARENS.sub("", arg_str).strip()

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
        if arg_str in TYPE_MAP:
            return [Argument("arg", TYPE_MAP[arg_str], default="...")]

        # Single argument or list of arguments, e.g. 'String...' or 'Int...'
        if arg_str.endswith("...") and arg_str[0:-3] in TYPE_MAP:
            type = TYPE_MAP[arg_str[0:-3]]
            return [Argument("*args", f"__t.Sequence[{type}]|{type}")]

    else:  # Multiple type
        args = arg_str.split()

        if "..." not in arg_str:
            # Single types only e.g. String Int Float
            # Make each one be its own argument
            arguments: list[Argument] = []
            for i, arg in enumerate(args):
                arg_type = TYPE_MAP.get(arg, None)
                if not arg_type:
                    logger.warning(f"Could not determine positional arg type for command '{command}': unknown type '{arg}'")
                arguments.append(Argument(f"arg{i+1}", arg_type, default="..."))

            return arguments

        else:  # `arg_str` contains '...'
            listable_types = set()
            single_types = set()

            for arg in args:
                if arg.strip(".") not in TYPE_MAP:
                    logger.warning(f"Could not determine positional arg type for command '{command}': unknown type '{arg}'")
                    return default_arg()

                if arg.endswith("..."):
                    listable_types.add(TYPE_MAP.get(arg[0:-3], None))
                else:
                    single_types.add(TYPE_MAP.get(arg, None))

            arguments: list[Argument] = []
            for i, arg_type in enumerate(single_types):
                arguments.append(Argument(f"arg{i+1}", arg_type, default="..."))
            if listable_types:
                listable_type = "|".join(listable_types)
                arguments.append(Argument("*args", f"__t.Sequence[{listable_type}]|{listable_type}"))

            return arguments

    # [String...] -> *args:str|typing.Sequence[str]
    logger.warning(f"Could not determine positional args for command '{command}': {arg_str}")

    return default_arg()
