import logging
import time
import os

import populate_functions
import documentaion
import base_types
import maya_info

logging.basicConfig(level=logging.DEBUG)


def generate_string() -> str:
    commands: list[base_types.Command] = []

    with maya_info.MayaStandalone():
        cmds_commands = maya_info.cmds_info.get_commands()

        documentation_commands = documentaion.index.get_commands(maya_info.version())
        for doc_command in documentation_commands:
            # if doc_command.command not in cmds_commands:
                # TODO: Don't skip these, some of them are only not avaliable in mayapy.exe, use any num of arguments
                # logging.warning(f'Skipping command documented but not found in `maya.cmds`: "{doc_command.command}"')
                # continue

            doc_info = documentaion.command.get_info(doc_command.url)

            command = base_types.Command(doc_command.command, doc_info)
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

    os.makedirs(os.path.dirname(out_filepath), exist_ok=True)
    with open(out_filepath, "w") as f:
        f.write(code)

    logging.info(f"Generated stubs in {time.perf_counter() - start_time:.2f} seconds")


generate_stubs("D:/Projects/Programming/Python_Packages/cmds-stub-generator/dist/cmds.pyi")
