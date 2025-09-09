"""

"""
from dataclasses import dataclass

from .documentaion.command import CommandDocumentation

@dataclass
class Argument:
    name: str
    argument_type: str | None = None
    default: str | None = None

    def get_string(self) -> str:
        string = self.name

        if self.argument_type:
            string += f":{self.argument_type}"

        if self.default is not None:
            string += f"={self.default}"

        return string


@dataclass
class Function:
    name: str
    positional_arguments: list[Argument]
    keyword_arguments: list[Argument]
    return_type: str | None = "Any"
    docstring: str | None = None

    deprecated: bool = False
    deprecation_message: str | None = None

    def get_string(self) -> str:
        string = ""
        if self.deprecated:
            string = f'@deprecated("""{self.deprecation_message}""")\n'

        string += f"def {self.name}("

        has_star_args = any(arg.name.startswith("*") for arg in self.positional_arguments)

        if self.positional_arguments:
            string += ",".join(arg.get_string() for arg in self.positional_arguments)
            if not has_star_args:
                string += ",/"
            if self.keyword_arguments:
                string += ","

        if self.keyword_arguments:
            keyword_args_str = ",".join(arg.get_string() for arg in self.keyword_arguments)
            if not has_star_args:
                keyword_args_str = f"*,{keyword_args_str}"
            string += keyword_args_str

        string += ")"

        return_type = self.return_type or "Any"
        string += f"->{return_type}"

        string += ":"

        if self.docstring:
            string += f'\n\t"""{self.docstring}"""'
        else:
            string += '...'

        return string


class Command:
    def __init__(self, name: str, command_docs: CommandDocumentation, positional_args: list[Argument]) -> None:
        self.name = name
        self.command_docs = command_docs
        self.positional_args = positional_args

        self._functions: list[Function] = []

    def add_function(self, function: Function) -> None:
        function.positional_arguments = self.positional_args + function.positional_arguments
        self._functions.append(function)

    def get_string(self) -> str:
        delimiter = "\n"
        if len(self._functions) > 1:
            delimiter = "\n@overload\n"

        outstring = delimiter.join(func.get_string() for func in self._functions)

        if len(self._functions) > 1:
            outstring = f"@overload\n{outstring}"

        return outstring
