import re

from . import base_types
from .documentation import command
from .flags import GeneratorFlag

from . import resources

PATTERN_ARRAY = re.compile(r'\[\d*\]$')

TYPE_CONVERSION = resources.load("type_conversion.jsonc")
TYPE_CONVERSION_RETURNS = resources.load("type_conversion_returns.jsonc")
CREATE_FLAG_RETURN_TYPES = resources.load("create_return_types.jsonc")
QUERY_FLAG_MODIFIERS = resources.load("query_flag_modifiers.jsonc")
QUERY_FLAG_RETURN_TYPES = resources.load("query_return_types.jsonc")


def get_arg_type(arg_type_str: str, *, return_type: bool = False, sequence_as_tuple: bool = False) -> str:
    def __get_type(arg: str):
        if match := PATTERN_ARRAY.search(arg):
            base_type = arg[:match.start()]
            return f"list[{__get_type(base_type)}]"

        if return_type and arg in TYPE_CONVERSION_RETURNS:
            return TYPE_CONVERSION_RETURNS[arg]

        return TYPE_CONVERSION.get(arg, arg)

    arg_type = arg_type_str.lower().strip()
    if "|" in arg_type:
        items = {get_arg_type(x, return_type=return_type, sequence_as_tuple=sequence_as_tuple) for x in arg_type.split("|")}
        return "|".join(sorted(items))

    # [string, [, string, ], [, string, ]] -> tuple[str, str, str]
    # [[, boolean, float, ]] -> tuple[bool, float]
    if "[, " in arg_type:
        arg_type = arg_type.replace("[, ", "").replace(", ]", "")

    if arg_type.startswith("["):
        items = arg_type.removeprefix("[").removesuffix("]").split(",")
        items = [__get_type(x.strip()) for x in items]
        if sequence_as_tuple:
            return f"tuple[{','.join(items)}]"
        else:
            items = sorted(list(set(items)))  # Remove duplicates
            return f"Sequence[{','.join(items)}]"

    return __get_type(arg_type)


def flag_to_arg(flag: command.Flag, *, sequence_as_tuple: bool = False) -> base_types.Argument:
    if flag.arg_type is None:
        arg_type = None
    else:
        arg_type = get_arg_type(flag.arg_type, sequence_as_tuple=sequence_as_tuple)

    if flag.multi_use:
        arg_type = f"multiuse[{arg_type}]"

    return base_types.Argument(
        name=flag.name_long,
        argument_type=arg_type,
        default="..."
    )


def get_functions_create(command_name: str,
                         docs: command.CommandDocumentation,
                         positional_args: list[base_types.Argument],
                         flags: GeneratorFlag) -> list[base_types.Function]:
    functions: list[base_types.Function] = []

    create_flag = docs.get_create_flags()
    create_args = [flag_to_arg(x, sequence_as_tuple=bool(flags & GeneratorFlag.TUPLE_PARAMS)) for x in create_flag]

    return_types = set()
    for x in docs.returns:
        return_types.update(get_arg_type(x.type, return_type=True, sequence_as_tuple=True).split("|"))
    if not return_types:
        return_types.add("Any")

    # Figure out if we need to split up the create functions based on known return types
    if create_returns := CREATE_FLAG_RETURN_TYPES.get(command_name):
        # Assume all flags with this return type has been documented and remove them from the general return types
        return_types.difference_update(create_returns.values())

        for flag_name, flag_return_type in create_returns.items():
            if arg_to_modify := next((x for x in create_args if x.name == flag_name), None):
                # Remove the flag from the default create args
                create_args.remove(arg_to_modify)

                arg_to_modify.default = None

                functions.append(
                    base_types.Function(
                        name=command_name,
                        positional_arguments=positional_args,
                        keyword_arguments=[arg_to_modify],
                        return_type=flag_return_type
                    )
                )

    return_type_str = "|".join(sorted(return_types))

    functions.insert(
        0,
        base_types.Function(
            name=command_name,
            positional_arguments=positional_args,
            keyword_arguments=create_args,
            return_type=return_type_str,
        )
    )

    return functions


