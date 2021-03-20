from functools import partial

from dcc_toolbox.ui.ui_utils import QtCore, QtWidgets


class ToolBoxItemBase(QtWidgets.QWidget):
    TOOL_NAME = "TOOL"

    def __init__(self, *args, **kwargs):
        super(ToolBoxItemBase, self).__init__(*args, **kwargs)

        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        # if multiple actions defined for Tool
        self._tool_actions = self.get_tool_actions()

        self.param_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addLayout(self.param_layout)

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


class BaseParam(object):
    def __init__(self, base_cls, label, default=None, build_ui=True, *args, **kwargs):
        self.base_cls = base_cls  # type: ToolBoxItemBase
        self.label_text = label

        if build_ui:
            self.build_ui()

        if default:
            self.set_value(default)

    def build_ui(self):
        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.param_label = QtWidgets.QLabel(self.label_text)
        self.main_layout.addWidget(self.param_label)

        self.base_cls.param_layout.addLayout(self.main_layout)
        self.build_type_widgets()

    def build_type_widgets(self):
        raise NotImplementedError("build_type_widgets not implemented for: {}".format(self.__class__))

    def get_value(self):
        raise NotImplementedError("get_value not implemented for: {}".format(self.__class__))

    def set_value(self, val):
        raise NotImplementedError("set_value not implemented for: {}".format(self.__class__))


class FloatParam(BaseParam):
    def __init__(self, *args, **kwargs):
        self.minimum = kwargs.get("min", -200000)
        self.maximum = kwargs.get("max", 200000)
        super(FloatParam, self).__init__(*args, **kwargs)

    def build_type_widgets(self):
        self.spinbox = QtWidgets.QDoubleSpinBox()
        self.spinbox.setStepType(QtWidgets.QDoubleSpinBox.AdaptiveDecimalStepType)
        self.spinbox.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.spinbox.setMinimum(self.minimum)
        self.spinbox.setMaximum(self.maximum)
        self.main_layout.addWidget(self.spinbox)

    def get_value(self):
        return self.spinbox.value()

    def set_value(self, val):
        self.spinbox.setValue(val)


class StringParam(BaseParam):
    def build_type_widgets(self):
        self.line_edit = QtWidgets.QLineEdit()
        self.line_edit.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.main_layout.addWidget(self.line_edit)

    def get_value(self):
        return self.line_edit.text()

    def set_value(self, val):
        self.line_edit.setText(val)


class ChoiceParam(BaseParam):
    def __init__(self, *args, **kwargs):
        self.options = kwargs.get("choices", [])
        super(ChoiceParam, self).__init__(*args, **kwargs)

    def build_type_widgets(self):
        self.combo_box = QtWidgets.QComboBox()
        self.combo_box.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.combo_box.addItems(self.options)
        self.main_layout.addWidget(self.combo_box)

    def set_value(self, val):
        self.combo_box.setCurrentText(val)

    def get_value(self):
        return self.combo_box.currentText()


def all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)])


"""
def all_run_functions(cls):
    for key, val in cls.__dict__.items():
        if "run" in key and inspect.isfunction(val):
            yield val

"""
