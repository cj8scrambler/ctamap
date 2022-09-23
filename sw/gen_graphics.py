import math
import svgwrite

REDCOLOR="#c60c30"
BLUECOLOR="#00a1de"
BROWNCOLOR="#62361b"
GREENCOLOR="#009b3a"
ORANGECOLOR="#f9461c"
PINKCOLOR="#e27ea6"
PURPLECOLOR="#522398"
YELLOWCOLOR="#f9e300"

# Image dimensions
WIDTH  = 1000
HEIGHT = 2000

# Addressing ranges
MAX_W_ADDR = 8000
MAX_E_ADDR = 400
MAX_N_ADDR = 10800
MAX_S_ADDR = 10000

LINE_THICK=20
STATION_THICK=2
ARCH_R=200

# Scaling needed to fit all addresses into image
SCALE = min(WIDTH / (MAX_W_ADDR + MAX_E_ADDR), HEIGHT / (MAX_N_ADDR + MAX_S_ADDR))

# Two different coordinate systems are used here:
#  Street Addresses: Cartesian coordinates with N/E addresses posistive, S/W addresses negative
#  SVG coordinates: (0,0) is top left of image and offsets are only positive to the right and down.
# Lines are described using street addresses, but all angles are calculated in SVG coordinates.
# 0 degrees is to the right.  Positive angles sweep clockwise.

class TrainLine:
    """ Class for drawing CTA line maps."""
    def __init__(self, drawing, start_address, color='#b0b0b0', thick=LINE_THICK):
        """ point is tuple with initial location in city address coordinates"""
        self._loc = start_address
        self._angle = None
#        print("angle initialized to: {}".format(self._angle))
        self._dwg = drawing
        self._line = drawing.add(drawing.g(stroke=color, stroke_width=thick, fill='none', fill_opacity=0 ))
        self._stations = drawing.add(drawing.g(stroke='black', stroke_width=STATION_THICK, fill='none', fill_opacity=0 ))
        self._center = [MAX_W_ADDR*SCALE, MAX_S_ADDR*SCALE]

    def AbsCoord(self, addr):
        """ Takes a Chicago street address (N/E: positive, S/W: negative) and maps it into absolute view coordiantes """
        x = self._center[0] + addr[0] * SCALE
        y = self._center[1] + addr[1] * -SCALE
#        print("addr: {} -> coord: {}".format(addr, [x,y]))
        return ([x,y])

    def RelDistance(self, blocks):
        """ Takes a Chicago stree address range and maps it into a relative distance in the view coordiantes """
        x = blocks[0] * SCALE
        y = -blocks[1] * SCALE
#        print("blocks: {} -> distance {}".format(blocks, [x,y]))
        return ([x,y])

    def Scale(self, value):
        """ Takes a value and scales it the same as address -> coordinates """
        return (value*SCALE)

    def Address(self, coord):
        """ Takes absolute view coordinates and maps them to a Chicago street address """
        x = (coord[0] - self._center[0]) / SCALE
        y = (coord[1] - self._center[1]) / -SCALE
        print("coord: {} -> address: {}".format(coord, [x,y]))
        return ([x,y])

    def Blocks(self, distance):
        """ Takes a relative view distance and maps it to a Chicago street address range """
        x = distance[0] / SCALE
        y = -distance[1] / SCALE
#        print("distance: {} -> blocks: {}".format(distance, [x,y]))
        return ([x,y])

    def DrawToAddress(self, address):
        """ Adds a line that moves from current location to address"""
        begin = self.AbsCoord(self._loc)
        end = self.AbsCoord(address)
        args = {'x0':begin[0],
            'y0':begin[1],
            'x1':end[0],
            'y1':end[1]}
        self._line.add(self._dwg.path(d="M %(x0)f,%(y0)f L %(x1)f,%(y1)f"%args))
        self._angle = math.degrees(math.atan2(end[1]-begin[1],end[0]-begin[0]))
        #print("atan({},{}) angle: {}".format(end[1]-begin[1],end[0]-begin[0],self._angle))
#        print("DrawToAddress angle updated to: {}".format(self._angle))
        self._loc = address
        print("M %(x0)f,%(y0)f L %(x1)f,%(y1)f"%args)

    def DrawBlocks(self, blocks):
        """ Adds a line that moves from current location to a relative distance in blocks"""
        dest = [self._loc[0] + blocks[0], self._loc[1] + blocks[1]]
        begin = self.AbsCoord(self._loc)
        end = self.AbsCoord(dest)
        args = {'x0':begin[0],
            'y0':begin[1],
            'x1':end[0],
            'y1':end[1]}
        self._angle = math.degrees(math.atan2(end[1]-begin[1],end[0]-begin[0]))
        #print("atan({},{}) angle: {}".format(blocks[1], blocks[0],self._angle))