def get_functions_edit(command_name: str, docs: command.CommandDocumentation, positional_args: list[base_types.Argument], flags: GeneratorFlag) -> list[base_types.Function]:
    if not docs.editable:
        return []

    edit_flags = docs.get_edit_flags()
    edit_args = [flag_to_arg(x, sequence_as_tuple=bool(flags & GeneratorFlag.TUPLE_PARAMS)) for x in edit_flags]
    edit_args.insert(0, base_types.Argument(name="edit", argument_type="Literal[True]"))

    return [
        base_types.Function(
            name=command_name,
            positional_arguments=positional_args,
            keyword_arguments=edit_args
        )
    ]


def get_functions_query(command_name: str,
                        docs: command.CommandDocumentation,
                        positional_args: list[base_types.Argument],
                        flags: GeneratorFlag) -> list[base_types.Function]:
    if not docs.queryable:
        return []

    functions: list[base_types.Function] = []

    general_modifier_flags = [x for x in docs.flags if not x.query and "In query mode" in x.description]
    general_modifier_args = [flag_to_arg(x, sequence_as_tuple=bool(flags & GeneratorFlag.TUPLE_PARAMS)) for x in general_modifier_flags]

    modifiers = QUERY_FLAG_MODIFIERS.get(command_name, {})
    query_return_type = QUERY_FLAG_RETURN_TYPES.get(command_name, {})

    query_arg = base_types.Argument(
        name="query",
        argument_type="Literal[True]",
    )

    functions.append(
        base_types.Function(
            name=command_name,
            positional_arguments=positional_args,
            keyword_arguments=[query_arg, *general_modifier_args],
            return_type="Any"
        )
    )

    query_flags = docs.get_query_flags()
    for flag in query_flags:
        if flag.name_long in modifiers:
            # This flag is a modifier for other query flags
            # Skip creation of a separate function for it
            continue

        # Find all flags that are modifiers for this flag
        modifier_flags = [x for x in query_flags if flag.name_long in modifiers.get(x.name_long, [])]
        modifier_args = [flag_to_arg(x, sequence_as_tuple=bool(flags & GeneratorFlag.TUPLE_PARAMS)) for x in modifier_flags]

        flag_arg = base_types.Argument(
            name=flag.name_long,
            argument_type="Literal[True]"
        )

        if flag.name_long in query_return_type:
            return_type = query_return_type[flag.name_long]
        elif flag.is_query_only():
            # If a flag is query only, it will have the argument type 'boolean'
            # So then we cannot deduce a return type from it
            return_type = "Any"
        else:
            return_type = get_arg_type(flag.arg_type, return_type=True, sequence_as_tuple=True) if flag.arg_type else "Any"

            # Query can sometimes return something different than the flag type, most common with bool
            # This is usually indicated in the flag description as e.g. 'in query mode, or when queried'
            if return_type == "bool":
                desc_lowercase = flag.description.lower()
                if "query" in desc_lowercase or "queried" in desc_lowercase:
                    return_type = "Any"

        functions.append(
            base_types.Function(
                name=command_name,
                positional_arguments=positional_args,
                keyword_arguments=[query_arg, flag_arg, *modifier_args, *general_modifier_args],
                return_type=return_type
            )
        )

    return functions


def get_functions_all(command_name: str,
                      docs: command.CommandDocumentation | None,
                      positional_args: list[base_types.Argument],
                      flags: GeneratorFlag) -> list[base_types.Function]:
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
    functions.extend(get_functions_create(command_name, docs, positional_args, flags))
    functions.extend(get_functions_edit(command_name, docs, positional_args, flags))
    functions.extend(get_functions_query(command_name, docs, positional_args, flags))

    return functions
