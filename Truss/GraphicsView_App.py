#region imports
from GraphicsView_GUI import Ui_Form
import PyQt5.QtGui as qtg
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw
import math
import sys
import numpy as np
import scipy as sp
from scipy import optimize
#endregion

#region class definitions
class RigidLink(qtw.QGraphicsItem):
    def __init__(self, stX, stY, enX, enY, radius=10, parent=None, pen=None, brush=None, name='RigidLink'):
        """
        This is a custom class for drawing a rigid link.
        """
        super().__init__(parent)
        # step 1
        self.pen = pen
        self.brush = brush
        self.name = name
        self.startX = stX
        self.startY = stY
        self.endX = enX
        self.endY = enY
        self.radius = radius
        # step 2
        self.angle = self.linkAngle()
        # step 3
        self.rect = qtc.QRectF(-self.radius, -self.radius, self.length + self.radius, self.radius)
        # step 4: setup transform
        self.transform = qtg.QTransform()
        self.transform.reset()

    def boundingRect(self):
        return self.transform.mapRect(self.rect)

    def deltaY(self):
        self.DY = self.endY - self.startY
        return self.DY

    def deltaX(self):
        self.DX = self.endX - self.startX
        return self.DX

    def linkLength(self):
        self.length = math.sqrt(math.pow(self.deltaX(), 2) + math.pow(self.deltaY(), 2))
        return self.length

    def linkAngle(self):
        self.linkLength()
        if self.length == 0.0:
            self.angle = 0
        else:
            self.angle = math.acos(self.DX / self.length)
            self.angle *= -1 if (self.DY > 0) else 1
        return self.angle

    def paint(self, painter, option, widget=None):
        # Create the painter path for drawing the link.
        path = qtg.QPainterPath()
        len_val = self.linkLength()
        angLink = self.linkAngle() * 180 / math.pi
        rectSt = qtc.QRectF(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)
        rectEn = qtc.QRectF(self.length - self.radius, -self.radius, 2 * self.radius, 2 * self.radius)
        centerLinePen = qtg.QPen()
        centerLinePen.setStyle(qtc.Qt.DashDotLine)
        r, g, b, a = self.pen.color().getRgb()
        centerLinePen.setColor(qtg.QColor(r, g, b, 128))
        centerLinePen.setWidth(1)
        p1 = qtc.QPointF(0, 0)
        p2 = qtc.QPointF(len_val, 0)
        painter.setPen(centerLinePen)
        painter.drawLine(p1, p2)
        path.arcMoveTo(rectSt, 90)
        path.arcTo(rectSt, 90, 180)
        path.lineTo(self.length, self.radius)
        path.arcMoveTo(rectEn, 270)
        path.arcTo(rectEn, 270, 180)
        path.lineTo(0, -self.radius)
        if self.pen is not None:
            painter.setPen(self.pen)
        if self.brush is not None:
            painter.setBrush(self.brush)
        painter.drawPath(path)
        pivotStart = qtc.QRectF(-self.radius / 6, -self.radius / 6, self.radius / 3, self.radius / 3)
        pivotEnd = qtc.QRectF(self.length - self.radius / 6, -self.radius / 6, self.radius / 3, self.radius / 3)
        painter.drawEllipse(pivotStart)
        painter.drawEllipse(pivotEnd)
        self.rect = qtc.QRectF(-self.radius, -self.radius, self.length + 2 * self.radius, 2 * self.radius)
        self.transform.reset()
        self.transform.translate(self.startX, self.startY)
        self.transform.rotate(-angLink)
        self.setTransform(self.transform)
        self.transform.reset()
        stTT = self.name + "\nstart: ({:0.3f}, {:0.3f})\nend: ({:0.3f}, {:0.3f})\nlength: {:0.3f}\nangle: {:0.3f}".format(
            self.startX, self.startY, self.endX, self.endY, self.length, self.angle * 180 / math.pi)
        self.setToolTip(stTT)

class RigidPivotPoint(qtw.QGraphicsItem):
    def __init__(self, ptX, ptY, pivotHeight, pivotWidth, parent=None, pen=None, brush=None, rotation=0, name='RigidPivotPoint'):
        super().__init__(parent)
        self.x = ptX
        self.y = ptY
        self.pen = pen
        self.brush = brush
        self.height = pivotHeight
        self.width = pivotWidth
        self.radius = min(self.height, self.width) / 4
        self.rect = qtc.QRectF(self.x - self.width / 2, self.y - self.radius, self.width, self.height + self.radius)
        self.rotationAngle = rotation
        self.name = name
        self.transformation = qtg.QTransform()
        stTT = self.name + "\nx={:0.3f}, y={:0.3f}".format(self.x, self.y)
        self.setToolTip(stTT)

    def boundingRect(self):
        return self.transformation.mapRect(self.rect)

    def rotate(self, angle):
        self.rotationAngle = angle

    def paint(self, painter, option, widget=None):
        path = qtg.QPainterPath()
        radius = min(self.height, self.width) / 2
        H = math.sqrt(math.pow(self.width / 2, 2) + math.pow(self.height, 2))
        phi = math.asin(radius / H)
        theta = math.asin(self.height / H)
        ang = math.pi - phi - theta
        l = H * math.cos(phi)
        x1 = self.width / 2
        y1 = self.height
        path.moveTo(x1, y1)
        x2 = l * math.cos(ang)
        y2 = l * math.sin(ang)
        path.lineTo(x1 + x2, y1 - y2)
        pivotRect = qtc.QRectF(-radius, -radius, 2 * radius, 2 * radius)
        stAng = math.pi / 2 - phi - theta
        spanAng = math.pi - 2 * stAng
        path.arcTo(pivotRect, stAng * 180 / math.pi, spanAng * 180 / math.pi)
        x4 = -self.width / 2
        y4 = +self.height
        path.lineTo(x4, y4)
        if self.pen is not None:
            painter.setPen(self.pen)
        if self.brush is not None:
            painter.setBrush(self.brush)
        painter.drawPath(path)
        pivotPtRect = qtc.QRectF(-radius / 4, -radius / 4, radius / 2, radius / 2)
        painter.drawEllipse(pivotPtRect)
        x5 = -self.width
        x6 = +self.width
        painter.drawLine(x5, y4, x6, y4)
        penOutline = qtg.QPen(qtc.Qt.NoPen)
        hatchbrush = qtg.QBrush(qtc.Qt.BDiagPattern)
        painter.setPen(penOutline)
        painter.setBrush(hatchbrush)
        support = qtc.QRectF(x5, y4, self.width * 2, self.height)
        painter.drawRect(support)
        self.rect = qtc.QRectF(-self.width, -self.radius, self.width * 2, self.height * 2 + self.radius)
        self.transformation.reset()
        self.transformation.translate(self.x, self.y)
        self.transformation.rotate(self.rotationAngle)
        self.setTransform(self.transformation)
        self.transformation.reset()

