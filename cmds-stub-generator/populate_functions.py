import re

from . import base_types
from .documentation import command

TYPE_LOOKUP = {
    "boolean": "bool",
    "string": "str",
    "uint": "int",
    "int64": "int",
    "name": "str",
    "linear": "float",
    "angle": "float|str",
    "script": "Callable|str",
    "time": "float",
    "timerange": "tuple[float, float]",
    "floatrange": "tuple[float, float]",
    "double": "float",
    "selectionitem": "str",
    "int": "int",
}

PATTERN_ARRAY = re.compile(r'\[\d*\]$')


def get_arg_type(arg_type_str: str) -> str:
    def __get_type(arg: str):
        if match := PATTERN_ARRAY.search(arg):
            base_type = arg[:match.start()]
            arg = TYPE_LOOKUP.get(arg.lower(), arg)
            return f"list[{__get_type(base_type)}]"

        return TYPE_LOOKUP.get(arg.lower(), arg)

    arg_type = arg_type_str.strip()
    if "|" in arg_type:
        items = {get_arg_type(x) for x in arg_type.split("|")}
        return "|".join(sorted(items))

    # [string, [, string, ], [, string, ]] -> tuple[str, str, str]
    # [[, boolean, float, ]] -> tuple[bool, float]
    if "[, " in arg_type:
        arg_type = arg_type.replace("[, ", "").replace(", ]", "")

    if arg_type.startswith("["):
        items = arg_type.removeprefix("[").removesuffix("]").split(",")
        items = [__get_type(x.strip()) for x in items]
        return f"tuple[{','.join(items)}]"

    return __get_type(arg_type)


def flag_to_arg(flag: command.Flag, query=False) -> base_types.Argument:
    if flag.arg_type is None:
        arg_type = None
    else:
        arg_type = get_arg_type(flag.arg_type)

    if flag.multi_use:
        arg_type = f"multiuse[{arg_type}]"

    return base_types.Argument(
        name=flag.name_long,
        argument_type=arg_type,
        default="..."
    )


def create_functions(command_name: str, docs: command.CommandDocumentation | None, positional_args: list[base_types.Argument]) -> list[base_types.Function]:
    if not docs:
        return_type = "None" if command_name.isupper() else "Any"
        return [
            base_types.Function(
                name=command_name,
                positional_arguments=positional_args,
                keyword_arguments=[],
                return_type=return_type
            )
        ]

    if docs.obsolete:
        return [
            base_types.Function(
                name=command_name,
                positional_arguments=positional_args,
                keyword_arguments=[],
                deprecated=True,
                deprecation_message=docs.obsolete_message
            )
        ]

    functions: list[base_types.Function] = []

    # Create command
    create_flag = docs.get_create_flags()
    create_args = [flag_to_arg(x) for x in create_flag]

    return_types = set()
    for x in docs.returns:
        return_types.update(get_arg_type(x.type).split("|"))
    return_type_str = "|".join(sorted(return_types)) if return_types else "Any"

    functions.append(
        base_types.Function(
            name=command_name,
            positional_arguments=positional_args,
            keyword_arguments=create_args,
            return_type=return_type_str,
        )
    )

    # Edit commands
    if docs.editable:
        edit_flags = docs.get_edit_flags()
        edit_args = [flag_to_arg(x) for x in edit_flags]
        edit_args.insert(0, base_types.Argument(name="edit", argument_type="Literal[True]"))

        functions.append(
            base_types.Function(
                name=command_name,
                positional_arguments=positional_args,
                keyword_arguments=edit_args
            )
        )

    # Query commands
    if docs.queryable:
        query_arg = base_types.Argument(
            name="query",
            argument_type="Literal[True]",
        )

        functions.append(
            base_types.Function(
                name=command_name,
                positional_arguments=positional_args,
                keyword_arguments=[query_arg],
                return_type="Any"
            )
        )

        for flag in docs.get_query_flags():
            flag_arg = base_types.Argument(
                name=flag.name_long,
                argument_type="Literal[True]"
            )

            if flag.is_query_only():
                # If a flag is query only, it will have the argument type 'boolean'
                # So then we cannot deduce a return type from it
                return_type = "Any"
            else:
                return_type = get_arg_type(flag.arg_type) if flag.arg_type else "Any"

            functions.append(
                base_types.Function(
                    name=command_name,
                    positional_arguments=positional_args,
                    keyword_arguments=[query_arg, flag_arg],
                    return_type=return_type
                )
            )

    return functions
