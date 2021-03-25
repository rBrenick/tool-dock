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
    from . import tool_dock_utils
    from tool_dock.examples import tool_dock_examples
    from . import tool_dock_ui

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

    reload(tool_dock_utils)
    reload(tool_dock_examples)
    reload(tool_dock_ui)
