import os

import maya.OpenMaya as om
import pymel.core as pm

from . import tool_dock_dcc_base as dcc_base


class MayaToolDockInterface(dcc_base.BaseToolDockInterface):

    def open_script_in_editor(self, script_path):
        open_script(script_path)

    def register_scene_change_callback(self, func):
        callbacks = list()
        callbacks.append(om.MSceneMessage.addCallback(om.MSceneMessage.kAfterNew, func))
        callbacks.append(om.MSceneMessage.addCallback(om.MSceneMessage.kAfterOpen, func))
        self.callbacks.extend(callbacks)
        return callbacks

    def remove_callback(self, callback):
        try:
            om.MMessage.removeCallback(callback)
            self.callbacks.remove(callback)
        except Exception as e:
            print(e)


###########################
# Lots of this copied from https://github.com/rBrenick/script-tree

def open_script(script_path):
    """
    This is pretty much a duplicate of scriptEditorPanel.mel - global proc loadFileInNewTab(),
    but that function doesn't accept a path argument so we need to rebuild the logic

    :param script_path:
    :return:
    """
    if pm.mel.selectExecuterTabByName(script_path):  # tab exists, switch to it
        reload_selected_tab()
        return

    script_ext = os.path.splitext(script_path)[-1].lower()

    # create tab
    if script_ext == ".py":
        pm.mel.buildNewExecuterTab(-1, "Python", "python", 0)
    elif script_ext == ".mel":
        pm.mel.buildNewExecuterTab(-1, "MEL", "mel", 0)

    tabs = pm.melGlobals["$gCommandExecuterTabs"]
    tabs_layout = pm.tabLayout(tabs, q=True, ca=True)

    # Select newly created tab
    tabs_len = pm.tabLayout(tabs, q=True, numberOfChildren=True)
    pm.tabLayout(tabs, e=True, selectTabIndex=tabs_len)
    tab = tabs_layout[-1]

    # add script contents
    cmd_exec = pm.formLayout(tab, q=True, ca=True)[0]
    pm.cmdScrollFieldExecuter(cmd_exec, e=True, loadFile=script_path)

    # print(pm.cmdScrollFieldExecuter(cmd_exec, q=True, filename=True))

    # rename tab
    pm.mel.eval('renameCurrentExecuterTab("{}", 0);'.format(script_path))

    # hookup signals
    hookup_tab_signals(cmd_exec)


def reload_selected_tab():
    cmd_exec = get_selected_cmd_executer()
    script_path = pm.cmdScrollFieldExecuter(cmd_exec, q=True, filename=True)
    pm.cmdScrollFieldExecuter(cmd_exec, e=True, loadFile=script_path)


def hookup_tab_signals(cmd_exec):
    pm.cmdScrollFieldExecuter(cmd_exec, e=True,
                              modificationChangedCommand=lambda x: pm.mel.executerTabModificationChanged(x))
    pm.cmdScrollFieldExecuter(cmd_exec, e=True, fileChangedCommand=lambda x: pm.mel.executerTabFileChanged(x))


def get_selected_cmd_executer():
    tab_layout = pm.ui.TabLayout(pm.melGlobals["$gCommandExecuterTabs"])
    return pm.formLayout(tab_layout.getSelectTab(), q=True, ca=True)[0]
