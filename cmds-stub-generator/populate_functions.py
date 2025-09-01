import base_types
import documentaion.command

TYPE_LOOKUP = {
    "boolean": "bool",
    "string": "str",
    "uint": "int",
    "int64": "int",
    "name": "str",
    "linear": "float",
    "angle": "float",
    "script": "__t.Callable",
    "time": "float",
    "timerange": "tuple[float, float]",
    "floatrange": "tuple[float, float]",
}


def get_arg_type(flag: documentaion.command.Flag):
    def __get_type(arg: str):
        if arg.endswith("[]"):
            base_type = arg.removesuffix("[]")
            arg = TYPE_LOOKUP.get(arg, arg)
            return f"list[{__get_type(base_type)}]"

        return TYPE_LOOKUP.get(arg, arg)

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


def flag_to_arg(flag: documentaion.command.Flag, query=False) -> base_types.Argument:
    arg_type = get_arg_type(flag)
    if flag.multi_use:
        arg_type = f"multiuse[{arg_type}]"  #f"__t.Sequence[{arg_type}]|{arg_type}"

    return base_types.Argument(
        name=flag.name_long,
        argument_type=arg_type,
        default="..."
    )


def main(command: base_types.Command):

    # Create command
    create_flag = command.command_docs.get_create_flags()
    create_args = [flag_to_arg(x) for x in create_flag]

    command.add_function(
        base_types.Function(
            name=command.name,
            positional_arguments=[],
            keyword_arguments=create_args,
            return_type=None,
            docstring=None
        )
    )

    # Edit commands
    if edit_flags := command.command_docs.get_edit_flags():
        edit_args = [flag_to_arg(x) for x in edit_flags]
        edit_args.insert(0, base_types.Argument(name="edit", argument_type="__t.Literal[True]", default=None))

        command.add_function(
            base_types.Function(
                name=command.name,
                positional_arguments=[],
                keyword_arguments=edit_args,
                return_type=None,
                docstring=None
            )
        )

    # Query commands
    query_arg = base_types.Argument(
        name="query",
        argument_type="__t.Literal[True]",
    )
    for flag in command.command_docs.get_query_flags():
        flag_arg = base_types.Argument(
            name=flag.name_long,
            argument_type="__t.Literal[True]"
        )

        command.add_function(
            base_types.Function(
                name=command.name,
                positional_arguments=[],
                keyword_arguments=[query_arg, flag_arg],
                return_type=get_arg_type(flag),
                docstring=None
            )
        )