#        print("DrawBlocks angle updated to: {}".format(self._angle))
        print("M %(x0)f,%(y0)f l %(x1)f,%(y1)f"%args)
        self._line.add(self._dwg.path(d="M %(x0)f,%(y0)f L %(x1)f,%(y1)f"%args))
        self._loc = dest


    def polarToCartesian(self, point, radius, angleInDegrees):
        angleR = math.radians(angleInDegrees)
        return ( [point[0] + (radius * math.cos(angleR)),
                  point[1] + (radius * math.sin(angleR))]);

    def DrawTurn(self, degrees, radius=ARCH_R):
        """ Draws a turn of degrees from the current path.  
            negative degrees: counter-clockwise
            positive degrees: clockwise  """
        vector_radius = self.Scale(radius)
        begin = self.AbsCoord(self._loc)
        # Center is 90 (same sign as degrees) from current angle
        if (degrees > 0):
            center_angle = self._angle + 90
            sweep = 1
        else:
            center_angle = self._angle - 90
            sweep = 0
        center = self.polarToCartesian(begin, vector_radius, center_angle);
        # End angle is the opposite of center angle plus the turn angle
        end_angle = center_angle + 180 + degrees
        end = self.polarToCartesian(center, vector_radius, end_angle);
        args = {'x0':begin[0],
            'y0':begin[1],
            'radius':vector_radius,
            'ellipseRotation':0, #has no effect for circles
            'endx': end[0],
            'endy': end[1],
            'lgarc': 0,
            'sweep': sweep}
        print("M %(x0)f,%(y0)f A %(radius)f,%(radius)f %(ellipseRotation)f %(lgarc)d,%(sweep)d %(endx)f,%(endy)f"%args)
        self._line.add(self._dwg.path(d="M %(x0)f,%(y0)f A %(radius)f,%(radius)f %(ellipseRotation)f %(lgarc)d,%(sweep)d %(endx)f,%(endy)f"%args))
        self._loc = self.Address(end)
        self._angle = self._angle + degrees
#        print("DrawTurn angle updated to: {}".format(self._angle))
#        print("center_angle: {}".format(center_angle))
#        print("end_angle: {}".format(end_angle))
#        self._stations.add(self._dwg.circle(begin, r=1))
#        self._stations.add(self._dwg.circle(center, r=2))
#        self._stations.add(self._dwg.circle(end, r=3))

class GreenLine:
    """ Class for drawing Green line """
    def __init__(self, drawing, color=GREENCOLOR):
        _line = TrainLine(drawing, [-7200,400], color=color)
        # Harlem to Cicero
        loc = addLine(dwg, greenline, p0=addrToCoord([-7200,400]), p1=(addrToCoord([-4800,400])))
        # Cicero to California
        loc = addRelLine(dwg, greenline, loc, distance=blocksToRel([4800-2800,-100]))
        # California to Ashland
        loc = addRelLine(dwg, greenline, loc, distance=blocksToRel([2800-1600,50]))
        # Ashland to Loop (loop is exagerated)
        loc = addRelLine(dwg, greenline, loc, distance=blocksToRel([1600,00]))
        # Loop Curve
        loc = addRelArc(dwg, greenline, p0=loc, distance=[radius,radius], radius=radius, direction=[0,1])
        # Loop to Indiana
        loc = addRelLine(dwg, greenline, loc, distance=blocksToRel([0,-3900]))
        # Indiana dogleg
        loc = addRelArc(dwg, greenline, p0=loc, distance=[radius,radius], radius=radius, direction=[0,0])
        loc = addRelArc(dwg, greenline, p0=loc, distance=[radius,radius], radius=radius, direction=[0,1])
        # dogleg to split
        loc = addRelLine(dwg, greenline, loc, distance=blocksToRel([0,3900-5900]))
        # Split to 63rd (Cottage Gove leg)
        split = loc
        loc = addRelLine(dwg, greenline, loc, distance=blocksToRel([0,5900-6300]))
        loc63rd = loc
        loc = addRelArc(dwg, greenline, p0=loc, distance=[radius,radius], radius=radius, direction=[0,0])
        # 63rd to Cottage Grove
        loc = addRelLine(dwg, greenline, loc, distance=blocksToRel([800,0]))
        # Split to wells (Ashland/63rd Leg)
        loc = addRelArc(dwg, greenline, p0=split, distance=[-radius,radius], radius=radius, direction=[0,1])
        loc = addRelLine(dwg, greenline, loc, distance=blocksToRel([-800,0]))
        loc = addRelArc(dwg, greenline, p0=loc, distance=[-radius,radius], radius=radius, direction=[0,0])
        loc = addLine(dwg, greenline, loc, distance=blocksToRel([0,loc63rd[1]]))
        loc = addRelArc(dwg, greenline, p0=loc, distance=[-radius,radius], radius=radius, direction=[0,1])

