__author__ = "Richard Brenick"
__created__ = "2021-03-13"
__modified__ = "2021-03-13"

# Standard

# Tool
from dcc_toolbox import dcc_toolbox_utils as dtu

# UI
from dcc_toolbox.ui import ui_utils
from dcc_toolbox.ui.ui_utils import QtCore, QtWidgets

try:
    # subclasses defined in here will be read on window initialization
    from dcc_toolbox import dcc_toolbox_examples
except Exception as e:
    print(e)


class ToolBoxWindow(ui_utils.DockableWidget, QtWidgets.QMainWindow):
    docking_object_name = "ToolBox"

    def __init__(self, instance_number=0, *args, **kwargs):
        super(ToolBoxWindow, self).__init__(*args, **kwargs)
        self.instance_number = instance_number
        self.setWindowTitle("ToolBoxWindow_{}".format(self.instance_number))

        self.dock_widgets = []
        self.settings = dtu.ToolBoxSettings()

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
        menu_bar.addAction("Configure", self.configure_toolbox)
        layout_menu = menu_bar.addMenu("Layout")
        layout_menu.addAction("Set Window Name", self.ui_set_window_title)
        layout_menu.addAction("Save Layout", self.save_ui_settings)
        layout_menu.addAction("Load Layout", self.load_ui_settings)

        self.active_toolbox = "toolbox_{}".format(self.instance_number)
        self.k_active_tools = "{}/tools".format(self.active_toolbox)
        self.k_win_geometry = "{}/window_geometry".format(self.active_toolbox)
        self.k_win_state = "{}/window_state".format(self.active_toolbox)

        self.build_toolbox_display()

        self.load_ui_settings()

    def configure_toolbox(self):
        active_tools = self.settings.value(self.k_active_tools, defaultValue=list())
        win = ToolBoxConfigurationDialog(self, active_tools=active_tools)
        win.config_saved.connect(self.save_user_toolbox)
        return win.show()

    def save_user_toolbox(self, tool_names):
        self.save_ui_settings()
        self.settings.setValue(self.k_active_tools, tool_names)
        self.build_toolbox_display()
        self.load_ui_settings()

    def build_toolbox_display(self):
        # remove any existing toolbox dock widgets
        for dock_widget in self.dock_widgets:  # type: QtWidgets.QDockWidget
            dock_widget.close()
            dock_widget.deleteLater()
        self.dock_widgets = []

        # wait for deleteLater to finish
        ui_utils.process_q_events()

        active_tools = self.settings.value(self.k_active_tools, defaultValue=list())

        for toolbox_item_cls in dtu.all_subclasses(dtu.ToolBoxItemBase):
            if toolbox_item_cls.TOOL_NAME not in active_tools:  # only build for selected window actions
                continue

            dock = QtWidgets.QDockWidget(toolbox_item_cls.TOOL_NAME, self)

            clean_tool_name = toolbox_item_cls.__name__.replace(" ", "_")
            dock_object_name = "{}_{}_QtObject".format(clean_tool_name, self.instance_number)
            dock.setObjectName(dock_object_name)

            tool_widget = toolbox_item_cls()  # type:dtu.ToolBoxItemBase
            dock.setWidget(tool_widget)

            self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)
            self.dock_widgets.append(dock)

    def ui_set_window_title(self):
        val, ok = QtWidgets.QInputDialog.getText(self, "New Window Title", "Enter New Title",
                                                 QtWidgets.QLineEdit.Normal,
                                                 text=ui_utils.get_window_title(self)
                                                 )
        if ok:
            self.setWindowTitle(val)

    def load_ui_settings(self):
        window_geometry = self.settings.value(self.k_win_geometry)
        window_state = self.settings.value(self.k_win_state)
        if window_geometry and window_state:
            print("loading ui settings: {}".format(self.k_active_tools))
            self.restoreGeometry(window_geometry)
            self.restoreState(window_state)

    def save_ui_settings(self):
        self.settings.setValue(self.k_win_geometry, self.saveGeometry())
        self.settings.setValue(self.k_win_state, self.saveState())

    def closeEvent(self, event):
        self.save_ui_settings()
        super(ToolBoxWindow, self).closeEvent(event)


class ToolBoxConfigurationDialog(QtWidgets.QDialog):
    """
    Define which actions should be visible in the ToolBox
    """
    config_saved = QtCore.Signal(list)

    def __init__(self, parent=ui_utils.get_app_window(), active_tools=None, *args, **kwargs):
        super(ToolBoxConfigurationDialog, self).__init__(parent=parent, *args, **kwargs)
        self.setWindowTitle("Toolbox Configuration")

        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        self.tools_LW = QtWidgets.QListWidget()
        self.tools_LW.itemDoubleClicked.connect(ui_utils.toggle_list_widget_item_checked)
        self.fill_tool_list(active_tools)
        main_layout.addWidget(self.tools_LW)

        # Save Button
        save_button = QtWidgets.QPushButton("Save")
        save_button.clicked.connect(self.save_actions)
        main_layout.addWidget(save_button)

    def fill_tool_list(self, active_tools):
        """Populate ListWidget with items"""
        all_tool_names = sorted([cls.TOOL_NAME for cls in dtu.all_subclasses(dtu.ToolBoxItemBase)])

        for tool_name in all_tool_names:
            lwi = QtWidgets.QListWidgetItem(self.tools_LW)
            lwi.setText(tool_name)
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


def main(restore=False, force_refresh=False):
    restore_script = "import dcc_toolbox; dcc_toolbox.main(restore=True)"

    return ui_utils.create_dockable_widget(ToolBoxWindow,
                                           restore=restore,
                                           restore_script=restore_script,
                                           force_refresh=force_refresh
                                           )


if __name__ == '__main__':
    main()
