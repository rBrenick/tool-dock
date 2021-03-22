from .ui_utils import QtWidgets, QtCore, QtGui, get_app_window, delete_window


class FloatDisplay(QtWidgets.QWidget):
    value_set = QtCore.Signal(float)

    def __init__(self, min=None, max=None, default=0.0, absolute=False, precision=3, *args, **kwargs):
        super(FloatDisplay, self).__init__(*args, **kwargs)
        self.min_value = min
        self.max_value = max
        self._value = default
        self._display_value = ""
        self._display_precision = precision

        # absolute is only allowed when min and max is defined
        if min is not None and max is not None:
            self.absolute = absolute
        else:
            self.absolute = False

        # internal variables
        self._multiplier = 1.0
        self._move_delta = 0
        self._on_click_x_pos = 0
        self._on_click_value = 0
        self._on_click_global_pos = None

        # set some display things on init
        self.set_value(self._value)
        self.setCursor(QtCore.Qt.SplitHCursor)

    def value(self):
        return self._value

    def set_value(self, value):
        # clamp within range
        if self.min_value is not None:
            value = max(value, self.min_value)
        if self.max_value is not None:
            value = min(value, self.max_value)

        # set value for internal logic
        self._value = value
        self._display_value = self.get_formatted_display_value(value)

        # draw slider position
        self.repaint()

        # emit signal
        self.value_set.emit(value)

    def get_formatted_display_value(self, value):
        if value == 0:
            return "0"
        else:
            precision_form = "{{:.{0}f}}".format(self._display_precision)
            return precision_form.format(value)

    # --------------------------------------------- LOGIC EVENTS ----------------------------------------
    def mousePressEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            self._on_click_global_pos = event.globalPos()
            self._on_click_x_pos = event.x()
            self._on_click_value = self._value
            if self.absolute:
                self.ui_mouse_set_value(event)

    def mouseDoubleClickEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            val, ok = QtWidgets.QInputDialog.getDouble(self, "New Value", "Enter New Value", self._value,
                                                       decimals=self._display_precision)
            if ok:
                self.set_value(val)

    def keyPressEvent(self, event):
        self.set_multiplier()
        if event.key() & QtCore.Qt.LeftArrow:
            self.set_value(self._value - 1.0 * self._multiplier)
        elif event.key() & QtCore.Qt.RightArrow:
            self.set_value(self._value + 1.0 * self._multiplier)

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            self.setCursor(QtCore.Qt.BlankCursor)
            self.set_multiplier()
            self.ui_mouse_set_value(event)
            if not self.absolute:
                QtGui.QCursor.setPos(self._on_click_global_pos)

    def mouseReleaseEvent(self, event):
        self._move_delta = 0
        self.setCursor(QtCore.Qt.SplitHCursor)
        if event.buttons() == QtCore.Qt.LeftButton:
            QtGui.QCursor.setPos(self._on_click_global_pos)

    def ui_mouse_set_value(self, event):
        if self.absolute:
            # value as determined by point on slider
            val = self.ui_get_value_as_percent(event.x())
            val = val * self._multiplier
        else:
            # value as offset from the click position
            relative_value = self.ui_get_value_as_percent(event.x() - self._on_click_x_pos)
            relative_value = relative_value * self._multiplier
            self._move_delta += relative_value
            val = self._on_click_value + self._move_delta

            # convenience clamp so _move_delta doesn't go beyond range
            if self.min_value is not None and val < self.min_value:
                self._move_delta = self.min_value - self._on_click_value
            if self.max_value is not None and val > self.max_value:
                self._move_delta = self.max_value - self._on_click_value

        self.set_value(val)

    def ui_get_value_as_percent(self, value):
        percent = float(value) / self.size().width()
        if self.absolute:
            return percent * (self.max_value - self.min_value) + self.min_value
        else:
            range_mult = abs(self.max_value if self.max_value is not None else 1.0)
            return range_mult * percent

    def set_multiplier(self):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            self._multiplier = 10.0
        elif modifiers == QtCore.Qt.ControlModifier:
            self._multiplier = 0.1
        else:
            self._multiplier = 1.0

    # --------------------------------------------- DRAW EVENTS -----------------------------------------
    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)

        size = self.size()
        w = size.width()
        h = size.height()

        font = QtGui.QFont('Serif', 8, QtGui.QFont.Normal)
        qp.setFont(font)

        # resize text to scale with widget
        h_factor = float(h) / qp.fontMetrics().height()
        w_factor = float(w) / qp.fontMetrics().width(self._display_value)
        factor = min(h_factor, w_factor)  # the smaller value determines max text size
        font.setPointSizeF(font.pointSizeF() * factor)
        qp.setFont(font)

        if self.max_value is None or self.min_value is None:
            current_value_width = w
        else:
            # this took me way too long to figure out, even though it's just basic line equation
            m = float(w) / (self.max_value - self.min_value)
            current_value_width = int((m * self._value) - m * self.min_value)

        qp.setPen(QtGui.QColor(20, 20, 20))
        qp.setBrush(QtGui.QColor(100, 100, 100))
        qp.drawRect(0, 0, current_value_width, h)

        pen = QtGui.QPen(QtGui.QColor(20, 20, 20), 1, QtCore.Qt.SolidLine)
        qp.setPen(pen)
        qp.setBrush(QtCore.Qt.NoBrush)
        qp.drawRect(0, 0, w - 1, h - 1)

        # draw value text
        pen = QtGui.QPen(QtGui.QColor(200, 200, 200))
        qp.setPen(pen)
        qp.drawText(e.rect(), QtCore.Qt.AlignCenter, self._display_value)

        qp.end()


class TestParameters(QtWidgets.QMainWindow):

    def __init__(self):
        delete_window(self)
        super(TestParameters, self).__init__(parent=get_app_window())

        self.wid = FloatDisplay()

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.wid)
        main_layout.addWidget(FloatDisplay(min=0, max=1, absolute=True))
        main_layout.addWidget(FloatDisplay(min=5, max=20))
        main_layout.addWidget(FloatDisplay(min=-100, max=100, precision=0))
        main_layout.addWidget(FloatDisplay(min=-100, max=-50, default=-75))
        # main_layout.addWidget(QtWidgets.QPushButton("testing"))

        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.setWindowTitle('Parameter Testing Window')
        self.resize(QtCore.QSize(600, 400))
        self.show()


def main():
    return TestParameters()


"""
import dcc_toolbox.ui.parameter_widgets
reload(dcc_toolbox.ui.parameter_widgets)
win = dcc_toolbox.ui.parameter_widgets.main()

"""

if __name__ == '__main__':
    main()
