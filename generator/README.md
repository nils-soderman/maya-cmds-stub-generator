# Generating Stubs

```cmd
mayapy.exe -m pip install git+https://github.com/nils-soderman/maya-cmds-stub-generator#subdirectory=generator --target="{INSTALL_LOCATION}"

cd "{INSTALL_LOCATION}"

"C:/Program Files/Autodesk/Maya{VERSION}/bin/mayapy.exe" -m maya_cmds_stub_generator "{OUTPUT_DIR}"
```


* Replace `{INSTALL_LOCATION}` with your desired installation path
* Replace `{VERSION}` with your Maya version
* Replace `{OUTPUT_DIR}` with the directory where you want the stub files to be generated


## CLI Options

| Option | Description |
|-|-|
| `--cache` | Cache the online documentation on disk, mainly for development when you re-run the generator multiple times |
| `--tuple-params` | Use tuple for Sequence parameters, this is more strict _(e.g. `tuple[float, float, float]` vs `Sequence[float]`)_ |
| `--undocumented` | Include internal functions not documented in the maya cmds documentation |


## Design Overview

The `maya.cmds` API is not very Pythonic, functions accept many arguments and may return different types depending on those arguments.

To adress this, the stubs rely on the `@overload` decorator to create multiple different function signatures for each case.

_(The cmds documentation indicates for every parameter whether it can be used in create, edit, or query mode)_

```python
# Create
# Populate with all arguments that can be used in 'create' mode
@overload
def example(arg1: float):
    ...

# Edit
# Populate with all arguments that can be combined with edit
@overload
def example(edit: Literal[True], arg2: int):
    ...

# Query
# Create one function per queryable argument
# Because 'arg1' is of type float, querying 'arg1' will return float
@overload
def example(query: Literal[True], arg1: Literal[True]) -> float:
    ...

@overload
def example(query: Literal[True], arg2: Literal[True]) -> int:
    ...
```


## Issues

If you run into any issues with the generator. Please open a issue on the [GitHub repository](https://github.com/nils-soderman/maya-cmds-stub-generator/issues).

Contributions are welcomed!