__author__ = "Richard Brenick"
__created__ = "2021-03-13"
__modified__ = "2021-03-13"

# Standard

# Tool
import sys

from tool_dock import tool_dock_utils as tdu
# UI
from tool_dock.ui import ui_utils
from tool_dock.ui.ui_utils import QtCore, QtWidgets, QtGui

try:
    # subclasses defined in here will be read on window initialization
    from tool_dock.examples import tool_dock_examples

    # Extra module paths can be defined via an environment variable
    # These paths will then be imported on startup
    # for use by pipelines that wish to add their own tools in this system
    tdu.import_extra_modules()
    # Example of how to set the variable (this would have to happen before the DCC starts up, or early in it)
    # os.environ["TOOL_DOCK_EXTRA_MODULES"] = "a_module;another_module"

except Exception as e:
    print(e)


class ToolDockWindow(ui_utils.DockableWidget, QtWidgets.QMainWindow):
    docking_object_name = "ToolDock"

    def __init__(self, window_index=0, *args, **kwargs):
        super(ToolDockWindow, self).__init__(*args, **kwargs)
        self.window_index = window_index
        self.setWindowTitle("ToolDockWindow_{}".format(self.window_index))

        self.dock_widgets = []
        self.title_bar_widgets = {}
        self.settings = tdu.ToolDockSettings(QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope, 'tool_dock')

        # add a static widget to dock other widgets around
        self.central_widget = QtWidgets.QWidget()
        self.central_widget.setMaximumWidth(0)
        self.setCentralWidget(self.central_widget)

        # set docking options
        self.setDockNestingEnabled(True)
        self.setTabPosition(QtCore.Qt.TopDockWidgetArea, QtWidgets.QTabWidget.TabPosition.North)
        self.setTabPosition(QtCore.Qt.LeftDockWidgetArea, QtWidgets.QTabWidget.TabPosition.North)
        self.setTabPosition(QtCore.Qt.RightDockWidgetArea, QtWidgets.QTabWidget.TabPosition.North)
        self.setTabPosition(QtCore.Qt.BottomDockWidgetArea, QtWidgets.QTabWidget.TabPosition.North)

        # create docks for each subclassed tool widget
        menu_bar = self.menuBar()  # type: QtWidgets.QMenuBar
        menu_bar.addAction("Configure", self.configure_tooldock)
        layout_menu = menu_bar.addMenu("Layout")  # type: QtWidgets.QMenu
        layout_menu.addAction("Set Window Name", self.ui_set_window_title)
        layout_menu.addAction("Lock Layout", self.ui_lock_layout)
        layout_menu.addAction("Unlock Layout", self.ui_unlock_layout)
        layout_menu.addSeparator()
        layout_menu.addAction("Save Layout", self.ui_save_settings)
        layout_menu.addAction("Load Layout", self.ui_load_settings)
        layout_menu.addSeparator()
        layout_menu.addAction("Save Layout File", self.save_settings_to_file)
        layout_menu.addAction("Load Layout File", self.load_settings_from_file)

        # setting strings
        self.active_tooldock = "tooldock_{}".format(self.window_index)
        self.k_active_tools = "{}/tools".format(self.active_tooldock)
        self.k_win_geometry = "{}/window_geometry".format(self.active_tooldock)
        self.k_win_state = "{}/window_state".format(self.active_tooldock)
        self.k_layout_locked = "{}/layout_locked".format(self.active_tooldock)
        self.k_tool_splitters = "{}/tool_splitters".format(self.active_tooldock)
        self.k_param_grid_ui = "{}/param_grid".format(self.active_tooldock)

        # a timer can also be used for triggering the load settings
        # for some reason this sometimes works better than any qt refresh option
        self.ui_load_settings_timer = QtCore.QTimer()
        self.ui_load_settings_timer.setSingleShot(True)
        self.ui_load_settings_timer.timeout.connect(self.ui_load_settings)

        # build dock widgets for all configured tools
        self.ui_build_tool_widgets()
        self.ui_load_settings()

    def ui_build_tool_widgets(self):
        # remove any existing tooldock dock widgets
        for dock_widget in self.dock_widgets:  # type: QtWidgets.QDockWidget
            dock_widget.close()
            dock_widget.deleteLater()
        self.dock_widgets = []

        # wait for deleteLater to finish
        ui_utils.process_q_events()

        active_tools = self.settings.value(self.k_active_tools, defaultValue=list())

        for tool_item_cls in tdu.get_tool_classes():  # type: tdu.ToolDockItemBase
            if tool_item_cls.TOOL_NAME not in active_tools:  # only build for selected window actions
                continue

            dock = QtWidgets.QDockWidget(tool_item_cls.TOOL_NAME, self)

            clean_tool_name = tool_item_cls.__name__.replace(" ", "_")
            dock_object_name = "{0}_QtObject".format(clean_tool_name)
            dock.setObjectName(dock_object_name)

            tool_widget = tool_item_cls()  # type:tdu.ToolDockItemBase
            tool_widget.post_init()
            dock.setWidget(tool_widget)
            dock.setToolTip(tool_item_cls.TOOL_TIP)

            self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)
            self.dock_widgets.append(dock)

    def ui_load_settings(self):
        print("loading ui settings: {}".format(self.active_tooldock))

        # restore dock widget layouts
        window_geometry = self.settings.value(self.k_win_geometry)
        window_state = self.settings.value(self.k_win_state)
        if window_geometry and window_state:
            self.restoreGeometry(window_geometry)
            self.restoreState(window_state)

        # restore splitters between parameter_grid and run button
        dock_splitters = self.settings.value(self.k_tool_splitters)
        if dock_splitters:
            for dock_widget in self.dock_widgets:
                tool_item = dock_widget.widget()  # type:tdu.ToolDockItemBase
                splitter_data = dock_splitters.get(tool_item.TOOL_NAME)
                if not splitter_data:
                    continue

                if not isinstance(splitter_data, dict):
                    print("Could not restore splitter ui from: {}".format(splitter_data))
                    continue

                s_sizes = splitter_data.get("sizes")
                s_orientation = QtCore.Qt.Horizontal if splitter_data.get("orientation") == 1 else QtCore.Qt.Vertical

                tool_item.main_splitter.setSizes(s_sizes)
                tool_item.main_splitter.setOrientation(s_orientation)

        # restore parameter_grid header sizes
        parameter_grid_ui_settings = self.settings.value(self.k_param_grid_ui)
        if parameter_grid_ui_settings:
            for dock_widget in self.dock_widgets:
                tool_item = dock_widget.widget()  # type:tdu.ToolDockItemBase
                tool_param_grid = parameter_grid_ui_settings.get(tool_item.TOOL_NAME)
                if not tool_param_grid:
                    continue
                tool_item.param_grid.set_ui_settings(tool_param_grid)

        if self.settings.get_value(self.k_layout_locked, default=False):
            self.ui_lock_layout()

    def ui_save_settings(self):
        # store dock widget layouts
        self.settings.setValue(self.k_win_geometry, self.saveGeometry())
        self.settings.setValue(self.k_win_state, self.saveState())

        # store splitter size between parameter_grid and run button
        # store size of parameter_grid header sections
        tool_splitters = {}
        parameter_grids = {}
        for dock_widget in self.dock_widgets:  # type: QtWidgets.QDockWidget
            tool_item = dock_widget.widget()  # type:tdu.ToolDockItemBase

            # save parameter_grid settings
            parameter_grids[tool_item.TOOL_NAME] = tool_item.param_grid.get_ui_settings()

            # save main_splitter settings
            splitter_data = dict()
            splitter_data["sizes"] = tool_item.main_splitter.sizes()
            splitter_data["orientation"] = tool_item.main_splitter.orientation()
            tool_splitters[tool_item.TOOL_NAME] = splitter_data

        self.settings.setValue(self.k_tool_splitters, tool_splitters)
        self.settings.setValue(self.k_param_grid_ui, parameter_grids)
        print("Saved UI settings {}".format(self.active_tooldock))

    def configure_tooldock(self):
        """Choose which tools should be displayed for this tooldock"""
        active_tools = self.settings.value(self.k_active_tools, defaultValue=list())
        win = ToolDockConfigurationDialog(self, active_tools=active_tools)
        win.config_saved.connect(self.save_user_tooldock)
        return win.show()

    def save_user_tooldock(self, tool_names):
        """Save list of tool_names for this tooldock"""
        self.ui_save_settings()
        self.settings.setValue(self.k_active_tools, tool_names)
        self.ui_build_tool_widgets()
        self.ui_load_settings_timer.start(1)

    def ui_set_window_title(self):
        val, ok = QtWidgets.QInputDialog.getText(self, "New Window Title", "Enter New Title",
                                                 QtWidgets.QLineEdit.Normal,
                                                 text=ui_utils.get_window_title(self)
                                                 )
        if ok:
            self.setWindowTitle(val)

    def ui_lock_layout(self):
        for dock in self.dock_widgets:  # type:QtWidgets.QDockWidget
            self.title_bar_widgets[dock] = dock.titleBarWidget()
            dock.setTitleBarWidget(QtWidgets.QWidget(dock))
        self.settings.setValue(self.k_layout_locked, True)

    def ui_unlock_layout(self):
        for dock, dock_title_bar in self.title_bar_widgets.items():  # type:QtWidgets.QDockWidget
            try:
                dock.setTitleBarWidget(dock_title_bar)
            except RuntimeError as e:
                print(e)
        self.title_bar_widgets.clear()
        self.settings.setValue(self.k_layout_locked, False)

    def save_settings_to_file(self):
        self.ui_save_settings()
        new_path = tdu.save_tooldock_settings(self.settings, current_tooldock=self.active_tooldock)
        if new_path:
            print("Saved Layout to: {}".format(new_path))

    def load_settings_from_file(self):
        load_success = tdu.load_tooldock_settings(target_settings=self.settings,
                                                  target_tooldock=self.active_tooldock)
        if load_success:
            self.ui_build_tool_widgets()
            # Wut? for some reason just putting this in a timer works while the other refresh functions don't
            self.ui_load_settings_timer.start(1)
            # ui_utils.process_q_events()
            # self.update()
            # self.repaint()
            # self.resize(self.size())
            # self.updateGeometry()
            # self.load_ui_settings()

    # TODO: this event doesn't seem to trigger when using MayaQWidgetDockableMixin
    def closeEvent(self, event):
        self.ui_save_settings()
        super(ToolDockWindow, self).closeEvent(event)


