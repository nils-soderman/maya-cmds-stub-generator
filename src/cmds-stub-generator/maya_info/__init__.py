from .standalone import MayaStandalone

import maya.cmds
from . import cmds_info

def version():
    return maya.cmds.about(version=True)