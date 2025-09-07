import argparse
import os

from . import generator


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate type stubs for `maya.cmds` module.")
    parser.add_argument("output", type=str, help="Output file path for the generated stubs.")
    args = parser.parse_args()

    output_path = os.path.abspath(args.output)
    generator.generate_stubs(output_path)

if __name__ == "__main__":
    main()

# "C:/Program Files/Autodesk/Maya2026/bin/mayapy.exe" -m cmds-stub-generator "generated-stubs/2026/cmds.pyi"