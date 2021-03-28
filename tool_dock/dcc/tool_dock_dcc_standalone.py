import os

from . import tool_dock_dcc_base as dcc_base


class StandaloneToolDockInterface(dcc_base.BaseToolDockInterface):
    def open_script_in_editor(self, script_path):
        # Here I'm assuming that this is running on Windows
        cmd_str = "notepad.exe {}".format(script_path)
        os.system(cmd_str)
