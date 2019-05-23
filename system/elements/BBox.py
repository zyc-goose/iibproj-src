from .Coords import Coords
from uuid import uuid4
import re

class BBox:
    """The Bounding-Box object.
    attributes:
        coords - [Coords] coordinates of the bbox
        text - [str] text enclosed in the bbox
        page - [int] page num of the bbox
    """
    
    def __init__(self, coords, text, page, from_obj=False):
        self.text = text
        if from_obj:
            self.coords = Coords(**coords)
        else:
            self.coords = coords
        self.page = page
        self.id = str(uuid4())
        self._type_check()

    def area(self):
        """Return the area of the bbox."""
        return self.coords.area()

    def words(self):
        """Convert text to a list of BBoxWord objects and return the list."""
        text = self.text
        text = re.sub(r'[^\w\s]', ' ', text)
        text = text.lower()
        return list(map(BBoxWord, text.split()))
    
    def set_text(self, text):
        assert isinstance(text, str)
        self.text = text
    
    def to_group(self):
        """Return a BBoxGroup object which only contains the current BBox object (self)."""
        group = BBoxGroup()
        group.append(self)
        return group
    
    def to_obj(self):
        return dict(coords=self.coords.to_obj(), text=self.text, page=self.page)

    def __and__(self, other):
        """Return the intersection area of two BBox objects."""
        if self.page != other.page:
            return 0
        return self.coords & other.coords

    def _type_check(self):
        if not isinstance(self.coords, Coords):
            raise TypeError('coords should be a Coords object')
        if not isinstance(self.text, str):
            raise TypeError('text should be a str')
        if not isinstance(self.page, int):
            raise TypeError('page should be an int')
    
    def __str__(self):
        return '{{coords = {coords}, text = {text}}}'.format(coords=self.coords, text=self.text)
    
    def __repr__(self):
        return '<BBox> ' + self.__str__()


class BBoxGroup(list):
    """A Group of BBox objects (Atomic element for alignment)."""

    def __init__(self, group=(), from_obj=False):
        if from_obj:
            list.__init__(self, map(lambda x: BBox(**x, from_obj=True), group))
        else:
            list.__init__(self, group)
    
    def words(self):
        """Convert text to a list of BBoxWord objects and return the list."""
        res = []
        for elem in self:
            res.extend(elem.words())
        for i, elem in enumerate(res):
            elem.info.wid = i
        return res
    
    def area(self):
        return sum(x.area() for x in self)
    
    def page_range(self):
        if len(self) == 0:
            return (0, -1)
        return (self[0].page, self[-1].page)
    
    def common_page_range(self, other):
        r1 = self.page_range()
        r2 = other.page_range()
        p1 = max(r1[0], r2[0])
        p2 = min(r1[1], r2[1])
        return (p1, p2) if p1 <= p2 else None
    
    def to_obj(self):
        return list(map(lambda x: x.to_obj(), self))
    
    def __and__(self, other):
        if self.common_page_range(other) is None:
            return 0
        ret = 0
        for x in self:
            for y in other:
                ret += (x & y)
        return ret


class BBoxGroups(list):
    """A List of BBoxGroup objects."""
    
    def __init__(self, groups=(), from_obj=False):
        if from_obj:
            list.__init__(self, map(lambda x: BBoxGroup(x, from_obj=True), groups))
        else:
            list.__init__(self, map(lambda x: BBoxGroup(x, from_obj=False), groups))
    
    def words(self):
        """Convert text to a list of BBoxWord objects and return the list."""
        res = []
        for i, group in enumerate(self):
            group_words = group.words()
            glen = len(group_words)
            for word in group_words:
                word.info.gid = i
                word.info.glen = glen
            res.extend(group_words)
        N = len(res)
        for i, elem in enumerate(res):
            elem.info.relpos = i / N
        return res
    
    def area(self):
        return sum(x.area() for x in self)
    
    def page_range(self):
        if len(self) == 0:
            return (0, -1)
        return (self[0].page_range()[0], self[-1].page_range()[-1])
    
    def __and__(self, other):
        ret = 0
        for gx in self:
            for gy in other:
                rx, ry = gx.page_range(), gy.page_range()
                if ry[0] > rx[1]:
                    break
                ret += (gx & gy)
        return ret


class BBoxWordInfo:
    def __init__(self, gid=None, wid=None, glen=None, relpos=None):
        """gid: group id
           wid: word id
           glen: group len
           relpos: global word id / len(all words)
        """
        self.set(gid, wid, glen, relpos)
    
    def to_obj(self):
        return dict(gid=self.gid, wid=self.wid, glen=self.glen)
    
    def set(self, gid=None, wid=None, glen=None, relpos=None):
        self.gid, self.wid, self.glen, self.relpos = gid, wid, glen, relpos
    
    def __str__(self):
        return 'BBoxWordInfo(gid=%d, wid=%d, glen=%d)' % (self.gid, self.wid, self.glen)
    
    def __repr__(self):
        return self.__str__()


class BBoxWord:
    """A Word which also contains a BBoxGroup ID."""

    def __init__(self, word, info=None, from_obj=False):
        self.word = word
        if from_obj:
            self.info = BBoxWordInfo(**info)
        else:
            self.info = BBoxWordInfo()
        self._type_check()
    
    def to_obj(self):
        return dict(word=self.word, info=self.info.to_obj())
    
    def __eq__(self, other):
        return self.word == other.word
    
    def __str__(self):
        return 'BBoxWord(word=%s, info=%s)' % (self.word, self.info)
    
    def __repr__(self):
        return self.__str__()

    def _type_check(self):
        if not isinstance(self.word, str):
            raise TypeError('word should be a str')

class BBoxGUI:
    """BBox for GUI purposes (especially Canvas object)."""

    def __init__(self, bbox, color='blue'):
        if not isinstance(bbox, BBox):
            raise TypeError('bbox should be a BBox object')
        self.id = bbox.id
        self.canvasID = None
        self.coords = bbox.coords
        self.color = color
        assert isinstance(self.coords, Coords)


if __name__ == '__main__':
    coords = Coords(1, 2, 3, 4)
    text = 'lorem ipsum'
    bbox = BBox(coords, text, 1)
    bg = BBoxGroup()
    bg.append(bbox)
    print(bg[0])