class ToolDockConfigurationDialog(QtWidgets.QDialog):
    """
    Define which actions should be visible in the ToolDock
    """
    config_saved = QtCore.Signal(list)

    def __init__(self, parent=ui_utils.get_app_window(), active_tools=None, *args, **kwargs):
        super(ToolDockConfigurationDialog, self).__init__(parent=parent, *args, **kwargs)
        self.setWindowTitle("ToolDock Configuration")

        self.tool_classes = {cls.TOOL_NAME: cls for cls in tdu.get_tool_classes()}

        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        # add splitter
        self.main_splitter = QtWidgets.QSplitter()
        main_layout.addWidget(self.main_splitter)

        # add tool list
        self.tools_LW = QtWidgets.QListWidget()
        self.tools_LW.itemSelectionChanged.connect(self.preview_script)
        self.tools_LW.itemDoubleClicked.connect(ui_utils.toggle_list_widget_item_checked)
        self.fill_tool_list(active_tools)
        self.main_splitter.addWidget(self.tools_LW)

        # add preview tab
        self.script_preview_TE = QtWidgets.QTextEdit()
        self.script_preview_TE.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.script_preview_TE.setText("Script Preview")
        self.main_splitter.addWidget(self.script_preview_TE)

        # divide splitter in half
        self.main_splitter.setSizes([sys.maxint, sys.maxint])

        # Save Button
        save_button = QtWidgets.QPushButton("Save")
        save_button.clicked.connect(self.save_actions)
        main_layout.addWidget(save_button)

        # set to a nicer size
        self.resize(QtCore.QSize(700, 400))

    def preview_script(self):
        selected_items = self.tools_LW.selectedItems()
        if not selected_items:
            return

        # last selected script will be previewed
        item = selected_items[-1]

        tool_cls = self.tool_classes.get(item.text())  # type: tdu.ToolDockItemBase

        script_preview_text = tdu.get_preview_from_tool(tool_cls)

        self.script_preview_TE.setText(script_preview_text)

    def fill_tool_list(self, active_tools):
        """Populate ListWidget with items"""
        sorted_tool_names = sorted(self.tool_classes.keys())

        for tool_name in sorted_tool_names:
            tool_cls = self.tool_classes.get(tool_name)  # type: tdu.ToolDockItemBase
            lwi = QtWidgets.QListWidgetItem(self.tools_LW)
            lwi.setText(tool_name)
            lwi.setToolTip(tool_cls.TOOL_TIP)
            lwi.setFlags(lwi.flags() | QtCore.Qt.ItemIsUserCheckable)
            lwi.setCheckState(QtCore.Qt.Unchecked)

            if active_tools and tool_name in active_tools:
                lwi.setCheckState(QtCore.Qt.Checked)

    def save_actions(self):
        self.config_saved.emit(self.get_checked_tool_names())

    def get_checked_tool_names(self):
        checked_tool_names = []
        for tool_lwi in ui_utils.get_list_widget_items(self.tools_LW):  # type:QtWidgets.QListWidgetItem
            if tool_lwi.checkState() == QtCore.Qt.Checked:
                checked_tool_names.append(tool_lwi.text())
        return checked_tool_names


def main(restore=False, force_refresh=False, index=None):
    restore_script = "import tool_dock; tool_dock.main(restore=True, index={})"

    return ui_utils.create_dockable_widget(ToolDockWindow,
                                           restore=restore,
                                           restore_script=restore_script,
                                           force_refresh=force_refresh,
                                           window_index=index
                                           )


if __name__ == '__main__':
    main()
