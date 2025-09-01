import maya.cmds


def get_commands() -> set[str]:
    return set(dir(maya.cmds))
