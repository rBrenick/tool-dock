import os
import sys

from . import tool_dock_dcc_base as base_dcc_module

currently_using_maya = os.path.basename(sys.executable) == "maya.exe"
currently_using_mobu = os.path.basename(sys.executable) == "motionbuilder.exe"
currently_using_standalone = False

if currently_using_maya:
    dcc_name = "Maya"
elif currently_using_mobu:
    dcc_name = "MotionBuilder"
else:
    currently_using_standalone = True
    dcc_name = "Standalone"

# Import DCC specific module
if currently_using_maya:
    from . import tool_dock_maya as active_dcc_module

    Interface = active_dcc_module.MayaToolDockInterface

elif currently_using_standalone:
    from . import tool_dock_dcc_standalone as active_dcc_module

    Interface = active_dcc_module.StandaloneToolDockInterface

# no implementation made for this DCC, use common base
else:
    active_dcc_module = base_dcc_module
    Interface = base_dcc_module.BaseToolDockInterface