class PinkLine:
    """ Class for drawing Pink line """
    def __init__(self, drawing, begin, color=PINKCOLOR):
        print("#### Loop Pink Line ####")
        _line = TrainLine(drawing, begin, color)
        _line.DrawBlocks([-2000,0])
        _line.DrawTurn(-90)
        _line.DrawBlocks([0,-2400])
        _line.DrawTurn(90)
        _line.DrawBlocks([-3700,0])

class Loop:
    """ Class for drawing the Loop lines """
    def __init__(self, drawing, drawGreen=True, drawBlue=True, drawBrown=True,
                 drawRed=True, drawOrange=True, drawPink=True, drawPurple=True):
        # Entry points in the loop for each line
        self._pink = [-200, 200]
        self._green_west = [-200, 400]
        self._green_south = None
        self._orange = [2500, -3200]
        self._purple = [400, 1400]
#        if drawBlue:
#            print("#### Blue Line ####")
#            _blue = TrainLine(drawing, [-200,0], color=BLUECOLOR)
#            _blue.DrawBlocks([1800,0])
#            _blue.DrawTurn(90)
#            _blue.DrawBlocks([0,-3000])
#            _blue.DrawTurn(90)
        if drawPink:
            print("#### Loop Pink Line ####")
            pinkline = TrainLine(drawing, self._pink, color=PINKCOLOR)
            pinkline.DrawBlocks([2500,0])
            pinkline.DrawTurn(90)
            pinkline.DrawBlocks([0,-2500])
            pinkline.DrawTurn(90)
            pinkline.DrawBlocks([-1500,0])
            pinkline.DrawTurn(90)
            pinkline.DrawBlocks([0,2500])
            pinkline.DrawTurn(-90)
        if drawGreen:
            print("#### Loop Green Line ####")
            greenline = TrainLine(drawing, self._green_west, color=GREENCOLOR)
            greenline.DrawBlocks([2700,0])
            greenline.DrawTurn(90)
            greenline.DrawBlocks([0,-3800])
        if drawOrange:
            print("#### Loop Orange Line ####")
            orangeline = TrainLine(drawing, self._orange, color=ORANGECOLOR)
            orangeline.DrawBlocks([0,400])
            orangeline.DrawTurn(-61)
            orangeline.DrawTurn(61)
            orangeline.DrawBlocks([0,2248])
            orangeline.DrawTurn(-90)
            orangeline.DrawBlocks([-1095,0])
            orangeline.DrawTurn(-90)
            orangeline.DrawBlocks([0,-2090])
            orangeline.DrawTurn(-90)
            orangeline.DrawBlocks([1300,0])
        if drawPurple:
            print("#### Loop Purple Line ####")
            purpleline = TrainLine(drawing, self._purple, color=PURPLECOLOR)
            purpleline.DrawBlocks([0,-600])
            purpleline.DrawTurn(-90)
            purpleline.DrawBlocks([2100,0])
            purpleline.DrawTurn(90)
            purpleline.DrawBlocks([0,-3100])
            purpleline.DrawTurn(90)
            purpleline.DrawBlocks([-2100,0])
            purpleline.DrawTurn(90)
            purpleline.DrawBlocks([0,3500])
#        if drawBrown:
#            print("#### Loop Brown Line ####")
#            _brown = TrainLine(drawing, [400,900], color=BROWNCOLOR)
#            _brown.DrawBlocks([0,-300])
#            _brown.DrawTurn(-90)
#            _brown.DrawBlocks([1905,0])
#            _brown.DrawTurn(90)
#            _brown.DrawBlocks([0,-2900])
#            _brown.DrawTurn(90)
#            _brown.DrawBlocks([-1900,0])
#            _brown.DrawTurn(90)
#            _brown.DrawBlocks([0,3300])
    def GetPink(self):
        return self._pink;
    def GetGreenWest(self):
        return self._green_west;
    def GetGreenSouth(self):
        return self._green_south;
    def GetOrange(self):
        return self._orange;

dwg = svgwrite.Drawing(filename='graphic.svg', profile='tiny')
dwg.viewbox(0,0,WIDTH,HEIGHT)

loop = Loop(dwg)
pink = PinkLine(dwg, loop.GetPink())

dwg.save()

