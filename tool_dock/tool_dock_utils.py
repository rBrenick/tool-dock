import collections
import importlib
import inspect
import os
import runpy
import sys
import traceback
from copy import copy
from functools import partial

from tool_dock import dcc
from tool_dock.ui import parameter_grid
from tool_dock.ui import ui_utils
from tool_dock.ui.ui_utils import QtCore, QtWidgets, QtGui

PY_2 = sys.version_info[0] < 3
background_form = "background-color:rgb({0}, {1}, {2})"
dcc_interface = dcc.Interface()


class RequiresValueType(object):
    """Used to mark whether arguments have a default value specified"""
    pass


class ToolDockSettings(QtCore.QSettings):
    def __init__(self, *args, **kwargs):
        super(ToolDockSettings, self).__init__(*args, **kwargs)

    def get_value(self, key, default=None):
        data_type = None
        if default is not None:
            data_type = type(default)

        settings_val = self.value(key, defaultValue=default)

        # safety for list types
        if data_type == list and not isinstance(settings_val, list):
            settings_val = [settings_val] if settings_val else list()

        # safety for dict types
        if data_type == dict and not isinstance(settings_val, dict):
            settings_val = dict(settings_val)

        # safety for int types
        if data_type == int and not isinstance(settings_val, int):
            settings_val = default if settings_val is None else int(settings_val)

        # safety convert bool to proper type
        if data_type == bool:
            settings_val = True if settings_val in ("true", "True", "1", 1, True) else False

        return settings_val

    def set_user_color(self, tool_name, color):
        user_colors = self.get_value(lk.user_colors, default=dict())
        user_colors[tool_name] = color
        self.setValue(lk.user_colors, user_colors)

    def set_user_label(self, tool_name, label):
        user_labels = self.get_value(lk.user_labels, default=dict())
        user_labels[tool_name] = label
        self.setValue(lk.user_labels, user_labels)

    def set_tools_as_viewed(self):
        available_tools = [cls.TOOL_NAME for cls in get_tool_classes()]
        self.setValue(lk.last_viewed_tools, available_tools)


class LocalConstants(object):
    # generate custom py scripts from folder
    dynamic_classes_generated = False
    dynamic_classes = {}

    env_extra_modules = "TOOL_DOCK_EXTRA_MODULES"
    env_script_folders = "TOOL_DOCK_SCRIPT_FOLDERS"
    extension_path_prefix = "tool_dock_ext"

    # settings keys
    user_script_paths = "user_script_paths"
    user_colors = "user_colors"
    user_labels = "user_labels"
    last_viewed_tools = "last_viewed_tools"  # list of tools seen in tool

    # only make one settings instance for use everywhere
    settings = ToolDockSettings(QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope,
                                'tool_dock', '{dcc}_tool_dock'.format(dcc=ui_utils.dcc_name.lower()))

    # a base scripts folder can be defined via this environment variable
    # script files in this folder structure will be added as dynamic classes
    script_folders = os.environ.get(env_script_folders, "D:/Google Drive/Scripting/_Scripts___")

    def generate_dynamic_classes(self):
        if not self.script_folders:
            return

        for script_folder in self.script_folders.split(";"):
            if not script_folder:  # ignore empty strings
                continue

            if not os.path.exists(script_folder):
                continue

            self.dynamic_classes_from_script_folder(script_folder)

        if len(self.dynamic_classes.keys()) > 0:
            print("Generated: {} tool(s) from files in: {}".format(len(self.dynamic_classes), self.script_folders))

        # generate classes user specified script paths
        user_script_classes = self.dynamic_classes_from_user_settings()
        if len(user_script_classes):
            print("Generated: {} tool(s) from user scripts".format(len(user_script_classes)))

        self.dynamic_classes_generated = True

    def dynamic_classes_from_script_folder(self, script_folder):
        """Find all scripts in folder structure and add them as tool classes"""
        for script_path in get_paths_in_folder(script_folder, extension_filter=".py"):
            self.dynamic_class_from_script(script_path)

    def dynamic_classes_from_user_settings(self):
        """Generate classes for all user specified script paths"""
        script_classes = []
        for user_script_path in self.settings.get_value(lk.user_script_paths, default=list()):
            if not os.path.exists(user_script_path):
                print("Script path does not exist: {}".format(user_script_path))
                continue

            script_cls = self.dynamic_class_from_script(user_script_path)
            if not script_cls:
                continue

            script_cls.IS_USER_SCRIPT = True
            script_classes.append(script_cls)

        return script_classes

    # for dynamic class creation in custom modules
    def dynamic_class_from_script(self, script_path):
        script_name = os.path.splitext(os.path.basename(script_path))[0]
        if script_name in self.dynamic_classes.keys():
            return

        script_cls = make_class_from_script(script_path, tool_name=script_name)

        self.dynamic_classes[script_name] = script_cls

        return script_cls


