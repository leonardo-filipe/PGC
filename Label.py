import cv2
import numpy as np
import random as rnd
from CommonUtils import Utils


class Label(object):
    MINIMUM_ANGLE_DIFF = 30

    def __init__(self, label_number, parent_list):
        self.cellList = []
        self.number = label_number
        self.parentList = parent_list
        self.color = (rnd.randint(0, 255), rnd.randint(0, 255), rnd.randint(0, 255))
        self.orientationSum = 0.0

    def __del__(self):
        self.remove_from_all_cells()
        self.parentList = None

    def get_cell_count(self):
        return len(self.cellList)
    
    def assign_to(self, cell):
        if cell.label is not None:
            raise ValueError('Trying to assign new Label to a cell that already has a label.')
        cell.label = self
        self.cellList.append(cell)
        self.orientationSum += cell.orientation

    def get_mean_cell_orientation(self):
        if self.get_cell_count() != 0:
            return self.orientationSum / self.get_cell_count()
        else:
            return None

    def remove_from_all_cells(self):
        for cell in self.cellList:
            cell.label = None
        self.cellList = []

    def get_label_patch_orientation(self):
        if self.get_cell_count() == 0:
            return None
        elif self.get_cell_count() == 1:
            return self.cellList[0].orientation
        else:
            # Construct label point representation
            cell_points = [(cell.row, cell.col) for cell in self.cellList]
            min_row = min(cell_points, key=lambda c: c[0])[0]
            max_row = max(cell_points, key=lambda c: c[0])[0]
            min_col = min(cell_points, key=lambda c: c[1])[1]
            max_col = max(cell_points, key=lambda c: c[1])[1]
            offset = 5
            label_height = max_row - min_row
            label_width = max_col - min_col
            cell_points = [(p[0] - min_row + offset, p[1] - min_col + offset) for p in cell_points]
            img = np.zeros((label_height + (2*offset), label_width + (2*offset)), np.uint8)
            for row, col in cell_points:
                img[row, col] = 255

            # Get label contour to compute angle
            _, cnts, __ = cv2.findContours(Utils.otsu_binary(img), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
            cv2.imwrite(Utils.IMG_DIR + 'label%d.png' % self.number, img)
            return Utils.get_contour_orientation(cnts[0])

    def is_barcode_pattern(self):
        if self.get_cell_count() > 0:
            label_angle = self.get_label_patch_orientation()
            mean_cell_angle = self.get_mean_cell_orientation()
            if label_angle is None or mean_cell_angle is None:
                return False

            angle_diff = Utils.calc_angle_diff(label_angle, mean_cell_angle)
            if angle_diff < Label.MINIMUM_ANGLE_DIFF:
                return False
            else:
                return True
        else:
            return False
