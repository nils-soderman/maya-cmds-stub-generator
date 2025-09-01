"""

"""
from dataclasses import dataclass

from documentaion.command import CommandDocumentation

@dataclass
class Argument:
    name: str
    argument_type: str
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
    return_type: str | None
    docstring: str | None

    def get_string(self) -> str:
        string = f"def {self.name}("

        if self.positional_arguments:
            string += ",".join(arg.get_string() for arg in self.positional_arguments)
            string += ",/"
            if self.keyword_arguments:
                string += ","

        if self.keyword_arguments:
            keyword_args_str = ",".join(arg.get_string() for arg in self.keyword_arguments)
            string += f"*,{keyword_args_str}"

        string += ")"

        if self.return_type:
            string += f"->{self.return_type}"

        string += ":"

        if self.docstring:
            string += f'\n\t"""{self.docstring}"""'
        else:
            string += '...'

        return string


class Command:
    def __init__(self, name: str, command_docs: CommandDocumentation) -> None:
        self.name = name
        self.command_docs = command_docs

        self._functions: list[Function] = []

    def add_function(self, function: Function) -> None:
        self._functions.append(function)

    def get_string(self) -> str:
        delimiter = "\n"
        if len(self._functions) > 1:
            delimiter = "\n@__t.overload\n"

        outstring =  delimiter.join(func.get_string() for func in self._functions)

        if len(self._functions) > 1:
            outstring = f"@__t.overload\n{outstring}"

        return outstring