# New class for the roller support.
class RigidRollerPoint(qtw.QGraphicsItem):
    def __init__(self, ptX, ptY, pivotHeight, pivotWidth, parent=None, pen=None, brush=None, rotation=0, name='RigidRollerPoint'):
        super().__init__(parent)
        self.x = ptX
        self.y = ptY
        self.pen = pen
        self.brush = brush
        self.height = pivotHeight
        self.width = pivotWidth
        self.name = name
        self.rotationAngle = rotation
        self.transformation = qtg.QTransform()
        stTT = self.name + "\nx={:0.3f}, y={:0.3f} (roller support)".format(self.x, self.y)
        self.setToolTip(stTT)
        # Define a simple bounding rectangle.
        self.rect = qtc.QRectF(self.x - self.width, self.y - self.height, 2 * self.width, 2 * self.height)

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget=None):
        # Draw a base line for the roller.
        base_line = qtc.QLineF(self.x - self.width, self.y, self.x + self.width, self.y)
        if self.pen is not None:
            painter.setPen(self.pen)
        painter.drawLine(base_line)
        # Draw a circle (roller wheel) above the base line.
        radius = min(self.width, self.height) / 2
        center = qtc.QPointF(self.x, self.y - radius)
        circleRect = qtc.QRectF(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius)
        if self.brush is not None:
            painter.setBrush(self.brush)
        painter.drawEllipse(circleRect)
#endregion

#region MainWindow class (unchanged)
class MainWindow(Ui_Form, qtw.QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setupGraphics()
        self.gv_Main.setMouseTracking(True)
        self.pushButton.setMouseTracking(True)
        self.setMouseTracking(True)
        self.buildScene()
        self.show()

    def setupGraphics(self):
        self.scene = qtw.QGraphicsScene()
        self.scene.setObjectName("MyScene")
        self.scene.setSceneRect(-200, -200, 400, 400)
        self.gv_Main.setScene(self.scene)
        self.setupPensAndBrushes()

    def setupPensAndBrushes(self):
        self.penThick = qtg.QPen(qtc.Qt.darkGreen)
        self.penThick.setWidth(5)
        self.penMed = qtg.QPen(qtc.Qt.darkBlue)
        self.penMed.setStyle(qtc.Qt.SolidLine)
        self.penMed.setWidth(2)
        self.penLink = qtg.QPen(qtg.QColor("orange"))
        self.penLink.setWidth(1)
        self.penGridLines = qtg.QPen()
        self.penGridLines.setWidth(1)
        self.penGridLines.setColor(qtg.QColor.fromHsv(197, 144, 228, 128))
        self.brushFill = qtg.QBrush(qtc.Qt.darkRed)
        self.brushHatch = qtg.QBrush()
        self.brushHatch.setStyle(qtc.Qt.DiagCrossPattern)
        self.brushGrid = qtg.QBrush(qtg.QColor.fromHsv(87, 98, 245, 128))
        self.brushLink = qtg.QBrush(qtg.QColor.fromHsv(35, 255, 255, 64))
        self.brushPivot = qtg.QBrush(qtg.QColor.fromHsv(0, 0, 128, 255))

    def buildScene(self):
        self.scene.clear()
        self.drawAGrid(10, 10, 400, 400, Pen=self.penGridLines, Brush=self.brushGrid)
        self.pivot0 = self.drawPivot(-100, 0, 10, 20)
        self.pivot0.setTransformOriginPoint(qtc.QPointF(self.pivot0.x, self.pivot0.y))
        self.pivot0.rotate(90)
        self.pivot1 = self.drawPivot(60, -30, 10, 20)
        self.pivot1.setTransformOriginPoint(qtc.QPointF(self.pivot1.x, self.pivot1.y))
        self.pivot1.rotate(-90)
        self.link0 = self.drawLinkage(self.pivot0.x, self.pivot0.y, self.pivot1.x, self.pivot1.y, radius=5, pen=self.penGridLines, brush=self.brushGrid)
        self.link1 = self.drawLinkage(-100, 0, -100, -60, 5)
        self.link2 = self.drawLinkage(-100, -60, 100, -150, 5)
        self.link3 = self.drawLinkage(60, -30, 100, -150, 5)

    # The rest of the methods remain as originally supplied.
#endregion

#region function calls
if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    mw = MainWindow()
    mw.setWindowTitle('GraphicsView')
    sys.exit(app.exec())
#endregion
