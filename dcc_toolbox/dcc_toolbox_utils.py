import collections
import inspect
import os
import runpy
import sys
from functools import partial

from dcc_toolbox.ui import parameter_grid
from dcc_toolbox.ui.ui_utils import QtCore, QtWidgets, build_menu_from_action_list

PY_2 = sys.version_info[0] < 3
background_form = "background-color:rgb({0}, {1}, {2})"


class RequiresValueType(object):
    """Used to mark whether arguments have a default value specified"""
    pass


class LocalConstants(object):
    # generate custom py scripts from folder
    dynamic_classes_generated = False
    dynamic_classes = {}
    scripts_folder = os.environ.get("TOOLBOX_SCRIPT_FOLDER", "D:/Google Drive/Scripting/_Scripts")
    generate_script_preview = True

    def generate_dynamic_classes(self):
        if not self.scripts_folder or not os.path.exists(self.scripts_folder):
            return

        for script_path in get_script_paths(self.scripts_folder):
            script_name = os.path.splitext(os.path.basename(script_path))[0]
            if script_name in self.dynamic_classes.keys():
                continue

            script_cls = make_class_from_script(script_path, tool_name=script_name)

            self.dynamic_classes[script_name] = script_cls

        print("Generated: {} tool classes from files in: {}".format(len(self.dynamic_classes), self.scripts_folder))
        self.dynamic_classes_generated = True


lk = LocalConstants()


class _InternalToolBoxItemBase(QtWidgets.QWidget):
    """
    Internal Base Class for tools logic
    """
    TOOL_NAME = "TOOL"
    TOOL_TIP = "TOOLTIP UNDEFINED"
    BACKGROUND_COLOR = None

    SCRIPT_PATH = None  # used by dynamically generated classes

    def __init__(self, *args, **kwargs):
        super(_InternalToolBoxItemBase, self).__init__(*args, **kwargs)

        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        # right click menu
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)
        self.context_menu_actions = [
            {"Set Splitter - Vertical": partial(self.set_splitter_orientation, True)},
            {"Set Splitter - Horizontal": partial(self.set_splitter_orientation, False)},
        ]

        # if multiple actions defined for Tool
        self._tool_actions = self.get_tool_actions()
        self._parameters_auto_generated = False

        # Splitter between parameter_grid and 'run' buttons
        self.main_splitter = QtWidgets.QSplitter()

        # parameter grid
        self.param_grid = parameter_grid.ParameterGrid()
        self.param_grid.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.main_splitter.addWidget(self.param_grid)

        # build run buttons and add to splitter
        ui_widget = self.build_ui_widget()
        if self.BACKGROUND_COLOR:
            ui_widget.setStyleSheet(background_form.format(*self.BACKGROUND_COLOR))
        self.main_splitter.addWidget(ui_widget)

        # default hide parameter grid
        self.main_splitter.handle(1).setEnabled(False)
        self.main_splitter.setSizes([0, 100])
        self.main_layout.addWidget(self.main_splitter)

    def open_context_menu(self):
        return build_menu_from_action_list(self.context_menu_actions)

    def auto_populate_parameters(self):
        """Convenience function for generating parameters based on arguments of 'run'"""
        run_arguments = get_func_arguments(self.run)

        if not run_arguments:
            return

        for param_name, default_value in run_arguments.items():
            if param_name == "self":  # ignore 'self' argument, should be safe-ish
                run_arguments.pop(param_name)
                continue

            is_required = default_value == RequiresValueType
            if is_required:
                run_arguments[param_name] = str()  # fill to make sure every argument has something

        if run_arguments:
            self.param_grid.from_data(run_arguments)
            self._parameters_auto_generated = True

    def set_splitter_orientation(self, vertical=True):
        orientation = QtCore.Qt.Vertical if vertical else QtCore.Qt.Horizontal
        self.main_splitter.setOrientation(orientation)

    def post_init(self):
        # auto generate parameter widgets if run function has arguments
        # skip if parameters have been manually defined
        if not self.param_grid.parameters:
            self.auto_populate_parameters()

        # show parameter grid if parameters are defined
        if self.param_grid.parameters:
            self.main_splitter.handle(1).setEnabled(True)
            self.main_splitter.setSizes([sys.maxint, sys.maxint])

    def build_ui_widget(self):
        """
        Create buttons to execute run function
        Can be overridden by subclasses
        :return:
        """
        if self._tool_actions:
            multi_button_layout = QtWidgets.QHBoxLayout()
            multi_button_layout.setContentsMargins(0, 0, 0, 0)
            for name, func in self._tool_actions.items():
                btn = QtWidgets.QPushButton(name)
                btn.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.MinimumExpanding)

                btn.clicked.connect(partial(self._run, func))
                multi_button_layout.addWidget(btn)

            multi_button_widget = QtWidgets.QWidget()
            multi_button_widget.setLayout(multi_button_layout)
            main_widget = multi_button_widget
        else:
            btn = QtWidgets.QPushButton("{}".format(self.TOOL_NAME))
            btn.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.MinimumExpanding)
            btn.clicked.connect(self._run)
            main_widget = btn
        return main_widget

    def _run(self, func=None):
        kwargs = {}  # maybe put something in here by default? not sure
        if func:
            func(**kwargs)
        else:
            if self._parameters_auto_generated:
                kwargs = self.param_grid.as_data()
            self.run(**kwargs)

    # to overwrite
    def run(self, *args, **kwargs):
        print("'run' not implemented: {}".format(self.TOOL_NAME))

    def get_tool_actions(self):
        return {}


