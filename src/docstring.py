import re

from .documentation import command

PATTERN_ENDING_HEADER_FILE = re.compile(r"\n[A-Za-z]+\.h$", re.MULTILINE)
PATTERN_SINGLE_BACKSLASH = re.compile(r'(?<!\\)\\(?!\\)')


def create_docstring(docs: command.CommandDocumentation) -> str:
    command_desc = docs.description.strip()
    command_desc = command_desc.replace("\n\n", "\n").replace("\n\n", "\n")  # Avoid triple newlines
    command_desc = command_desc.replace("\n", "\n\n\t")  # Indent new lines

    # If description ends with the name of a C++ header file, remove it
    command_desc = re.sub(PATTERN_ENDING_HEADER_FILE, '', command_desc).strip()
    command_desc = re.sub(PATTERN_SINGLE_BACKSLASH, r'\\\\', command_desc)

    if command_desc.endswith('"'):
        command_desc = command_desc[:-1] + r'\"'

    # Parameters
    params_str = ""
    if docs.flags:
        params_str = "\n\n\t# Parameters"
        for flag in docs.flags:
            flag_desc = flag.description.strip()
            flag_desc = flag_desc.replace("\\", "\\\\")
            flag_desc = flag_desc.replace("\n", "\n\t\t\t")
            params_str += f"\n\t\t- {flag.name_long}: {flag_desc}\n"
        params_str = params_str.rstrip()

    # Return values
    returns_str = ""
    if any(x.description.strip() for x in docs.returns):  # If there are no descriptions, don't add a returns section
        returns_str = "\n\n\t# Returns"
        for return_value in docs.returns:
            return_desc = return_value.description.strip()
            return_desc = return_desc.replace("\n", "\n\t\t")
            returns_str += f"\n\t\t- {return_value.type}: {return_desc}"

    # Undoable
    if docs.undoable:
        undoable_str = "This command is undoable"
    else:
        undoable_str = "This command is **NOT undoable**"


    return f"{command_desc}{params_str}{returns_str}\n\n\t{undoable_str}"
