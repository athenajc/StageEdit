import os
import sys
import tkinter as tk
from aui import ImageObj
        
 
class Rect():
    def __init__(self, x0, y0, x1, y1):
        self.w, self.h = x1-x0, y1-y0  
        self.size = self.w, self. h
        self.set(x0, y0)         
        
    def set(self, x0, y0):
        w, h = self.size
        x1, y1 = x0 + w, y0 + h
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.left, self.top, self.right, self.bottom = x0, y0, x1, y1   
        self.topleft = x0, y0
        
        w2, h2 = w/2, h/2
        self.midbottom = x0 + w2, y1
        self.center = x0+w2, y0+h2
        
    def copy(self):
        return Rect(self.x0, self.y0, self.x1, self.y1)
                       
    def __str__(self):
        return str(np.array(self.get_rect()).astype(int))           
    
    def moveto(self, x, y, offset=(0, 0)):
        px, py = offset
        x0, y0 = x + px, y + py        
        self.set(x0, y0)
        
    def move_ip(self, dx=0, dy=0):
        if type(dx) == tuple:
            dx, dy = dx
        x0, y0 = self.x0 + dx, self.y0 + dy
        self.set(x0, y0) 
        
    def move(self, dx=0, dy=0):
        x0, y0 = self.x0 + dx, self.y0 + dy
        self.set(x0, y0)        
        return x0, y0
        
    def is_cross(self, box):
        if self.left > box.right or self.right < box.left:
            return False
        if self.top > box.bottom or self.bottom < box.top:
            return False
        return True        
        
    def clamp(self, box):        
        left, right, top, bottom = box.get_rect()
        x, y = self.x0, self.y0    
        if self.x0 < left:
            x = left + 1
        elif self.x1 > right:  
            x = right - self.w - 1
        if self.y0 < top:
            y = top + 1
        elif self.y1 > bottom:
            y = bottom - self.h - 1
        if x != self.x0 or y != self.y0:  
            x1, y1 = x + self.w, y + self.h
            return Rect(x, y, x1, y1)  
        return self    
        
    def get_rect(self):
        return self.left, self.right, self.top, self.bottom
        
    def get_size(self):
        return self.size     
        
    def inflate(self, w, h):
        x0, x1, y0, y1 = self.get_rect()
        return Rect(x0 + w, y0 + h, x1 - w, y1 - h)   
        
    def contains(self, obj):
        left, right, top, bottom = self.get_rect()
        x0, x1, y0, y1 = obj.get_rect()
        if x0 > left and x1 < right and y0 > top and y1 < bottom:
            return True
        return False
        
    def includep(self, p):
        x, y = p
        return (x >= self.left and x <= self.right and y >= self.top and y <= self.bottom)
            
    def include(self, x, y):
        return (x >= self.left and x <= self.right and y >= self.top and y <= self.bottom)      
          
    def set_right(self, x1):
        x0 = x1 - self.w
        self.set(x0, self.y0)
        
    def set_left(self, x0):
        self.set(x0, self.y0)
                

class Sprite():
    def __init__(self, page, pos, image, filename):
        self.page = page        
        self.dtype = 'image'
        self.tag = 'sprite'
        self.filename = filename
        self.imageobj = image
        self.tkimage = image.get_tkimage()        
        x, y = pos
        x, y = int(x), int(y)
        w, h = image.size
        self.size = (w, h)
        self.pos = x, y
        self.rect = Rect(x, y, x+w, y+h)
        
    def moveto(self, xy):
        self.pos = xy
        
    def set_rect(self, rect):
        self.pos = rect.x0, rect.y0
        self.rect = rect.copy()
        
    def get_data(self):
        dct = dict(size=self.size, pos=self.pos, image=self.filename)
        return dct        
                
