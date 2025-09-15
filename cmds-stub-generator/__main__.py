import argparse
import os

from . import generator, GeneratorFlag


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate stubs for the `maya.cmds` module. This module must run in the mayapy interpreter.")

    parser.add_argument("output", type=str, help="Output file path for the generated stubs.")
    parser.add_argument(
        "--undocumented",
        action="store_true",
        help="Include internal functions not publicly documented"
    )

    args = parser.parse_args()

    output_path = os.path.abspath(args.output)

    flags = GeneratorFlag.NONE
    if args.undocumented:
        flags |= GeneratorFlag.INCLUDE_UNDOCUMENTED_FUNCTIONS

    generator.generate_stubs(output_path, flags=flags)


if __name__ == "__main__":
    main()