lk = LocalConstants()


class _InternalToolDockItemBase(QtWidgets.QWidget):
    """
    Internal Base Class for tools logic
    """
    TOOL_NAME = "TOOL"
    TOOL_LABEL = None  # will be same as TOOL_NAME unless specified
    TOOL_TIP = "TOOLTIP UNDEFINED"
    BACKGROUND_COLOR = None
    ICON = None
    REGISTER_SCENE_CALLBACK = False

    SCRIPT_PATH = None  # used by dynamically generated classes
    IS_USER_SCRIPT = False  # is set to true for dynamically generated user scripts

    def __init__(self, *args, **kwargs):
        super(_InternalToolDockItemBase, self).__init__(*args, **kwargs)
        if not self.TOOL_LABEL:
            self.TOOL_LABEL = self.TOOL_NAME

        self.settings = lk.settings

        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        # right click menu
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)
        self.context_menu_actions = []

        self._internal_context_menu_actions = [
            {"Set Label": self.open_button_label_editor},
            {"Set Background Color": self.open_background_color_picker},
            "-",
            {"Set Splitter - Vertical": partial(self.set_splitter_orientation, True)},
            {"Set Splitter - Horizontal": partial(self.set_splitter_orientation, False)},
            "-",
            {"Reset Label": self.reset_tool_label},
            {"Reset Background Color": self.reset_background_color},
        ]

        if self.SCRIPT_PATH:
            self.context_menu_actions.insert(
                0, {"Open in Script Editor": partial(dcc_interface.open_script_in_editor, self.SCRIPT_PATH)}
            )
            self.context_menu_actions.insert(1, "-")

        # register scene change callback
        self._tool_callbacks = []
        if self.REGISTER_SCENE_CALLBACK:
            self._tool_callbacks.extend(dcc_interface.register_scene_change_callback(self._on_scene_change))

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
        self.main_ui_widget = self.build_ui_widget()
        self.main_splitter.addWidget(self.main_ui_widget)

        # default hide parameter grid
        self.main_splitter.handle(1).setEnabled(False)
        self.main_splitter.setSizes([0, 100])
        self.main_layout.addWidget(self.main_splitter)

        ####################################################################
        # get user color override
        self._default_background_color = self.BACKGROUND_COLOR

        user_colors = self.settings.get_value(lk.user_colors, default=dict())
        user_color_override = user_colors.get(self.TOOL_NAME)
        if user_color_override:
            self.BACKGROUND_COLOR = user_color_override

        if self.BACKGROUND_COLOR:
            self.set_background_color(self.BACKGROUND_COLOR)

        ####################################################################
        # get user label override
        self._default_label = self.TOOL_LABEL

        user_labels = self.settings.get_value(lk.user_labels, default=dict())
        user_label_override = user_labels.get(self.TOOL_NAME)
        if user_label_override is not None:
            self.TOOL_LABEL = user_label_override
        self.set_tool_label(self.TOOL_LABEL)

    def open_context_menu(self):
        action_list = copy(self.context_menu_actions)
        action_list.append("-")
        action_list.extend(self._internal_context_menu_actions)
        return ui_utils.build_menu_from_action_list(action_list)

    def auto_populate_parameters(self):
        """Convenience function for generating parameters based on arguments of 'run'"""
        run_arguments = get_func_arguments(self.run)

        if not run_arguments:
            return

        # ignore 'self' argument, should be safe-ish
        if "self" in list(run_arguments.keys()):
            run_arguments.pop("self")

        for param_name, default_value in run_arguments.items():
            is_required = default_value == RequiresValueType
            if is_required:
                run_arguments[param_name] = str()  # fill to make sure every argument has something

        if run_arguments:
            self.param_grid.from_data(run_arguments)
            self._parameters_auto_generated = True

    def set_splitter_orientation(self, vertical=True):
        orientation = QtCore.Qt.Vertical if vertical else QtCore.Qt.Horizontal
        self.main_splitter.setOrientation(orientation)

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
                btn = ui_utils.ContentResizeButton(name)
                btn.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)

                btn.clicked.connect(partial(self._run, func))
                multi_button_layout.addWidget(btn)

            multi_button_widget = QtWidgets.QWidget()
            multi_button_widget.setLayout(multi_button_layout)
            main_widget = multi_button_widget
        else:
            btn = ui_utils.ContentResizeButton("{}".format(self.TOOL_NAME))
            btn.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
            btn.clicked.connect(self._run)

            # set Icon on button
            if self.ICON:
                # if it's a string, assume it's a path to an icon image
                if isinstance(self.ICON, str):
                    self.ICON = QtGui.QIcon(self.ICON)
                btn.setIcon(self.ICON)

            main_widget = btn

        return main_widget

    def open_background_color_picker(self):
        new_color = ui_utils.open_color_picker(current_color=self.BACKGROUND_COLOR,
                                               color_signal=self.set_background_color)
        if new_color:
            color_values = new_color.getRgb()[:3]

            # store values in instance and settings
            self.BACKGROUND_COLOR = color_values
            self.settings.set_user_color(self.TOOL_NAME, color=color_values)

            self.set_background_color(new_color)

        else:
            self.set_background_color(self.BACKGROUND_COLOR)

    def set_background_color(self, color):
        if isinstance(color, QtGui.QColor):
            color = color.getRgb()[:3]

        param_grid_header = self.param_grid.header()  # type: QtWidgets.QHeaderView

        # reset colors
        if color is None:
            self.main_ui_widget.setStyleSheet("")
            self.param_grid.setStyleSheet("")
            param_grid_header.setStyleSheet("")
            return

        # use subtler color equivalent for parameter grid
        col = QtGui.QColor()
        col.setRgb(*color)
        col.setHsv(col.hue(), col.saturation() * 0.5, col.value() * 0.5)
        subtle_color = col.getRgb()[:3]

        # set colors on widgets
        self.main_ui_widget.setStyleSheet(background_form.format(*color))
        self.param_grid.setStyleSheet("QTreeView{{background-color:rgb({},{},{})}}".format(*subtle_color))
        param_grid_header.setStyleSheet(background_form.format(*color))

    def reset_background_color(self):
        self.set_background_color(self._default_background_color)
        self.settings.set_user_color(self.TOOL_NAME, color=None)

    def open_button_label_editor(self):
        if not isinstance(self.main_ui_widget, QtWidgets.QPushButton):
            # TODO: add support for multiple tool buttons
            return

        current_text = self.main_ui_widget.text()
        new_text, ok = QtWidgets.QInputDialog.getText(self, "New Tool Label",
                                                      "Enter new tool label for: {}".format(self.TOOL_NAME),
                                                      text=current_text)
        if ok:
            self.settings.set_user_label(self.TOOL_NAME, new_text)
            self.set_tool_label(new_text)
            self.TOOL_LABEL = new_text

    def set_tool_label(self, label):
        if not isinstance(self.main_ui_widget, QtWidgets.QPushButton):
            return
        self.main_ui_widget.setText(label)
        # trigger resize event so text scale gets updated
        self.main_ui_widget.resizeEvent(QtGui.QResizeEvent(self.main_ui_widget.size(), QtCore.QSize()))

    def reset_tool_label(self):
        self.set_tool_label(self._default_label)
        self.settings.set_user_label(self.TOOL_NAME, label=None)

    def deleteLater(self):
        self._remove_callbacks()
        super(_InternalToolDockItemBase, self).deleteLater()

    def _remove_callbacks(self):
        [dcc_interface.remove_callback(c) for c in self._tool_callbacks]
        self._tool_callbacks = []

    def post_init(self):
        # auto generate parameter widgets if run function has arguments
        # skip if parameters have been manually defined
        if not self.param_grid.parameters:
            self.auto_populate_parameters()

        # show parameter grid if parameters are defined
        if self.param_grid.parameters:
            self.main_splitter.handle(1).setEnabled(True)
            self.main_splitter.setSizes([1, 1])
        else:
            self.main_splitter.setHandleWidth(0)

    def _on_scene_change(self, *args, **kwargs):
        """internal method because maya callbacks sends args and I don't want to have to define that everywhere"""
        self.on_scene_change()

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

    def on_scene_change(self):
        pass


