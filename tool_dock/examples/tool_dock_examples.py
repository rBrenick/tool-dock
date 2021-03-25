import os
import sys

from tool_dock import tool_dock_utils as tdu
from tool_dock.ui import parameter_grid as pg
from tool_dock.ui.ui_utils import QtWidgets


#####################################################
# Example tools

class BasicAction(tdu.ToolDockItemBase):
    TOOL_NAME = "Basic Action"
    BACKGROUND_COLOR = (80, 120, 80)

    def run(self):
        print("triggered BasicAction")


class BasicParamExample(tdu.ToolDockItemBase):
    TOOL_NAME = "Basic Params"

    # function arguments can be extrapolated and automatically added as parameters
    def run(self, arg_1=True, arg_2=3.0):
        print(arg_1, arg_2)


class ComplexParamExample(tdu.ToolDockItemBase):
    TOOL_NAME = "Complex Params"
    BACKGROUND_COLOR = (50, 100, 160)

    def __init__(self, *args, **kwargs):
        super(ComplexParamExample, self).__init__(*args, **kwargs)

        # parameters can also be defined like this
        # ui will be auto generated and added to the parameter grid
        self.float_param = pg.FloatParam(self.param_grid, "Float", min=0, max=1)
        self.str_param = pg.StringParam(self.param_grid, "Example")
        self.choice_param = pg.ChoiceParam(self.param_grid, "Color", choices=["Red", "Green", "Blue"], default="Blue")
        self.bool_param = pg.BoolParam(self.param_grid, "Active", default=True)

        # extra actions can be added to the right click menu like this
        self.context_menu_actions.extend([
            "-",
            {"Extra Right-Click Action": self.example_right_click_action}
        ])

    def run(self):
        # example of getting param values
        print(self.float_param.get_value())
        print(self.str_param.get_value())
        print(self.choice_param.get_value())
        print(self.bool_param.get_value())

    def example_right_click_action(self):
        print("Extra right click action: {}".format(self.TOOL_NAME))


class MultiButtonExample(tdu.ToolDockItemBase):
    TOOL_NAME = "Multi Buttons"
    BACKGROUND_COLOR = (160, 80, 20)

    # multiple run buttons can be added like this
    def get_tool_actions(self):
        return {
            "A": lambda: sys.stdout.write("A triggered\n"),
            "B": lambda: sys.stdout.write("B triggered\n")
        }


class OverrideWidgetExample(tdu.ToolDockItemBase):
    TOOL_NAME = "Custom Widget"

    # if you want to be really fancy, you can override the widget creation like this
    def build_ui_widget(self):
        lw = QtWidgets.QListWidget()
        lw.setMinimumHeight(0)
        lw.setMinimumWidth(0)
        lw.addItems(["Item1", "Item2", "Item3"])
        return lw


# tool classes can also be created from script paths like this
simple_script_path = os.path.join(os.path.dirname(__file__), "simple_script_example.py")
simple_script_cls = tdu.lk.dynamic_class_from_script(simple_script_path)

# you can then set properties of the class like this
simple_script_cls.BACKGROUND_COLOR = (100, 100, 150)