class Page():
    def __init__(self, stage, index):
        self.stage = stage
        self.index = index
        self.objs = []
        self.size = stage.size
        self.bkg = ImageObj(size=self.size, mode="RGBA")    
        self.tkimage = self.bkg.get_tkimage()
        self.imgobjs = {}           
        
    def get_data(self):
        dct = {}
        dct['bkg'] = self.bkg.filename
        lst = []
        for obj in self.objs:
            lst.append(obj.get_data())
        dct['obj'] = lst
        return dct
        
    def set_data(self, dct):
        if dct == {} or dct == None:
            return
        self.objs = []    
        #self.imgobjs = {}
        filename = dct.get('bkg')
        if filename != None and filename != '':
            self.set_bkg(filename, self.size)
        for data in dct.get('obj', []):       
            fn = data.get('image')
            if fn == None or fn == '':
                continue    
            self.put_image(data.get('pos'), fn)
            
    def remove_bkg(self):
        self.bkg = ImageObj(size=self.size, mode="RGBA")    
        self.tkimage = self.bkg.get_tkimage()
        
    def remove_sprite(self, obj):
        if obj in self.objs:
            self.objs.remove(obj)
        
    def set_bkg(self, filename, size):
        self.bkg = self.stage.get_image(filename)
        if self.bkg.size != size:
            self.bkg.resize(size=size)
        self.tkimage = self.bkg.get_tkimage()
          
    def put_image(self, pos, filename):
        imgobj = self.stage.get_image(filename)
        obj = Sprite(self, pos, imgobj, filename)        
        self.objs.append(obj)       
        
    def draw_imgobj(self, size):
        imgobj = ImageObj(size=size)
        imgobj.draw_image((0, 0), self.bkg)
        draw = imgobj.draw
        for obj in self.objs:
            if obj.dtype == 'text':
               draw.text(obj.pos, obj.text, fill=obj.color, font=obj.font)
            elif obj.dtype == 'image':
               imgobj.draw_image(obj.pos, obj.imageobj)
        return imgobj
        
    def get_thumb(self, size):
        imgobj = self.draw_imgobj(self.stage.size)
        imgobj.resize(size)    
        return imgobj
        
 
class Stage():
    def __init__(self, master, size=(1024, 768)):
        self.master = master
        self.frame = master
        self.reset(size)
        
    def reset(self, size):
        self.size = size
        self.objs = []
        self.pages = []
        self.imagelist = []
        self.imgobjs = {}
        for i in range(10):
            self.new_page(i)
        self.curpage = self.pages[0]
        
    def set_update(self, flag=''):
        self.frame.event_generate("<<update_stage>>", when='tail')
        
    def new_page(self, i):
        page = Page(self, i)
        self.pages.append(page)
        
    def set_page(self, page):
        self.curpage = page      
        self.set_update('curpage')
        
    def load_image(self, filename):
        if '.svg' in filename:
            w, h = self.size
            w, h = int(w/3), int(h/3)
            imgobj = ImageObj(filename, mode="RGBA", size=(w, h))
        else:
            imgobj = ImageObj(filename, mode="RGBA")
        self.imgobjs[filename] = imgobj
            
    def add_image(self, filename):
        if not filename in self.imagelist:
           self.imagelist.append(filename)
           self.load_image(filename)
           
    def remove_image(self, filename):
        if not filename in self.imagelist:
            return False
        for page in self.pages:
            for obj in page.objs:
                if obj.filename == filename:
                    return False
        self.imagelist.remove(filename)
        return True

    def get_image(self, filename):
        if not filename in self.imgobjs:        
           self.add_image(filename)         
        imgobj = self.imgobjs.get(filename)
        return imgobj
        
    def set_data(self, dct):        
        if dct == None or dct == {}:
            return
        self.size = dct.get('size', (1024, 768))
        for fn in dct.get('images', []):
            self.add_image(fn)    
        for page in self.pages:
            dct1 = dct.get(page.index, {})
            page.set_data(dct1)
            
    def get_data(self):
        dct = {}
        dct['size'] = self.size
        dct['images'] = self.imagelist
        for page in self.pages:  
            dct[page.index] = page.get_data()
        return dct

        

if __name__ == "__main__":       
    from StageED import MainFrame
    from aui import App
    app = App(title='APP', size=(1500,860))
    frame = MainFrame(app)
    app.mainloop()