class ToolDockItemBase(_InternalToolDockItemBase):
    """
    Base Class for tools to inherit from
    """
    pass


def import_extra_modules(refresh=False):
    modules_to_import = os.environ.get(lk.env_extra_modules, "").split(";")

    if refresh:
        for mod_key in sys.modules.keys():
            for module_import_str in modules_to_import:

                if not module_import_str:  # skip empty strings
                    continue

                # pop up out all submodule of imported module
                if module_import_str in mod_key:
                    sys.modules.pop(mod_key)
                    continue

            if mod_key.startswith(lk.extension_path_prefix):
                sys.modules.pop(mod_key)
                continue

    # search in sys.paths for tool_dock_ext modules and packages, then import them
    for sys_path in sys.path:
        if not os.path.isdir(sys_path):
            continue

        for sys_path_name in os.listdir(sys_path):

            # only import modules with this specific name at the start
            if not sys_path_name.startswith(lk.extension_path_prefix):
                continue

            module_name = os.path.splitext(sys_path_name)[0]
            modules_to_import.append(module_name)

    # remove potential duplicates
    modules_to_import = list(set(modules_to_import))

    # import modules defined in environment variable
    for module_import_str in modules_to_import:
        if not module_import_str:  # skip empty strings
            continue

        try:
            importlib.import_module(module_import_str)
            print("Imported tool_dock extension: {}".format(module_import_str))
        except Exception as e:
            traceback.print_exc()


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


