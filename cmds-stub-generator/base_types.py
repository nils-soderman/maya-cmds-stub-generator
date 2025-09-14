from dataclasses import dataclass


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

    deprecated: bool = False
    deprecation_message: str | None = None

    def get_string(self, docstring: str | None = None) -> str:
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

        if docstring:
            string += f'\n\t"""{docstring}"""'
        else:
            string += '...'

        return string

@dataclass
class Command:
    name: str
    docstring: str
    functions: list[Function]

    def get_string(self) -> str:
        delimiter = "\n"

        overloading = len(self.functions) > 1
        if overloading:
            delimiter = "\n@overload\n"

        docstring = self.docstring if not overloading else None
        outstring = delimiter.join(func.get_string(docstring) for func in self.functions)

        if overloading:
            outstring = f"@overload\n{outstring}"

            # Add a final function definition without overload decorator, that has the docstring
            if self.docstring:
                outstring += f'\ndef {self.name}(*args, **kwargs):\n\t"""{self.docstring}"""'

        return outstring
