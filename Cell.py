import cv2
import numpy as np
from CommonUtils import Utils


class Cell(object):
    COMPACTNESS_THRESHOLD = 3
    CONTOUR_SIZE_THRESH = 10

    def __init__(self, row, col, cell_img):
        self.img = cell_img
        self.row = row
        self.col = col
        self.hasBarcodeFeatures = False
        self.orientation = 0
        self.label = None
        self.contours = None
        self.evaluate_barcode_features()
    
    def get_img_contours(self):
        if self.contours is None:
            _, cnts, __ = cv2.findContours(self.img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            self.contours = cnts
        return self.contours
    
    def get_contour_img(self):
        self.get_img_contours()
        cell_img = cv2.cvtColor(255-self.img, cv2.COLOR_GRAY2RGB)
        return cv2.drawContours(cell_img, self.contours, -1, (0,255,0), 3)
    
    def get_skeletonized_image(self):
        """ OpenCV function to return a skeletonized version of img, a Mat object"""
        #  hat tip to http://felix.abecassis.me/2011/09/opencv-morphological-skeleton/
        img = self.img.copy() # don't clobber original
        skel = self.img.copy()
        skel[:, :] = 0
        kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3,3))
        while True:
            eroded = cv2.morphologyEx(img, cv2.MORPH_ERODE, kernel)
            temp = cv2.morphologyEx(eroded, cv2.MORPH_DILATE, kernel)
            temp = cv2.subtract(img, temp)
            skel = cv2.bitwise_or(skel, temp)
            img[:, :] = eroded[:, :]
            if cv2.countNonZero(img) == 0 or cv2.countNonZero(img) == img.size:
                break
        return skel
    
    def get_skeletonized_img_contours(self):
        skeletonized = self.get_skeletonized_image()
        cnt_im, cnts, hierarchy = cv2.findContours(skeletonized, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        self.contours = cnts
        return cnts
    
    def evaluate_barcode_features(self):
        self.get_img_contours()
        
        # Filter out smaller contours which should be random noise
        filtered_contours = filter(lambda c: Utils.get_contour_size(c) > Cell.CONTOUR_SIZE_THRESH, self.contours)
        
        # Get contour orientations
        angles = [Utils.get_contour_orientation(contour) for contour in filtered_contours]
        angles = filter(lambda a: a is not None, angles)
        
        # Eliminate cells with a small number of valid contours
        element_count = len(angles)
        if element_count < 2:
            # cell is not part of barcode
            self.hasBarcodeFeatures = False
            return self
        
        # Use K-means clustering to determine if there is a prevalent orientation among contours
        # Define criteria = ( type, max_iter = 10 , epsilon = 0.5 )
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 0.5)
        flags = cv2.KMEANS_RANDOM_CENTERS
        cluster_elements = np.float32(angles)
        cluster_elements = cluster_elements.reshape((element_count, 1))
        compactness, labels, centers = cv2.kmeans(cluster_elements, 2, None, criteria, 10, flags)
        
        # Smaller compactness should occur for a group of similarly oriented contours
        mean_compactness = compactness / float(element_count)
        if mean_compactness < Cell.COMPACTNESS_THRESHOLD:
            self.hasBarcodeFeatures = True
            self.orientation = Utils.get_cluster_mean(cluster_elements, labels)
            return self
        else:
            self.hasBarcodeFeatures = False
            return self
    
    def get_image_with_border(self, border_color=(127, 127, 127)):
        cell_img = cv2.cvtColor(255-self.img, cv2.COLOR_GRAY2RGB)
        if border_color is None:
            return cell_img
        cell_img[0:2, :] = border_color
        cell_img[:, 0:2] = border_color
        cell_img[-2:, :] = border_color
        cell_img[:, -2:] = border_color
        return cell_img
    
    def get_fill_image(self, fill_color=(127, 127, 127)):
        cell_img = cv2.cvtColor(255-self.img, cv2.COLOR_GRAY2RGB)
        if fill_color is None:
            return cell_img
        cell_img[:, :] = fill_color
        return cell_img
    
    def get_label_mask_image(self, label):
        img = self.img.copy()
        if self.label == label:
            img[:, :] = 255
            return img
        else:
            img[:, :] = 0
            return img
    
    def get_label_border_image(self):
        if self.label is not None:
            label_color = self.label.color
            cell_img = self.get_image_with_border(label_color)
            return cell_img
        else:
            return self.get_image_with_border(None)
    
    def get_label_orientation_image(self):
        if self.label is not None:
            label_color = self.label.color
            cell_img = self.get_fill_image(label_color)
            font = cv2.FONT_HERSHEY_SIMPLEX
            text_color = (255-label_color[0], 255-label_color[1], 255-label_color[2])
            cv2.putText(cell_img, str(self.orientation), (2, 30), font, 0.6, text_color, 2, cv2.LINE_AA)
            return cell_img
        else:
            return self.get_fill_image(None)