def get_tool_classes():
    if not lk.dynamic_classes_generated:
        lk.generate_dynamic_classes()

    # get all base sub classes
    subclasses = list(all_subclasses(ToolDockItemBase))
    subclasses.extend(lk.dynamic_classes.values())
    return subclasses


def get_preview_from_script_path(script_path, max_line_count=None):
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


def get_preview_from_script_cls(tool_cls):
    preview_str = "{}\n\n{}".format(tool_cls.__module__, inspect.getsource(tool_cls.run))
    return preview_str


def get_preview_from_tool(tool_cls):
    if tool_cls.SCRIPT_PATH:
        script_preview_text = get_preview_from_script_path(tool_cls.SCRIPT_PATH)
    else:
        script_preview_text = get_preview_from_script_cls(tool_cls)

    return script_preview_text


def get_tool_tip_from_tool(tool_cls):
    return "{}\n{}".format(tool_cls.TOOL_NAME, tool_cls.TOOL_TIP)


def make_class_from_script(script_path, tool_name):
    class DynamicClass(_InternalToolDockItemBase):
        TOOL_NAME = tool_name
        TOOL_TIP = script_path
        SCRIPT_PATH = script_path

        def run(self):
            return runpy.run_path(script_path, init_globals=globals(), run_name="__main__")

    return DynamicClass


def get_paths_in_folder(root_folder, extension_filter=""):
    for folder, _, file_names in os.walk(root_folder):
        for file_name in file_names:
            if file_name.endswith(extension_filter):
                yield os.path.join(folder, file_name)


def browse_for_settings_path(save=False):
    dialog = QtWidgets.QFileDialog(ui_utils.get_app_window())
    dialog.setNameFilter("*.ini")

    if save:
        dialog.setAcceptMode(dialog.AcceptSave)
    else:
        dialog.setAcceptMode(dialog.AcceptOpen)

    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        return dialog.selectedFiles()[0]


def save_tooldock_settings(settings, current_tooldock, settings_path=None):
    """
    Save settings for current tooldock to standalone file for loading and saving

    :param settings:
    :param current_tooldock:
    :param settings_path:
    :return:
    """
    if settings_path is None:
        settings_path = browse_for_settings_path()

    if not settings_path:
        return

    out_settings = ToolDockSettings(settings_path, QtCore.QSettings.IniFormat)

    for setting_key in settings.allKeys():  # type: str
        if not setting_key.startswith(current_tooldock):
            continue
        out_settings.setValue(setting_key, settings.get_value(setting_key))

    out_settings.setValue("tooldock", current_tooldock)
    return settings_path


def load_tooldock_settings(target_settings=None, target_tooldock="", source_settings=None):
    """
    Load tooldock settings from standalone file into the target_settings

    :param target_settings:
    :param target_tooldock:
    :param source_settings:
    :return:
    """
    if source_settings is None:
        source_settings = browse_for_settings_path()

    if not source_settings:
        return

    if not isinstance(source_settings, ToolDockSettings):
        source_settings = ToolDockSettings(source_settings, QtCore.QSettings.IniFormat)

    settings_tooldock = source_settings.get_value("tooldock")

    for setting_key in source_settings.allKeys():  # type: str
        if not setting_key.startswith(settings_tooldock):
            continue

        # save data in current tooldock
        key = setting_key.replace(settings_tooldock, target_tooldock)

        target_settings.setValue(key, source_settings.get_value(setting_key))

    return True
