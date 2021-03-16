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
    docking_object_name = "ToolBoxWindow"

    def __init__(self, *args, **kwargs):
        super(ToolBoxWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("ToolBoxWindow")

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

        self.user_toolbox_names = self.settings.value("user/toolbox", defaultValue=list())
        self.build_toolbox_display()

        self.load_ui_settings()

    def configure_toolbox(self):
        win = ToolBoxConfigurationDialog(self, user_toolbox_names=self.user_toolbox_names)
        win.config_saved.connect(self.save_user_toolbox)
        return win.show()

    def save_user_toolbox(self, tool_names):
        self.save_ui_settings()
        self.user_toolbox_names = tool_names
        self.settings.setValue("user/toolbox", tool_names)
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

        for toolbox_item_cls in dtu.all_subclasses(dtu.ToolBoxItemBase):
            if toolbox_item_cls.TOOL_NAME not in self.user_toolbox_names:  # only build for selected window actions
                continue

            dock = QtWidgets.QDockWidget(toolbox_item_cls.TOOL_NAME, self)
            dock.setObjectName(toolbox_item_cls.__name__.replace(" ", "_") + "_QtObject")

            tool_widget = toolbox_item_cls()  # type:dtu.ToolBoxItemBase
            dock.setWidget(tool_widget)

            self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)
            self.dock_widgets.append(dock)

    def load_ui_settings(self):
        window_geometry = self.settings.value(dtu.ToolBoxSettings.k_window_geometry)
        window_state = self.settings.value(dtu.ToolBoxSettings.k_window_state)
        if window_geometry and window_state:
            print("loading ui settings")
            self.restoreGeometry(window_geometry)
            self.restoreState(window_state)

    def save_ui_settings(self):
        self.settings.setValue(dtu.ToolBoxSettings.k_window_geometry, self.saveGeometry())
        self.settings.setValue(dtu.ToolBoxSettings.k_window_state, self.saveState())

    def closeEvent(self, event):
        self.save_ui_settings()
        super(ToolBoxWindow, self).closeEvent(event)


class ToolBoxConfigurationDialog(QtWidgets.QDialog):
    """
    Define which actions should be visible in the ToolBox
    """
    config_saved = QtCore.Signal(list)

    def __init__(self, parent=ui_utils.get_app_window(), user_toolbox_names=None, *args, **kwargs):
        super(ToolBoxConfigurationDialog, self).__init__(parent=parent, *args, **kwargs)
        self.setWindowTitle("Toolbox Configuration")

        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        self.tools_LW = QtWidgets.QListWidget()
        self.tools_LW.itemDoubleClicked.connect(ui_utils.toggle_list_widget_item_checked)
        self.fill_tool_list(user_toolbox_names)
        main_layout.addWidget(self.tools_LW)

        # Save Button
        save_button = QtWidgets.QPushButton("Save")
        save_button.clicked.connect(self.save_actions)
        main_layout.addWidget(save_button)

    def fill_tool_list(self, user_toolbox_names):
        """Populate ListWidget with items"""
        all_tool_names = sorted([cls.TOOL_NAME for cls in dtu.all_subclasses(dtu.ToolBoxItemBase)])

        for tool_name in all_tool_names:
            lwi = QtWidgets.QListWidgetItem(self.tools_LW)
            lwi.setText(tool_name)
            lwi.setFlags(lwi.flags() | QtCore.Qt.ItemIsUserCheckable)
            lwi.setCheckState(QtCore.Qt.Unchecked)

            if user_toolbox_names and tool_name in user_toolbox_names:
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
