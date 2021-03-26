# content
def main(*args, **kwargs):
    from tool_dock import tool_dock_ui
    return tool_dock_ui.main(*args, **kwargs)


def reload_module(full_refresh=False):
    import sys
    if sys.version_info[0] >= 3:
        from importlib import reload
    else:
        from imp import reload

    from .ui import ui_utils
    from .examples import tool_dock_examples
    from . import tool_dock_utils
    from . import tool_dock_configure
    from . import tool_dock_ui
    from . import dcc

    # wipe all the scene callbacks before losing the connections via the reloads
    tool_dock_utils.dcc_interface.remove_all_callbacks()

    # custom wonky reload things here
    for window_index, tooldock_window in ui_utils.wh.windows.items():
        to_remove = False
        try:
            if not tooldock_window.isVisible():
                tooldock_window.deleteLater()
                to_remove = True
        except Exception as e:
            to_remove = True
        finally:
            if to_remove:
                ui_utils.wh.windows.pop(window_index)

    if full_refresh:  # under conditional argument because WindowHandler class is defined here
        reload(ui_utils)

    reload(dcc.base_dcc_module)
    reload(dcc.active_dcc_module)
    reload(tool_dock_utils)
    reload(tool_dock_examples)
    tool_dock_utils.import_extra_modules(refresh=True)
    reload(tool_dock_configure)
    reload(tool_dock_ui)
