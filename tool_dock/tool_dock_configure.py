# Standard
import os

# Tool
from tool_dock import tool_dock_utils as tdu
# UI
from tool_dock.ui import ui_utils
from tool_dock.ui.ui_utils import QtCore, QtWidgets, QtGui


class ToolDockConfigurationDialog(QtWidgets.QDialog):
    """
    Define which actions should be visible in the ToolDock
    """
    config_saved = QtCore.Signal(list)

    def __init__(self, parent=ui_utils.get_app_window(), active_tools=None, *args, **kwargs):
        super(ToolDockConfigurationDialog, self).__init__(parent=parent, *args, **kwargs)
        self.setWindowTitle("ToolDock Configuration")

        self.active_tools = active_tools
        self.tool_classes = {}

        self.ui = ToolDockConfigurationUI()
        self.setLayout(self.ui.main_layout)

        # connect signals
        self.ui.tools_LW.itemSelectionChanged.connect(self.preview_script)
        self.ui.tools_LW.itemDoubleClicked.connect(ui_utils.toggle_list_widget_item_checked)
        self.ui.save_BTN.clicked.connect(self.save_actions)
        self.ui.add_script_BTN.clicked.connect(self.open_add_script_dialog)

        # fill up tool list
        self.rebuild_ui()

        # set to a nicer size
        self.resize(QtCore.QSize(700, 400))

    def open_add_script_dialog(self):

        selected_files, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "Select script files", filter="*.py")
        if selected_files:
            add_scripts_to_user_paths(selected_files)
        self.rebuild_ui()

        # At some future point I'll probably need this more complicated UI for this.

        # win = AddScriptDialog(parent=self)
        # win.script_added.connect(self.rebuild_ui)
        # win.show()
        # return win

    def rebuild_ui(self):
        self.tool_classes = {cls.TOOL_NAME: cls for cls in tdu.get_tool_classes()}
        self.fill_tool_list()

    def preview_script(self):
        selected_items = self.ui.tools_LW.selectedItems()
        if not selected_items:
            return

        # last selected script will be previewed
        item = selected_items[-1]

        tool_cls = self.tool_classes.get(item.text())  # type: tdu.ToolDockItemBase

        script_preview_text = tdu.get_preview_from_tool(tool_cls)

        self.ui.script_preview_TE.setText(script_preview_text)

    def fill_tool_list(self):
        """Populate ListWidget with items"""
        self.ui.tools_LW.clear()

        sorted_tool_names = sorted(self.tool_classes.keys())

        for tool_name in sorted_tool_names:
            tool_cls = self.tool_classes.get(tool_name)  # type: tdu.ToolDockItemBase
            lwi = QtWidgets.QListWidgetItem(self.ui.tools_LW)
            lwi.setText(tool_name)
            lwi.setToolTip(tdu.get_tool_tip_from_tool(tool_cls))
            lwi.setFlags(lwi.flags() | QtCore.Qt.ItemIsUserCheckable)
            lwi.setCheckState(QtCore.Qt.Unchecked)

            if self.active_tools and tool_name in self.active_tools:
                lwi.setCheckState(QtCore.Qt.Checked)

    def save_actions(self):
        self.config_saved.emit(self.get_checked_tool_names())

    def get_checked_tool_names(self):
        checked_tool_names = []
        for tool_lwi in ui_utils.get_list_widget_items(self.ui.tools_LW):  # type:QtWidgets.QListWidgetItem
            if tool_lwi.checkState() == QtCore.Qt.Checked:
                checked_tool_names.append(tool_lwi.text())
        return checked_tool_names


class ToolDockConfigurationUI(QtWidgets.QWidget):
    """
    Define which actions should be visible in the ToolDock
    """

    def __init__(self, *args, **kwargs):
        super(ToolDockConfigurationUI, self).__init__(*args, **kwargs)
        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)

        # add splitter
        self.main_splitter = QtWidgets.QSplitter()
        self.main_layout.addWidget(self.main_splitter)

        # add tool list
        tools_layout = QtWidgets.QVBoxLayout()
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_widget = QtWidgets.QWidget(self)
        tools_widget.setLayout(tools_layout)

        self.tools_LW = QtWidgets.QListWidget()
        tools_layout.addWidget(self.tools_LW)

        self.add_script_BTN = QtWidgets.QPushButton("Add Script")
        tools_layout.addWidget(self.add_script_BTN)

        self.main_splitter.addWidget(tools_widget)

        # add preview tab
        self.script_preview_TE = QtWidgets.QTextEdit()
        self.script_preview_TE.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.script_preview_TE.setText("Script Preview")
        self.main_splitter.addWidget(self.script_preview_TE)

        # divide splitter in half
        self.main_splitter.setSizes([1, 1])

        # Save button
        self.save_BTN = QtWidgets.QPushButton("Save")
        self.main_layout.addWidget(self.save_BTN)


######################################################################################
# Add User Script
# THIS DIALOG IS CURRENTLY NOT USED. A FILE BROWSER WAS SUFFICIENT

class AddScriptDialog(QtWidgets.QDialog):
    """
    Add extra user defined scripts to list of tools
    """
    script_added = QtCore.Signal(str)

    def __init__(self, parent=ui_utils.get_app_window(), *args, **kwargs):
        super(AddScriptDialog, self).__init__(parent=parent, *args, **kwargs)
        self.setWindowTitle("Add Script to Tool List")

        self.settings = tdu.lk.settings

        self.ui = AddScriptUI()
        self.setLayout(self.ui.main_layout)

        # Connect signals
        self.ui.save_BTN.clicked.connect(self.save_script)

        self.resize(QtCore.QSize(500, 200))

    def save_script(self):
        script_text = self.ui.script_TE.toPlainText()
        if len(script_text.splitlines()) == 1:
            script_path = script_text.replace("\\", "/")
            if not os.path.exists(script_path):
                QtWidgets.QMessageBox.warning(self, "Path not found",
                                              "Path not found on disk:\n{}\n".format(script_path))
                return

            add_scripts_to_user_paths(script_path)

            # tell the configure dialog that something has been added
            self.script_added.emit(script_path)

        else:
            QtWidgets.QMessageBox.warning(self, "Only script paths supported",
                                          "Multi line input found. Currently only paths to script are supported")


class AddScriptUI(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(AddScriptUI, self).__init__(*args, **kwargs)

        self.main_layout = QtWidgets.QVBoxLayout()

        self.script_TE = QtWidgets.QTextEdit()
        self.script_TE.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.script_TE.setPlaceholderText("Script")
        self.main_layout.addWidget(self.script_TE)

        self.save_BTN = QtWidgets.QPushButton("Add Script")
        self.main_layout.addWidget(self.save_BTN)


def add_scripts_to_user_paths(script_paths):
    if not isinstance(script_paths, list):
        script_paths = [script_paths]

    user_script_paths = tdu.lk.settings.get_value(tdu.lk.user_script_paths, default=list())
    for script_path in script_paths:
        # add to settings
        user_script_paths.append(script_path)

        # generate class for current instance as well
        tdu.lk.dynamic_class_from_script(script_path)

    user_script_paths = list(set(user_script_paths))
    tdu.lk.settings.setValue(tdu.lk.user_script_paths, user_script_paths)
