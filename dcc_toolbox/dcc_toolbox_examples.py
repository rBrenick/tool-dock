from dcc_toolbox import dcc_toolbox_utils as dtu


#####################################################
# Example tools

class AutoSkin(dtu.ToolBoxItemBase):
    TOOL_NAME = "AutoSkin"

    def run(self, argument_1=True, arg_2=3.0):
        print(argument_1, arg_2)


class UpdateSkeleton(dtu.ToolBoxItemBase):
    TOOL_NAME = "Update Skeleton"

    def run(self, argument_1=True, arg_2=3.0):
        print(argument_1, arg_2)


class UpdateSkeletonA(dtu.ToolBoxItemBase):
    TOOL_NAME = "Update Skeleton_A"


class UpdateSkeletonB(dtu.ToolBoxItemBase):
    TOOL_NAME = "Update Skeleton_B"


class UpdateSkeletonC(dtu.ToolBoxItemBase):
    TOOL_NAME = "Update Skeleton_C"


class UpdateSkeletonD(dtu.ToolBoxItemBase):
    TOOL_NAME = "Update Skeleton_D"


class UpdateSkeletonE(dtu.ToolBoxItemBase):
    TOOL_NAME = "Update Skeleton_E"


class UpdateSkeletonF(dtu.ToolBoxItemBase):
    TOOL_NAME = "Update"


class UpdateSkeletonG(dtu.ToolBoxItemBase):
    TOOL_NAME = "Update Skeleton_G"


class UpdateSkeletonH(dtu.ToolBoxItemBase):
    TOOL_NAME = "Update Skeleton_H"


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


class MoreToggleLodsButtons(dtu.ToolBoxItemBase):
    TOOL_NAME = "MoreToggleLods"

    def get_tool_actions(self):
        return {
            "Hide LODs": run_hide,
            "Show LODs": run_show
        }


def run_hide():
    print("hiding")


def run_show():
    print("showing")
