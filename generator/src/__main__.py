import argparse
import os

from . import generator
from .flags import GeneratorFlag


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate stubs for the `maya.cmds` module. This module must run in the mayapy interpreter.")

    parser.add_argument("output", type=str, help="Output file path for the generated stubs.")
    parser.add_argument(
        "--undocumented",
        action="store_true",
        help="Include internal functions not publicly documented"
    )
    parser.add_argument(
        "--cache",
        action="store_true",
        help="Cache downloaded documentation to disk"
    )
    parser.add_argument(
        "--tuple-params",
        action="store_true",
        help="Use tuple parameters for functions, will otherwise use Sequence which is less strict"
    )

    args = parser.parse_args()

    output_path = os.path.abspath(args.output)

    flags = GeneratorFlag.NONE
    if args.undocumented:
        flags |= GeneratorFlag.INCLUDE_UNDOCUMENTED_FUNCTIONS
    if args.cache:
        flags |= GeneratorFlag.CACHE
    if args.tuple_params:
        flags |= GeneratorFlag.TUPLE_PARAMS

    generator.generate_stubs(output_path, flags=flags)


if __name__ == "__main__":
    main()
