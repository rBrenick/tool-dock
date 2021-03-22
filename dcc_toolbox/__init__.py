# content
def main(*args, **kwargs):
    from dcc_toolbox import dcc_toolbox_ui
    return dcc_toolbox_ui.main(*args, **kwargs)


def reload_module(full_refresh=False):
    import sys
    if sys.version_info[0] >= 3:
        from importlib import reload
    else:
        from imp import reload

    from .ui import ui_utils
    from . import dcc_toolbox_utils
    from . import dcc_toolbox_examples
    from . import dcc_toolbox_ui

    # custom wonky reload things here
    for window_index, toolbox_window in ui_utils.wh.windows.items():
        to_remove = False
        try:
            if not toolbox_window.isVisible():
                toolbox_window.deleteLater()
                to_remove = True
        except Exception as e:
            to_remove = True
        finally:
            if to_remove:
                ui_utils.wh.windows.pop(window_index)

    if full_refresh:  # under conditional argument because WindowHandler class is defined here
        reload(ui_utils)

    reload(dcc_toolbox_utils)
    reload(dcc_toolbox_examples)
    reload(dcc_toolbox_ui)
