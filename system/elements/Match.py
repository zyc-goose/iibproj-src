from .BBox import BBoxGroup, BBoxGroups
from .TInterval import TIntervalGroup

class Match:
    """A Match from BBoxGroup to TIntervalGroup."""

    def __init__(self, bbox_group, tinterval_group, from_obj=False):
        if from_obj:
            self.bbox_group = BBoxGroup(bbox_group, from_obj=True)
            self.tinterval_group = TIntervalGroup(tinterval_group, from_obj=True)
        else:
            self.bbox_group = bbox_group
            self.tinterval_group = tinterval_group
        self._type_check()
    
    def to_obj(self):
        return dict(
            bbox_group=self.bbox_group.to_obj(),
            tinterval_group=self.tinterval_group.to_obj()
        )
    
    def __str__(self):
        return 'Match(bbox_group=%s, tinterval_group=%s)' % (self.bbox_group, self.tinterval_group)
    
    def __repr__(self):
        return self.__str__()
    
    def _type_check(self):
        if not isinstance(self.bbox_group, BBoxGroup):
            raise TypeError('bbox_group should be a BBoxGroup object')
        if not isinstance(self.tinterval_group, TIntervalGroup):
            raise TypeError('tinterval_group should be a TIntervalGroup object')

class Matches(list):
    """List of Match objects."""

    def __init__(self, matches=(), from_obj=False):
        if from_obj:
            list.__init__(self, map(lambda x: Match(**x, from_obj=True), matches))
        else:
            list.__init__(self, matches)
    
    def to_obj(self):
        return list(map(lambda x: x.to_obj(), self))
    
    def get_bbox_groups(self):
        return BBoxGroups(map(lambda x: x.bbox_group, self), from_obj=False)