__author__ = "Richard Brenick"
__created__ = "2021-03-13"
__modified__ = "2021-03-13"

# Standard

# Tool

from tool_dock import tool_dock_configure as tdc
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

        self.tool_dock_widgets = []
        self.spacer_dock_widgets = []
        self.title_bar_widgets = {}
        self.settings = tdu.lk.settings  # type: tdu.ToolDockSettings

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
        self.tool_bar = QtWidgets.QToolBar("Tool Dock Menu")
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.tool_bar)

        # configure tools action
        configure_action = QtWidgets.QAction(ui_utils.create_qicon("configure"), "Configure", self)
        configure_action.triggered.connect(self.configure_tooldock)
        self.tool_bar.addAction(configure_action)

        # make id for new_tool_check
        config_widget = self.tool_bar.widgetForAction(configure_action)
        config_widget.setObjectName("configure")

        # Layout button
        layout_tool_button = QtWidgets.QToolButton(self)
        layout_tool_button.setText("Layout")
        layout_tool_button.setIcon(ui_utils.create_qicon("layout"))
        layout_tool_button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        # add layout menu
        layout_tool_button.setStyleSheet("QToolButton::menu-indicator{width:0px;}")
        layout_tool_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        layout_menu = QtWidgets.QMenu(layout_tool_button)
        layout_tool_button.setMenu(layout_menu)

        layout_menu.addAction("Lock Layout", self.ui_lock_layout)
        layout_menu.addAction("Unlock Layout", self.ui_unlock_layout)
        layout_menu.addSeparator()
        layout_menu.addAction("Save Layout", self.ui_save_settings)
        layout_menu.addAction("Load Layout", self.ui_load_settings)
        layout_menu.addSeparator()
        layout_menu.addAction("Save Layout File", self.save_settings_to_file)
        layout_menu.addAction("Load Layout File", self.load_settings_from_file)
        self.tool_bar.addWidget(layout_tool_button)

        # Extra actions
        self.tool_bar.addAction(QtWidgets.QAction("Set Name", self, triggered=self.ui_set_window_title))
        self.tool_bar.addAction(QtWidgets.QAction("Add Spacer", self, triggered=self.ui_add_spacer))
        self.tool_bar.addAction(QtWidgets.QAction("Set Text Padding", self, triggered=self.set_button_padding))

        # setting strings
        self.active_tooldock = "tooldock_{}".format(self.window_index)
        self.k_active_tools = "{}/tools".format(self.active_tooldock)
        self.k_win_geometry = "{}/window_geometry".format(self.active_tooldock)
        self.k_win_state = "{}/window_state".format(self.active_tooldock)
        self.k_layout_locked = "{}/layout_locked".format(self.active_tooldock)
        self.k_tool_splitters = "{}/tool_splitters".format(self.active_tooldock)
        self.k_param_grid_ui = "{}/param_grid".format(self.active_tooldock)
        self.k_spacer_count = "{}/spacer_count".format(self.active_tooldock)

        # a timer can also be used for triggering the load settings
        # for some reason this sometimes works better than any qt refresh option
        self.ui_load_settings_timer = QtCore.QTimer()
        self.ui_load_settings_timer.setSingleShot(True)
        self.ui_load_settings_timer.timeout.connect(self.ui_load_settings)

        # set button text padding from settings
        # (important that this happens before ui_build_tool_widgets)
        button_padding = self.settings.get_value(tdu.lk.button_text_padding_multiplier,
                                                 default=ui_utils.ContentResizeButton.TEXT_PADDING_MULTIPLIER)
        ui_utils.ContentResizeButton.TEXT_PADDING_MULTIPLIER = button_padding

        # build dock widgets for all configured tools
        self.ui_build_tool_widgets()
        self.ui_load_settings_timer.start(0)

        # after initialization, update UI if new tools are available
        self.ui_update_new_tools_display()

    def ui_build_tool_widgets(self):
        # remove any existing tooldock dock widgets
        for dock_widget in self.tool_dock_widgets + self.spacer_dock_widgets:  # type: QtWidgets.QDockWidget
            tool_cls = dock_widget.widget()  # type: tdu.ToolDockItemBase
            if isinstance(tool_cls, tdu.ToolDockItemBase):
                tool_cls._remove_callbacks()
            dock_widget.close()
            dock_widget.deleteLater()
        self.tool_dock_widgets = []
        self.spacer_dock_widgets = []

        # wait for deleteLater to finish
        ui_utils.process_q_events()

        active_tools = self.settings.value(self.k_active_tools)
        if not active_tools:
            return

        for tool_item_cls in tdu.get_tool_classes():  # type: type(tdu.ToolDockItemBase)
            if tool_item_cls.TOOL_NAME not in active_tools:  # only build for selected window actions
                continue

            dock = QtWidgets.QDockWidget(tool_item_cls.TOOL_NAME, self)

            clean_tool_name = tool_item_cls.TOOL_NAME.replace(" ", "_")
            dock_object_name = "{0}_QtObject".format(clean_tool_name)
            dock.setObjectName(dock_object_name)

            tool_widget = tool_item_cls()  # type:tdu.ToolDockItemBase
            tool_widget.post_init()
            dock.setWidget(tool_widget)
            dock.setToolTip(tdu.get_tool_tip_from_tool(tool_item_cls))

            self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)
            self.tool_dock_widgets.append(dock)

        # add spacer widgets
        spacer_count = self.settings.get_value(self.k_spacer_count, default=0)
        for _ in range(spacer_count):
            self.ui_add_spacer()

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
            for dock_widget in self.tool_dock_widgets:
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
            for dock_widget in self.tool_dock_widgets:
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
        for dock_widget in self.tool_dock_widgets:  # type: QtWidgets.QDockWidget
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
        self.settings.setValue(self.k_spacer_count, len(self.spacer_dock_widgets))
        print("Saved UI settings {}".format(self.active_tooldock))

    def configure_tooldock(self):
        """Choose which tools should be displayed for this tooldock"""
        active_tools = self.settings.value(self.k_active_tools, defaultValue=list())
        win = tdc.ToolDockConfigurationDialog(self, active_tools=active_tools)
        win.config_saved.connect(self.save_user_tooldock)

        # save the tools list so we can check if new tools have been added in the future
        self.settings.set_tools_as_viewed()

        # update ui display
        self.ui_update_new_tools_display()

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

    def ui_add_spacer(self):
        dock = QtWidgets.QDockWidget("Spacer", self)

        dock_object_name = "_SPACER_{0}_QtObject".format(len(self.spacer_dock_widgets))
        dock.setObjectName(dock_object_name)

        # empty widget for spacer
        dock.setWidget(QtWidgets.QWidget())
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)

        # Build right click menu
        action_list = [
            {"Delete Spacer": lambda: self.ui_delete_spacer(dock)}
        ]

        dock.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        dock.customContextMenuRequested.connect(lambda: ui_utils.build_menu_from_action_list(action_list))

        self.spacer_dock_widgets.append(dock)

    def ui_delete_spacer(self, dock_widget):
        # Delete spacer UI
        dock_widget.close()
        dock_widget.deleteLater()
        self.spacer_dock_widgets.remove(dock_widget)

    def set_button_padding(self):
        win = tdc.ButtonPaddingConfigureDialog(self)
        win.slider_widget.value_set.connect(self.ui_refresh_buttons)
        win.show()

    def ui_refresh_buttons(self):
        for dock in self.tool_dock_widgets:
            dock_tool_widget = dock.widget()  # type: tdu.ToolDockItemBase
            main_widget = dock_tool_widget.main_ui_widget
            main_widget.resizeEvent(QtGui.QResizeEvent(main_widget.size(), QtCore.QSize()))

    def ui_lock_layout(self):
        for dock in self.tool_dock_widgets + self.spacer_dock_widgets:  # type:QtWidgets.QDockWidget
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

    def ui_update_new_tools_display(self):
        if self.are_new_tools_available():
            self.tool_bar.setStyleSheet("QToolButton#configure{background-color: rgb(40, 120, 40)}")
        else:
            self.tool_bar.setStyleSheet("")

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

    def are_new_tools_available(self):
        last_viewed_tools = self.settings.get_value(tdu.lk.last_viewed_tools, default=list())

        # tools have never been shown, so all tools are new
        if len(last_viewed_tools) == 0:
            return False

        for tool_cls in tdu.get_tool_classes():  # type: tdu.ToolDockItemBase
            if tool_cls.TOOL_NAME not in last_viewed_tools:
                return True  # new tool found, exit early
        return False

    # TODO: this event doesn't seem to trigger when using MayaQWidgetDockableMixin
    def closeEvent(self, event):
        self.ui_save_settings()
        super(ToolDockWindow, self).closeEvent(event)


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