class ToolBoxItemBase(_InternalToolBoxItemBase):
    """
    Base Class for tools to inherit from
    """
    pass


class ToolBoxSettings(QtCore.QSettings):
    def __init__(self):
        super(ToolBoxSettings, self).__init__(
            QtCore.QSettings.IniFormat,
            QtCore.QSettings.UserScope,
            'dcc_toolbox',
        )


def get_func_arguments(func):
    """ copied from https://github.com/rBrenick/argument-dialog """
    if PY_2:
        arg_spec = inspect.getargspec(func)
    else:
        arg_spec = inspect.getfullargspec(func)

    parameter_dict = collections.OrderedDict()
    for param_name in arg_spec.args:
        parameter_dict[param_name] = RequiresValueType  # argument has no default value, not even a 'None'

    if arg_spec.defaults:
        for param_value, param_key in zip(arg_spec.defaults[::-1], reversed(parameter_dict.keys())):  # fill in defaults
            parameter_dict[param_key] = param_value

    return parameter_dict


def all_subclasses(cls):
    return set(cls.__subclasses__()).union([s for c in cls.__subclasses__() for s in all_subclasses(c)])


def get_toolbox_item_classes():
    if not lk.dynamic_classes_generated:
        lk.generate_dynamic_classes()

    # get all base sub classes
    subclasses = list(all_subclasses(ToolBoxItemBase))
    subclasses.extend(lk.dynamic_classes.values())
    return subclasses


def get_preview_from_script(script_path, max_line_count=None):
    """
    Open file and read a couple of lines
    :param script_path: script file path
    :type script_path: str
    :param max_line_count: truncate preview to a certain line count
    :type max_line_count: int
    :return:
    """
    with open(script_path, "r") as fp:
        script_lines = fp.readlines()

    if max_line_count is None:
        max_line_count = len(script_lines)

    script_code = "".join(script_lines[:max_line_count])
    if len(script_lines) > max_line_count:
        script_code = "{}......".format(script_code)  # indicators that script is truncated

    preview_str = "{}\n\n{}\n".format(script_path, script_code)
    return preview_str


def make_class_from_script(script_path, tool_name):
    class DynamicClass(_InternalToolBoxItemBase):
        TOOL_NAME = tool_name
        TOOL_TIP = script_path
        SCRIPT_PATH = script_path

        def run(self):
            return runpy.run_path(script_path, init_globals=globals(), run_name="__main__")

    return DynamicClass


def get_script_paths(root_folder):
    for folder, _, file_names in os.walk(root_folder):
        for file_name in file_names:
            if file_name.endswith(".py"):
                yield os.path.join(folder, file_name)
