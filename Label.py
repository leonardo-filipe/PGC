import random as rnd

class Label(object):
    def __init__(self, labelNumber, parentList):
        self.count = 0
        self.number = labelNumber
        self.parentList = parentList
        self.color = (rnd.randint(0,255), rnd.randint(0, 255), rnd.randint(0, 255))
        self.orientationSum = 0.0
    
    def assignTo(self, obj):
        if obj.label != None:
            raise ValueError('Trying to assign new Label to an object that already has a label.')
        obj.label = self
        self.count += 1
        self.orientationSum += obj.orientation

    def getMeanOrientation(self):
        if self.count != 0:
            return self.orientationSum / self.count
        else:
            return 0.0