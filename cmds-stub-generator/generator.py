import logging
import enum
import time
import os

from . import populate_functions, documentaion, base_types, maya_info

logger = logging.getLogger(__name__)


class GeneratorFlag(enum.Flag):
    NONE = 0
    INCLUDE_UNDOCUMENTED_FUNCTIONS = enum.auto()
    """ Include all functions available in cmds, even the undocumented ones """


def generate_string(flags=GeneratorFlag(0)) -> str:
    commands: list[base_types.Command] = []

    with maya_info.MayaStandalone():
        maya_commands = maya_info.cmds_info.get_commands()
        documentation_commands = documentaion.index.get_commands(maya_info.version())

        all_commands = set(maya_commands) | set(documentation_commands.keys())

        for command_name in sorted(all_commands):
            positional_args = maya_info.cmds_info.get_positional_args(command_name)
            positional_args = [base_types.Argument(arg.name, arg.argument_type, arg.default) for arg in positional_args]

            doc_info = None
            if url := documentation_commands.get(command_name):
                doc_info = documentaion.command.get_info(url)
                if doc_info.obsolete:
                    positional_args = [base_types.Argument("*args"), base_types.Argument("**kwargs")]
            elif not (flags & GeneratorFlag.INCLUDE_UNDOCUMENTED_FUNCTIONS):
                continue

            command = base_types.Command(command_name, )
            populate_functions.main(command, doc_info, positional_args)

            commands.append(command)

        header_filepath = os.path.join(os.path.dirname(__file__), "header.py")
        with open(header_filepath, "r") as f:
            header = f.read()

        header = header.replace("{VERSION}", maya_info.version())

    code_str = "\n".join(x.get_string() for x in commands)
    return f"{header}\n{code_str}"


def generate_stubs(out_filepath: str, *, flags: GeneratorFlag = GeneratorFlag(0)) -> None:
    start_time = time.perf_counter()

    code = generate_string(flags)

    if os.path.isdir(out_filepath):
        out_filepath = os.path.join(out_filepath, "cmds.pyi")

    os.makedirs(os.path.dirname(out_filepath), exist_ok=True)
    with open(out_filepath, "w") as f:
        f.write(code)

    logger.info(f"Generated stubs in {time.perf_counter() - start_time:.2f} seconds")
