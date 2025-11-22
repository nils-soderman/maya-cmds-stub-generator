import logging
import time
import os

from . import populate_functions, documentation, base_types, maya_info, docstring
from .flags import GeneratorFlag

logger = logging.getLogger(__name__)




def create_command(command_name: str, doc_url: str | None, flags: GeneratorFlag) -> base_types.Command:
    positional_args = maya_info.cmds_info.get_positional_args(command_name)
    positional_args = [base_types.Argument(arg.name, arg.argument_type, arg.default) for arg in positional_args]

    doc_info = None
    if doc_url:
        doc_info = documentation.command.get_info(doc_url, use_cache=bool(flags & GeneratorFlag.CACHE))
        if doc_info.obsolete:
            positional_args = [base_types.Argument("*args"), base_types.Argument("**kwargs")]

    functions = populate_functions.get_functions_all(command_name, doc_info, positional_args, flags)
    doc_str = docstring.create_docstring(doc_info) if doc_info else ""
    command = base_types.Command(command_name, doc_str, functions)

    return command


def generate_string(flags=GeneratorFlag.NONE) -> str:
    commands: list[base_types.Command] = []

    with maya_info.MayaStandalone():
        maya_commands = maya_info.cmds_info.get_commands()
        documentation_commands = documentation.index.get_commands(maya_info.version())

        all_commands = set(maya_commands) | set(documentation_commands.keys())

        for command_name in sorted(all_commands):
            docs_url = documentation_commands.get(command_name)
            if not docs_url and not (flags & GeneratorFlag.INCLUDE_UNDOCUMENTED_FUNCTIONS):
                continue

            command = create_command(command_name, docs_url, flags)
            commands.append(command)

        header_filepath = os.path.join(os.path.dirname(__file__), "template_header.py")
        with open(header_filepath, "r") as f:
            header = f.read()

        header = header.replace("{VERSION}", maya_info.version())

    code_str = "\n".join(x.get_string() for x in commands)
    return f"{header}\n{code_str}"


def generate_stubs(out_filepath: str, *, flags: GeneratorFlag = GeneratorFlag.NONE) -> None:
    start_time = time.perf_counter()

    code = generate_string(flags)

    if os.path.isdir(out_filepath):
        out_filepath = os.path.join(out_filepath, "cmds.pyi")

    os.makedirs(os.path.dirname(out_filepath), exist_ok=True)
    with open(out_filepath, "w", encoding="utf-8") as f:
        f.write(code)

    logger.info(f"Generated stubs in {time.perf_counter() - start_time:.2f} seconds")
