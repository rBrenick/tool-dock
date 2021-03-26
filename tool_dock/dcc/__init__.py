import os
import sys

from . import tool_dock_dcc_base as base_dcc_module

if os.path.basename(sys.executable) == "maya.exe":
    from . import tool_dock_maya as active_dcc_module
    Interface = active_dcc_module.MayaToolDockInterface

# no implementation made for this DCC, use common base
else:
    active_dcc_module = base_dcc_module
    Interface = base_dcc_module.BaseToolDockInterface
