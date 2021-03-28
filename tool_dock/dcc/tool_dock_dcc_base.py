class BaseToolDockInterface(object):
    def __init__(self):
        self.callbacks = []

    def remove_all_callbacks(self):
        for callback in self.callbacks:
            self.remove_callback(callback)

    " ---------------- Methods below needs DCC implementations ---------------------- "

    def open_script_in_editor(self, script_path):
        print("open_script_in_editor is not implemented for this DCC")

    def register_scene_change_callback(self, func):
        print("register_scene_change_callback is not implemented for this DCC")
        return []  # return a list of callbacks that can be removed later

    def remove_callback(self, callback):
        print("register_scene_change_callback is not implemented for this DCC")
