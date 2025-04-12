#region imports
import math
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from GraphicsView_App import RigidLink, RigidPivotPoint, RigidRollerPoint
#endregion

#region class definitions
class Position():
    def __init__(self, pos=None, x=None, y=None, z=None):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        if pos is not None:
            self.x, self.y, self.z = pos
        self.x = x if x is not None else self.x
        self.y = y if y is not None else self.y
        self.z = z if z is not None else self.z

    def __add__(self, other):
        return Position((self.x + other.x, self.y + other.y, self.z + other.z))

    def __sub__(self, other):
        return Position((self.x - other.x, self.y - other.y, self.z - other.z))

    def __mul__(self, other):
        if type(other) in (float, int):
            return Position((self.x * other, self.y * other, self.z * other))
        if isinstance(other, Position):
            return Position((self.x * other.x, self.y * other.y, self.z * other.z))

    def __truediv__(self, other):
        if type(other) in (float, int):
            return Position((self.x / other, self.y / other, self.z / other))

    def mag(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def getAngleRad(self):
        l = self.mag()
        if l <= 0.0:
            return 0
        if self.y >= 0.0:
            return math.acos(self.x / l)
        return 2.0 * math.pi - math.acos(self.x / l)

    def getAngleDeg(self):
        return (180.0 / math.pi) * self.getAngleRad()

class Rectangle():
    def __init__(self, top=None, left=None, bottom=None, right=None):
        self.top = 0 if top is None else top
        self.left = 0 if left is None else left
        self.bottom = 0 if bottom is None else bottom
        self.right = 0 if right is None else right

    def height(self):
        return self.top - self.bottom

    def width(self):
        return self.right - self.left

    def centerY(self):
        return self.bottom + self.height() / 2.0

    def centerX(self):
        return self.left + self.width() / 2.0

class Material():
    def __init__(self, uts=None, ys=None, modulus=None, staticFactor=None):
        self.uts = uts
        self.ys = ys
        self.E = modulus
        self.staticFactor = staticFactor

class Node():
    def __init__(self, name=None, position=None):
        self.name = name
        self.position = position if position is not None else Position()
        self.graphic = None  # Assigned later (either RigidPivotPoint or RigidRollerPoint)

    def __eq__(self, other):
        return self.name == other.name and self.position == other.position

class Link():
    def __init__(self, name="", node1="1", node2="2",
                 length=None, angleRad=None,
                 width=1.0, thickness=0.1, material='steel'):
        """
        Extended link class with cross-sectional width, thickness and material.
        """
        self.name = name
        self.node1_Name = node1
        self.node2_Name = node2
        self.width = width
        self.thickness = thickness
        self.material = material
        self.length = length
        self.angleRad = angleRad
        self.graphic = RigidLink(0, 0, 1, 1)
        self.graphic.name = name

    def __eq__(self, other):
        return (self.node1_Name == other.node1_Name and
                self.node2_Name == other.node2_Name and
                self.length == other.length and
                self.angleRad == other.angleRad)

    def set(self, node1=None, node2=None, length=None, angleRad=None):
        self.node1_Name = node1
        self.node2_Name = node2
        self.length = length
        self.angleRad = angleRad

    @property
    def area(self):
        return self.width * self.thickness

    @property
    def density(self):
        if self.material.lower() == 'steel':
            return 0.284  # lb/in^3
        elif self.material.lower() == 'aluminum':
            return 0.098
        else:
            return 0.284

    @property
    def weight(self):
        if self.length is None:
            return 0.0
        return self.area * self.length * self.density

class TrussModel():
    def __init__(self):
        self.title = None
        self.links = []
        self.nodes = []
        self.material = Material()
        self.rct = Rectangle()

    def getNode(self, name):
        for n in self.nodes:
            if n.name.lower() == name.lower():
                return n
        return None

    def getCenterPt(self):
        # Calculate the bounding rectangle that encloses all nodes.
        if not self.nodes:
            return
        rct = Rectangle()
        first = self.nodes[0].position
        rct.left = first.x
        rct.right = first.x
        rct.top = first.y
        rct.bottom = first.y
        for n in self.nodes:
            if n.position.x < rct.left:
                rct.left = n.position.x
            if n.position.x > rct.right:
                rct.right = n.position.x
            if n.position.y > rct.top:
                rct.top = n.position.y
            if n.position.y < rct.bottom:
                rct.bottom = n.position.y
        self.rct = rct

class TrussView():
    def __init__(self):
        self.scene = qtw.QGraphicsScene()
        self.le_LongLinkName = qtw.QLineEdit()
        self.le_LongLinkNode1 = qtw.QLineEdit()
        self.le_LongLinkNode2 = qtw.QLineEdit()
        self.le_LongLinkLength = qtw.QLineEdit()
        self.te_Report = qtw.QTextEdit()
        self.gv = qtw.QGraphicsView()
        # Setup pens and brushes.
        self.penLink = qtg.QPen(qtg.QColor("orange"))
        self.penLink.setWidth(1)
        self.penNode = qtg.QPen(qtc.Qt.darkBlue)
        self.penNode.setStyle(qtc.Qt.SolidLine)
        self.penNode.setWidth(1)
        self.penLabel = qtg.QPen(qtc.Qt.darkMagenta)
        self.penLabel.setStyle(qtc.Qt.SolidLine)
        self.penLabel.setWidth(1)
        self.penGridLines = qtg.QPen()
        self.penGridLines.setWidth(1)
        self.penGridLines.setColor(qtg.QColor.fromHsv(197, 144, 228, 50))
        self.brushLink = qtg.QBrush(qtg.QColor.fromHsv(35, 255, 255, 64))
        self.brushPivot = qtg.QBrush(qtg.QColor.fromRgb(215, 215, 215, 128))
        self.brushFill = qtg.QBrush(qtc.Qt.darkRed)
        self.brushNode = qtg.QBrush(qtg.QColor.fromCmyk(0, 0, 255, 0, 100))
        self.brushGrid = qtg.QBrush(qtg.QColor.fromHsv(87, 98, 245, 128))

    def setDisplayWidgets(self, args):
        self.te_Report = args[0]
        self.le_LongLinkName = args[1]
        self.le_LongLinkNode1 = args[2]
        self.le_LongLinkNode2 = args[3]
        self.le_LongLinkLength = args[4]
        self.gv = args[5]
        self.gv.setScene(self.scene)

    def displayReport(self, truss=None):
        st = '\tTruss Design Report\n'
        st += 'Title:  {}\n'.format(truss.title)
        st += 'Static Factor of Safety:  {:0.2f}\n'.format(truss.material.staticFactor)
        st += 'Ultimate Strength:  {:0.2f}\n'.format(truss.material.uts)
        st += 'Yield Strength:  {:0.2f}\n'.format(truss.material.ys)
        st += 'Modulus of Elasticity:  {:0.2f}\n'.format(truss.material.E)
        st += '_____________Link Summary________________\n'
        st += 'Link\t(1)\t(2)\tLength\tAngle\n'
        longest = None
        for l in truss.links:
            if longest is None or (l.length is not None and l.length > longest.length):
                longest = l
            st += '{}\t{}\t{}\t{:0.2f}\t{:0.2f}\n'.format(l.name, l.node1_Name, l.node2_Name, l.length or 0.0, l.angleRad or 0.0)
        self.te_Report.setText(st)
        if longest is not None:
            self.le_LongLinkName.setText(longest.name)
            self.le_LongLinkLength.setText("{:0.2f}".format(longest.length or 0.0))
            self.le_LongLinkNode1.setText(longest.node1_Name)
            self.le_LongLinkNode2.setText(longest.node2_Name)

    def buildScene(self, truss=None):
        truss.getCenterPt()
        rct = truss.rct
        rct.left -= 50
        rct.right += 50
        rct.top += 50
        rct.bottom -= 50
        self.scene.clear()
        self.drawAGrid(10, 10, abs(rct.height()), abs(rct.width()), CenterX=0, CenterY=0)
        self.drawLinks(truss=truss)
        self.drawNodes(truss=truss)

    def drawAGrid(self, DeltaX=10, DeltaY=10, Height=320, Width=180, CenterX=120, CenterY=60):
        Pen = self.penGridLines
        Brush = self.brushGrid
        left = CenterX - Width / 2.0
        top = CenterY - Height / 2.0
        if Brush is not None:
            rect = qtw.QGraphicsRectItem(left, top, Width, Height)
            rect.setBrush(Brush)
            rect.setPen(Pen)
            self.scene.addItem(rect)
        x = left
        while x <= left + Width:
            lVert = qtw.QGraphicsLineItem(x, top, x, top + Height)
            lVert.setPen(Pen)
            self.scene.addItem(lVert)
            x += DeltaX
        y = top
        while y <= top + Height:
            lHor = qtw.QGraphicsLineItem(left, y, left + Width, y)
            lHor.setPen(Pen)
            self.scene.addItem(lHor)
            y += DeltaY

    def drawLinks(self, truss=None):
        rct = truss.rct
        offset = Position(x=rct.centerX(), y=rct.centerY())
        for l in truss.links:
            n1 = truss.getNode(l.node1_Name)
            n2 = truss.getNode(l.node2_Name)
            if n1 is None or n2 is None:
                continue
            # Create the graphic with proper offset and with a short radius.
            l.graphic = RigidLink(
                n1.position.x - offset.x,
                -(n1.position.y - offset.y),
                n2.position.x - offset.x,
                -(n2.position.y - offset.y),
                radius=3, pen=self.penLink, brush=self.brushLink, name="link: " + l.name
            )
            st = f"Link: {l.name}\nWidth: {l.width:.3f} in\nThickness: {l.thickness:.3f} in\nMaterial: {l.material}\nWeight: {l.weight:.3f} lb"
            l.graphic.setToolTip(st)
            self.scene.addItem(l.graphic)

    def drawNodes(self, truss=None, scene=None):
        rct = truss.rct
        offset = Position(x=rct.centerX(), y=rct.centerY())
        for n in truss.nodes:
            x = n.position.x - offset.x
            y = n.position.y - offset.y
            if n.name.lower() == 'left':
                reaction = getattr(n, "reaction", 0.0)
                n.graphic = RigidPivotPoint(x, -y, 10, 18, brush=self.brushPivot, name=n.name)
                n.graphic.setToolTip(f"Node: {n.name}\nVertical Reaction = {reaction:.2f} lb")
                self.scene.addItem(n.graphic)
            elif n.name.lower() == 'right':
                reaction = getattr(n, "reaction", 0.0)
                n.graphic = RigidRollerPoint(x, -y, 10, 18, brush=self.brushPivot, name=n.name)
                n.graphic.setToolTip(f"Node: {n.name} (roller support)\nVertical Reaction = {reaction:.2f} lb")
                self.scene.addItem(n.graphic)
            self.drawALabel(x=x - 5, y=y + 15, str=n.name, pen=self.penLabel)

    def drawALabel(self, x, y, str='', pen=None, brush=None, tip=None):
        lbl = qtw.QGraphicsTextItem(str)
        w = lbl.boundingRect().width()
        h = lbl.boundingRect().height()
        lbl.setX(x - w / 2.0)
        lbl.setY(-y - h / 2.0)
        if tip is not None:
            lbl.setToolTip(tip)
        if pen is not None:
            lbl.setDefaultTextColor(pen.color())
        self.scene.addItem(lbl)
#endregion

class TrussController():
    def __init__(self):
        self.truss = TrussModel()
        self.view = TrussView()

    def ImportFromFile(self, data):
        # Create a new truss model.
        self.truss = TrussModel()
        for L in data:
            L = L.strip()
            if L.startswith('#'):
                continue
            Cells = L.split(',')
            if len(Cells) <= 1:
                continue
            elif Cells[0].lower().find('material') >= 0:
                sut = float(Cells[1].strip())
                sy = float(Cells[2].strip())
                E = float(Cells[3].strip())
                self.truss.material = Material(uts=sut, ys=sy, modulus=E)
            elif Cells[0].lower().find('static') >= 0:
                sf = float(Cells[1].strip())
                self.truss.material.staticFactor = sf
            elif Cells[0].lower().find('node') >= 0:
                name = Cells[1].strip()
                x = float(Cells[2].strip())
                y = float(Cells[3].strip())
                self.truss.nodes.append(Node(name=name, position=Position(x=x, y=y)))
            elif Cells[0].lower().find('link') >= 0:
                name = Cells[1].strip()
                n1 = Cells[2].strip()
                n2 = Cells[3].strip()
                width = float(Cells[4].strip()) if len(Cells) > 4 else 1.0
                thickness = float(Cells[5].strip()) if len(Cells) > 5 else 0.1
                material = Cells[6].strip() if len(Cells) > 6 else 'steel'
                self.truss.links.append(Link(name=name, node1=n1, node2=n2,
                                             width=width, thickness=thickness, material=material))
        self.calcLinkVals()
        self.computeSupportReactions()
        self.displayReport()
        self.drawTruss()

    def calcLinkVals(self):
        for l in self.truss.links:
            n1 = self.truss.getNode(l.node1_Name)
            n2 = self.truss.getNode(l.node2_Name)
            if n1 is not None and n2 is not None:
                r = n2.position - n1.position
                l.length = r.mag()
                l.angleRad = r.getAngleRad()

    def computeSupportReactions(self):
        # Compute vertical reactions assuming a simply supported beam with supports at 'Left' and 'Right'
        node_left = self.truss.getNode("Left")
        node_right = self.truss.getNode("Right")
        if node_left is None or node_right is None:
            return
        x_left = node_left.position.x
        x_right = node_right.position.x
        L_total = x_right - x_left if x_right != x_left else 1.0
        total_weight = 0.0
        moment_sum = 0.0
        for l in self.truss.links:
            w = l.weight
            total_weight += w
            n1 = self.truss.getNode(l.node1_Name)
            n2 = self.truss.getNode(l.node2_Name)
            if n1 is not None and n2 is not None:
                x_mid = (n1.position.x + n2.position.x) / 2.0
                moment_sum += w * (x_mid - x_left)
        R_right = moment_sum / L_total
        R_left = total_weight - R_right
        # Store reaction values in the nodes
        node_left.reaction = R_left
        node_right.reaction = R_right

    def setDisplayWidgets(self, args):
        self.view.setDisplayWidgets(args)

    def displayReport(self):
        self.view.displayReport(truss=self.truss)

    def drawTruss(self):
        self.view.buildScene(truss=self.truss)

    # The following helper methods allow the App to work only with the controller.
    def installSceneEventFilter(self, filterObj):
        self.view.scene.installEventFilter(filterObj)

    def getScene(self):
        return self.view.scene

    def itemAtScenePos(self, pos, transform):
        return self.view.scene.itemAt(pos, transform)

    def itemsAtScenePos(self, pos):
        return self.view.scene.items(pos)
#endregion


