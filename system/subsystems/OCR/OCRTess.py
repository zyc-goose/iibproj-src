import pytesseract, pdf2image
import os, re, json
from PIL import Image
from collections import namedtuple

from ...aux import printmsg
from .OCR import OCR
from ...elements.BBox import BBox, BBoxGroup, BBoxGroups
from ...elements.Coords import Coords
from ...cache.Cache import global_cache

class OCRTess(OCR):
    """Tesseract OCR"""

    def __init__(self, filename, scale='par', lang='eng'):
        path = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../../data/%s.pdf' % filename))
        super().__init__(path)
        self.filename = filename
        self.cache = global_cache
        self.scale = scale
        self.lang = lang
        self.update_cache_key()
    
    def update_cache_key(self):
        self.cache_key = 'OCRTess(%s, lang=%s, scale=%s)' % (self.filename, self.lang, self.scale)
        self.cache_key_obj = 'OCRTess(%s, lang=%s)' % (self.filename, self.lang)
    
    def set_scale(self, scale):
        self.scale = scale
        self.update_cache_key()
    
    def set_lang(self, lang):
        self.lang = lang
        self.update_cache_key()

    def process(self):
        if self.cache_key_obj in self.cache:
            obj = self.cache[self.cache_key_obj]
        else:
            images = self.pdf_to_images()
            obj = self.images_to_obj(images)
            self.cache[self.cache_key_obj] = obj
        bbox_groups = self.obj_to_bbox_groups(obj, scale=self.scale)
        self.result = bbox_groups
        return self.result
        
    def pdf_to_images(self):
        """Convert a single PDF file to a list of PIL images.
        returns:
            images - list of converted PIL images
        """
        filename = os.path.basename(self.path)
        printmsg.begin("Converting '%s' to PIL images" % filename)
        images = pdf2image.convert_from_path(self.path)
        printmsg.end()
        return images
    
    def images_to_obj(self, images):
        """Process the PIL images by OCR engine and store results in a dict.
        args:
            images - PIL images converted from PDF file
        returns:
            obj - a Python dict which stores all processing results from OCR
        """
        obj = {
            'totalPages': len(images), 
            'pages': []
        }
        for k, image in enumerate(images):
            printmsg.begin('Processing PIL images [%d/%d]' % (k+1, len(images)))
            tsvdata = pytesseract.image_to_data(image, lang=self.lang)
            tsvlines = tsvdata.split('\n')
            TSVBBox = namedtuple('TSVBBox', tsvlines[0])
            page_bbox = TSVBBox(*map(int, tsvlines[1].split()), None)
            page = {
                'pageNum': k + 1, 
                'width': page_bbox.width, 
                'height': page_bbox.height,
                'blocks': []
            }
            obj['pages'].append(page)
            for tsvline in tsvlines[2:]:
                line_splitted = tsvline.split()
                bbox = TSVBBox(*map(int, line_splitted[:11]), None)
                bbox_pos = {
                    'left': bbox.left,
                    'top': bbox.top,
                    'width': bbox.width,
                    'height': bbox.height
                }
                if bbox.level == 2: # block
                    block = {
                        'blockNum': len(page['blocks']) + 1,
                        **bbox_pos,
                        'pars': []
                    }
                    page['blocks'].append(block)
                elif bbox.level == 3: # paragraph
                    par = {
                        'parNum': len(block['pars']) + 1,
                        **bbox_pos,
                        'lines': []
                    }
                    block['pars'].append(par)
                elif bbox.level == 4: # line
                    line = {
                        'lineNum': len(par['lines']) + 1,
                        **bbox_pos,
                        'words': []
                    }
                    par['lines'].append(line)
                elif bbox.level == 5: # word
                    word = {
                        'wordNum': len(line['words']) + 1,
                        **bbox_pos,
                        'confidence': bbox.conf,
                        'text': line_splitted[-1]
                    }
                    line['words'].append(word)
        printmsg.end()
        return obj
    
    def obj_to_bbox_groups(self, obj, scale='par'):
        """Process the obj and return BBoxGroups object based on scale.
        args:
            obj - the dict as returned by self.images_to_obj(images)
            scale - could be 'word', 'line', 'par' (default), 'block'
        returns:
            bbox_groups - BBoxGroups object
        """
        bbox_groups = BBoxGroups()
        for page in obj['pages']:
            page_buf = []
            page_num = page['pageNum']
            for block in page['blocks']:
                block_buf = []
                for par in block['pars']:
                    par_buf = []
                    for line in par['lines']:
                        line_buf = []
                        for word in line['words']:
                            word_text = word['text']
                            line_buf.append(word_text)
                            if scale == 'word':
                                coords = self.extract_coords(word)
                                bbox = BBox(coords, word_text, page_num)
                                bbox_groups.append(bbox.to_group())
                        line_text = ' '.join(line_buf)
                        par_buf.append(line_text)
                        if scale == 'line':
                            coords = self.extract_coords(line)
                            bbox = BBox(coords, line_text, page_num)
                            bbox_groups.append(bbox.to_group())
                    par_text = ' '.join(par_buf)
                    block_buf.append(par_text)
                    if scale == 'par':
                        coords = self.extract_coords(par)
                        bbox = BBox(coords, par_text, page_num)
                        bbox_groups.append(bbox.to_group())
                block_text = ' '.join(block_buf)
                page_buf.append(block_text)
                if scale == 'block':
                    coords = self.extract_coords(block)
                    bbox = BBox(coords, block_text, page_num)
                    bbox_groups.append(bbox.to_group())
            page_text = ' '.join(page_buf)
            if scale == 'page':
                coords = self.extract_coords_from_page(page)
                bbox = BBox(coords, page_text, page_num)
                bbox_groups.append(bbox.to_group())
        print(bbox_groups)
        return bbox_groups
    
    def extract_coords(self, chunk):
        """Extract coordinates from a chunk.
        args:
            chunk - a dict object with attributes 'left', 'top', 'width' and 'height'
        returns:
            coords - a Coords object
        """
        x0 = chunk['left']
        x1 = x0 + chunk['width']
        y0 = chunk['top']
        y1 = y0 + chunk['height']
        return Coords(x0, y0, x1, y1)
    
    def extract_coords_from_page(self, page):
        """Extract coordinates from a page."""
        x0 = 10
        x1 = page['width'] - 20
        y0 = 10
        y1 = page['height'] - 15
        return Coords(x0, y0, x1, y1)

if __name__ == '__main__':
    ocr = OCRTess('lecture1')
    print(ocr.process(scale='block'))