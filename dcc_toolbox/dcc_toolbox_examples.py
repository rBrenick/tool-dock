from dcc_toolbox import dcc_toolbox_utils as dtu
from dcc_toolbox.ui import parameter_grid as pg
from .ui.ui_utils import QtWidgets


#####################################################
# Example tools

class BasicAction(dtu.ToolBoxItemBase):
    TOOL_NAME = "Basic Action"

    def run(self):
        print("triggered BasicAction")


class BasicParamExample(dtu.ToolBoxItemBase):
    TOOL_NAME = "Basic Params"

    # function arguments can be extrapolated and automatically added as parameters
    def run(self, arg_1=True, arg_2=3.0):
        print(arg_1, arg_2)


class ComplexParamExample(dtu.ToolBoxItemBase):
    TOOL_NAME = "Complex Params"

    def __init__(self, *args, **kwargs):
        super(ComplexParamExample, self).__init__(*args, **kwargs)

        # parameters can also be defined like this
        # ui will be auto generated and added to the parameter grid
        self.float_param = pg.FloatParam(self.param_grid, "Float", min=0, max=1)
        self.str_param = pg.StringParam(self.param_grid, "Example")
        self.choice_param = pg.ChoiceParam(self.param_grid, "Color", choices=["Red", "Green", "Blue"], default="Blue")
        self.bool_param = pg.BoolParam(self.param_grid, "Active", default=True)

    def run(self):
        # example of getting param values
        print(self.float_param.get_value())
        print(self.str_param.get_value())
        print(self.choice_param.get_value())
        print(self.bool_param.get_value())


class MultiButtonExample(dtu.ToolBoxItemBase):
    TOOL_NAME = "Multi Buttons"

    # multiple run buttons can be added like this
    def get_tool_actions(self):
        return {
            "A": run_hide,
            "B": run_show
        }


class OverrideWidgetExample(dtu.ToolBoxItemBase):
    TOOL_NAME = "Custom Widget"

    # if you want to be really fancy, you can override the widget creation like this
    def build_ui_widget(self):
        lw = QtWidgets.QListWidget()
        lw.addItems(["Item1", "Item2", "Item3"])
        return lw


#####################################################################################
# Real use-cases

class VtxColorsButtons(dtu.ToolBoxItemBase):
    TOOL_NAME = "ToggleVtxColors"

    def get_tool_actions(self):
        return {
            "Hide": run_hide,
            "Show": run_show
        }


class ToggleLodsButtons(dtu.ToolBoxItemBase):
    TOOL_NAME = "ToggleLods"

    def get_tool_actions(self):
        return {
            "Hide LODs": run_hide,
            "Show LODs": run_show
        }


def run_hide():
    print("hiding")


def run_show():
    print("showing")
