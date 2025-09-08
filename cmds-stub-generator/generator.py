import logging
import time
import os

from . import populate_functions, documentaion, base_types, maya_info

logger = logging.getLogger(__name__)

def generate_string() -> str:
    commands: list[base_types.Command] = []

    with maya_info.MayaStandalone():
        documentation_commands = documentaion.index.get_commands(maya_info.version())
        for doc_command in documentation_commands:
            doc_info = documentaion.command.get_info(doc_command.url)
            if not doc_info.obsolete:
                positional_args = maya_info.cmds_info.get_positional_args(doc_command.command)
                positional_args = [base_types.Argument(arg.name, arg.argument_type, arg.default) for arg in positional_args]
            else:
                positional_args = [base_types.Argument("*args"), base_types.Argument("**kwargs")]
            command = base_types.Command(doc_command.command, doc_info, positional_args)
            populate_functions.main(command)

            commands.append(command)

        header_filepath = os.path.join(os.path.dirname(__file__), "header.py")
        with open(header_filepath, "r") as f:
            header = f.read()

        header = header.replace("{VERSION}", maya_info.version())

    code_str = "\n".join(x.get_string() for x in commands)
    return f"{header}\n{code_str}"


def generate_stubs(out_filepath: str) -> None:
    start_time = time.perf_counter()

    code = generate_string()

    if os.path.isdir(out_filepath):
        out_filepath = os.path.join(out_filepath, "cmds.pyi")

    os.makedirs(os.path.dirname(out_filepath), exist_ok=True)
    with open(out_filepath, "w") as f:
        f.write(code)

    logger.info(f"Generated stubs in {time.perf_counter() - start_time:.2f} seconds")
