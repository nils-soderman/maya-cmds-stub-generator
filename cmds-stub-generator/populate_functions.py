from . import base_types
from .documentaion import command

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
}


def get_arg_type(flag: command.Flag) -> str | None:
    def __get_type(arg: str):
        if arg.endswith("[]"):
            base_type = arg.removesuffix("[]")
            arg = TYPE_LOOKUP.get(arg, arg)
            return f"list[{__get_type(base_type)}]"

        return TYPE_LOOKUP.get(arg, arg)

    if flag.arg_type is None:
        return None

    arg_type = flag.arg_type.strip()

    # [string, [, string, ], [, string, ]] -> tuple[str, str, str]
    # [[, boolean, float, ]] -> tuple[bool, float]
    if "[, " in arg_type:
        print("Broken arg type, fixing!")
        arg_type = arg_type.replace("[, ", "").replace(", ]", "")

    if arg_type.startswith("["):
        items = arg_type.removeprefix("[").removesuffix("]").split(",")
        items = [__get_type(x.strip()) for x in items]
        return f"tuple[{','.join(items)}]"

    return __get_type(arg_type)


def flag_to_arg(flag: command.Flag, query=False) -> base_types.Argument:
    arg_type = get_arg_type(flag)
    if flag.multi_use:
        arg_type = f"multiuse[{arg_type}]"  # f"Sequence[{arg_type}]|{arg_type}"

    return base_types.Argument(
        name=flag.name_long,
        argument_type=arg_type,
        default="..."
    )


def main(command: base_types.Command, docs: command.CommandDocumentation | None, positional_args: list[base_types.Argument]):
    if not docs:
        return_type = "None" if command.name[0].isupper() else "Any"
        command.add_function(
            base_types.Function(
                name=command.name,
                positional_arguments=positional_args,
                keyword_arguments=[],
                return_type=return_type
            )
        )
        return

    if docs.obsolete:
        command.add_function(
            base_types.Function(
                name=command.name,
                positional_arguments=positional_args,
                keyword_arguments=[],
                deprecated=True,
                deprecation_message=docs.obsolete_message
            )
        )
        return

    # Create command
    create_flag = docs.get_create_flags()
    create_args = [flag_to_arg(x) for x in create_flag]

    command.add_function(
        base_types.Function(
            name=command.name,
            positional_arguments=positional_args,
            keyword_arguments=create_args
        )
    )

    # Edit commands
    if docs.editable:
        edit_flags = docs.get_edit_flags()
        edit_args = [flag_to_arg(x) for x in edit_flags]
        edit_args.insert(0, base_types.Argument(name="edit", argument_type="Literal[True]", default=None))

        command.add_function(
            base_types.Function(
                name=command.name,
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

        command.add_function(
            base_types.Function(
                name=command.name,
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
                return_type = get_arg_type(flag) or "Any"

            command.add_function(
                base_types.Function(
                    name=command.name,
                    positional_arguments=positional_args,
                    keyword_arguments=[query_arg, flag_arg],
                    return_type=return_type
                )
            )
