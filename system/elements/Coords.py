class Coords:
    """Coordinates for a specific bounding-box.
    attributes:
        (x0, y0) - coordinates for the top-left corner
        (x1, y1) - coordinates for the bottom-right corner
    """
    
    def __init__(self, x0, y0, x1, y1):
        self.x0, self.y0 = x0, y0
        self.x1, self.y1 = x1, y1
        self._type_check()
        # swap coords if needed
        if self.x0 > self.x1:
            self.x0, self.x1 = self.x1, self.x0
        if self.y0 > self.y1:
            self.y0, self.y1 = self.y1, self.y0
    
    def area(self):
        """Return the area of the bbox."""
        return self._area(self.x0, self.y0, self.x1, self.y1)
    
    def contains_point(self, x, y):
        """Return true if (x, y) is inside the rectangle."""
        return self.x0 <= x <= self.x1 and self.y0 <= y <= self.y1
    
    def scale_XY(self, fx, fy):
        """Scale x-coords by fx, y-coords by fy, and return the new coords."""
        x0, y0 = round(self.x0 * fx), round(self.y0 * fy)
        x1, y1 = round(self.x1 * fx), round(self.y1 * fy)
        return Coords(x0, y0, x1, y1)
    
    def to_obj(self):
        return dict(x0=self.x0, y0=self.y0, x1=self.x1, y1=self.y1)
    
    def to_tuple(self):
        return (self.x0, self.y0, self.x1, self.y1)

    def __and__(self, other):
        """Return the intersection area of two Coords objects."""
        x0, y0 = max(self.x0, other.x0), max(self.y0, other.y0)
        x1, y1 = min(self.x1, other.x1), min(self.y1, other.y1)
        if x0 > x1 or y0 > y1:
            return 0
        return self._area(x0, y0, x1, y1)
        
    def _area(self, x0, y0, x1, y1):
        return abs(x1 - x0) * abs(y1 - y0)

    def _type_check(self):
        checklist = dict(x0=self.x0, y0=self.y0, x1=self.x1, y1=self.y1)
        for key in checklist.keys():
            if not isinstance(checklist[key], (int, float)):
                raise TypeError('%s should be a number' % key)
    
    def __str__(self):
        return '(x0 = %s, y0 = %s, x1 = %s, y1 = %s)' % (self.x0, self.y0, self.x1, self.y1)
    

if __name__ == '__main__':
    coords = Coords(4,3,2,1)
    print(coords)
    print(coords.area())
    coords2 = Coords(1,2,3,4)
    print(coords & coords2)
    coords3 = Coords(5,6,7,8)
    print(coords & coords3)