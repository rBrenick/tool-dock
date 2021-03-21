from collections import OrderedDict

from . import parameter_widgets
from .ui_utils import QtWidgets, QtCore, QtGui, get_app_window, delete_window


class ParameterGrid(QtWidgets.QTreeView):
    def __init__(self, *args, **kwargs):
        super(ParameterGrid, self).__init__(*args, **kwargs)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._model = QtGui.QStandardItemModel()
        self._model.setHorizontalHeaderLabels(['Param', 'Value'])
        self.setModel(self._model)
        self.setUniformRowHeights(True)

        self.parameters = []

        # display options
        self.setIndentation(0)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.header().setMinimumWidth(0)

    def add_param(self, param):
        """

        :param param:
        :type param: BaseParam
        :return:
        """
        param_key = QtGui.QStandardItem(param.label_text)
        param_val = QtGui.QStandardItem()
        self._model.appendRow([param_key, param_val])

        # build UI from param and add it to model
        widget_child = param.build_type_widget()
        qindex_child = param_val.index()
        self.setIndexWidget(qindex_child, widget_child)

        self.parameters.append(param)

    def from_data(self, data):
        type_param_map = {
            "float": FloatParam,
            "str": StringParam,
            "unicode": StringParam,
            "bool": BoolParam,
        }

        if not isinstance(data, (dict, OrderedDict)):
            print("data is not of type dict: {}".format(type(data)))
            return

        for key, val in data.items():
            type_as_str = type(val).__name__
            param_cls = type_param_map.get(type_as_str)
            if not param_cls:
                print("param_cls not found: {}".format(type_as_str))
                continue

            # generate instance
            param_cls(self, key, default=val)

    def as_data(self):
        out_data = OrderedDict()
        for param in self.parameters:  # type: BaseParam
            out_data[param.label_text] = param.get_value()
        return out_data

    def get_header_sizes(self):
        header_sizes = []
        for col in range(self._model.columnCount()):
            header_sizes.append(self.header().sectionSize(col))
        return header_sizes

    def set_header_sizes(self, sizes):
        for col in range(self._model.columnCount()):
            self.header().resizeSection(col, sizes[col])


class BaseParam(object):
    def __init__(self, param_grid, label, default=None, build_ui=True, *args, **kwargs):
        self.param_grid = param_grid  # type: ParameterGrid
        self.label_text = label

        if build_ui:
            self.param_grid.add_param(self)

        if default:
            self.set_value(default)

    def build_type_widget(self):
        raise NotImplementedError("build_type_widgets not implemented for: {}".format(self.__class__))

    def get_value(self):
        raise NotImplementedError("get_value not implemented for: {}".format(self.__class__))

    def set_value(self, val):
        raise NotImplementedError("set_value not implemented for: {}".format(self.__class__))


class FloatParam(BaseParam):
    def __init__(self, *args, **kwargs):
        self.minimum = kwargs.get("min")
        self.maximum = kwargs.get("max")
        self.default = kwargs.get("default", 0.0)
        super(FloatParam, self).__init__(*args, **kwargs)

    def build_type_widget(self):
        self.float_widget = parameter_widgets.FloatDisplay(min=self.minimum,
                                                           max=self.maximum,
                                                           default=self.default)
        self.float_widget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        return self.float_widget

    def get_value(self):
        return self.float_widget.value()

    def set_value(self, val):
        self.float_widget.set_value(val)


class StringParam(BaseParam):
    def build_type_widget(self):
        self.line_edit = QtWidgets.QLineEdit()
        self.line_edit.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        return self.line_edit

    def get_value(self):
        return self.line_edit.text()

    def set_value(self, val):
        self.line_edit.setText(val)


class BoolParam(BaseParam):
    def build_type_widget(self):
        self.chk_box = QtWidgets.QCheckBox()
        self.chk_box.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        return self.chk_box

    def get_value(self):
        return self.chk_box.isChecked()

    def set_value(self, val):
        self.chk_box.setChecked(bool(val))


class ChoiceParam(BaseParam):
    def __init__(self, *args, **kwargs):
        self.options = kwargs.get("choices", [])
        super(ChoiceParam, self).__init__(*args, **kwargs)

    def build_type_widget(self):
        self.combo_box = QtWidgets.QComboBox()
        self.combo_box.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.combo_box.addItems(self.options)
        return self.combo_box

    def set_value(self, val):
        self.combo_box.setCurrentText(val)

    def get_value(self):
        return self.combo_box.currentText()


class TestParameterGrid(QtWidgets.QDialog):

    def __init__(self):
        delete_window(self)
        super(TestParameterGrid, self).__init__(parent=get_app_window())

        self.param_grid = ParameterGrid()

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.param_grid)

        # parameters can be filled manually like this
        FloatParam(self.param_grid, "manual_float_0", min=-10, max=10)
        FloatParam(self.param_grid, "manual_float_1", min=0, max=10)

        # or via dictionary data like this
        test_data = OrderedDict()
        test_data["strkey"] = "testing"
        test_data["floatie"] = 23.0
        test_data["boolie"] = True
        self.param_grid.from_data(test_data)

        self.setLayout(main_layout)
        self.setWindowTitle('Parameter Grid Testing')
        self.resize(QtCore.QSize(600, 400))
        self.show()


def main():
    return TestParameterGrid()


"""

import dcc_toolbox.ui.parameter_grid
reload(dcc_toolbox.ui.parameter_grid)
win = dcc_toolbox.ui.parameter_grid.main()

"""

if __name__ == '__main__':
    main()
