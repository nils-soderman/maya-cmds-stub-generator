# Generating Stubs

```cmd
mayapy.exe -m pip install git+https://github.com/nils-soderman/maya-cmds-stub-generator --target="{INSTALL_DIR}"
cd "{INSTALL_DIR}"
mayapy.exe -m cmds-stub-generator "{OUTPUT_FILEPATH}"
```


## CLI Options

| Option | Description |
|-|-|
| `--cache` | Cache the online documentation on disk, mainly for development when you re-run the generator multiple times |
| `--tuple-params` | Use tuple for Sequence parameters, this is more strict _(e.g. `tuple[float, float, float]` vs `Sequence[float]`)_ |
| `--undocumented` | Include internal functions not documented in the maya cmds documentation |
