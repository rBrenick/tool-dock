from functools import partial

from dcc_toolbox.ui.ui_utils import QtCore, QtWidgets


class ToolBoxItemBase(QtWidgets.QWidget):
    TOOL_NAME = "TOOL"

    def __init__(self, *args, **kwargs):
        super(ToolBoxItemBase, self).__init__(*args, **kwargs)

        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.main_layout)

        # if multiple actions defined for Tool
        self._tool_actions = self.get_tool_actions()

        if self._tool_actions:
            for name, func in self._tool_actions.items():
                btn = QtWidgets.QPushButton(name)
                btn.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)

                btn.clicked.connect(partial(self._run, func))
                self.main_layout.addWidget(btn)
        else:
            btn = QtWidgets.QPushButton("{}".format(self.TOOL_NAME))
            btn.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
            btn.clicked.connect(self._run)
            self.main_layout.addWidget(btn)

    def _run(self, func=None):
        kwargs = {}
        if func:
            func(**kwargs)
        else:
            self.run(**kwargs)

    # to overwrite
    def run(self, *args, **kwargs):
        print("'run' not implemented: {}".format(self.TOOL_NAME))

    def get_tool_actions(self):
        return {}


class ToolBoxSettings(QtCore.QSettings):
    k_window_geometry = "window/geometry"
    k_window_state = "window/state"

    def __init__(self):
        super(ToolBoxSettings, self).__init__(
            QtCore.QSettings.IniFormat,
            QtCore.QSettings.UserScope,
            'dcc_toolbox',
        )


def all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)])


"""
def all_run_functions(cls):
    for key, val in cls.__dict__.items():
        if "run" in key and inspect.isfunction(val):
            yield val

"""
