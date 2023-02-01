import os
import sys
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from fileio import *

from aui import ImageObj, App, aFrame, Layout, Panel, MenuBar
import aui
from image_grid import ImageGrid, DirGrid, ImageThumb
from stage import Stage, Page, Sprite, Rect

from stage_menu import StageMenu
import json
import DB
                
class Notebook(ttk.Notebook):
    def add_frame(self, frame, label):
        self.add(frame, text=label.center(17))  
        
class SelectFrame():
    def __init__(self, canvas):
        self.canvas = canvas
        self.obj = None
        self.size = 100, 100
        self.item = canvas.create_rectangle(0, 0, 10, 10, dash=(5,1), tag=('selectframe','fg'))     
        canvas.tag_bind(self.item, '<ButtonPress-1>', self.on_press)
        canvas.tag_bind(self.item, '<ButtonRelease-1>', self.on_release)
        canvas.tag_bind(self.item, '<Motion>', self.on_motion)
     
        self.offset = 0, 0
        self.pos = 0, 0
        self.dragging = False
        
    def set_rect(self, pos, size):
        canvas = self.canvas
        x, y = pos    
        w, h = size        
        x1, y1 = x+w, y+h
        x2, y2 = x+w/2, y+h/2
        canvas.delete('selectframe')
        self.item = self.canvas.create_rectangle(x, y, x1, y1, dash=(3,3), tag=('selectframe','fg'))  
        d = 3 
        canvas.create_rectangle(x1-d, y1-d, x1+d, y1+d, fill='#444', tag=('selectframe', 'dot'))
        #canvas.create_rectangle(x2-d, y1-d, x2+d, y1+d, fill='#444', tag=('selectframe', 'dot'))
        #canvas.create_rectangle(x1-d, y2-d, x1+d, y2+d, fill='#444', tag=('selectframe', 'dot'))
        self.size = w, h
        self.pos = x, y
        self.offset = w/2, h/2
        #canvas.itemconfig('dot', cursor='cross')        
        
    def on_press(self, event):
        self.dragging = 'move'
        x, y = event.x, event.y
        x0, y0 = self.pos        
        dx, dy = x-x0, y-y0
        w, h = self.size
        d = 10
        if abs(dx-w) < d and abs(dy-h) < d:
             self.dragging = 'resize'
             print('resize', dx, dy)
             self.canvas.config(cursor='cross')
        self.offset = dx, dy
        self.canvas.tag_raise(self.item)
        
    def on_motion(self, event):
        if self.dragging == False:
            return
        dx, dy = self.offset    
        x, y = event.x-dx, event.y-dy  
        if self.dragging == 'resize':
            x0, y0 = self.pos
            w, h = event.x - x0, event.y - y0            
            self.size = w,h
        else:                  
            self.pos = x, y
            self.canvas.moveto(self.obj.canvas_item, x=x, y=y)
        
        self.set_rect(self.pos, self.size)
        
    def on_release(self, event):
        self.dragging = False
        obj = self.obj
        x, y = self.pos
        obj.moveto(self.pos)
        item = obj.canvas_item
        self.canvas.config(cursor='arrow')
        #self.canvas.scale(item, w, h, w1/w, h1/w)
        #self.canvas.moveto(item, x=x, y=y)
        #self.canvas.tag_lower(self.item)
        self.set_rect((x, y), self.size)
        
    def includep(self, p):
        x, y = p
        x0, y0 = self.pos
        if x < x0 or y < y0:
            return False            
        w, h = self.size
        x1, y1 = x0 + w, y0 + h
        if x > x1 or y > y1:
            return False            
        return True
            
    def set_obj(self, obj):        
        self.obj = obj
        self.set_rect(obj.pos, obj.size)
        
            
class StageCanvas(tk.Canvas):
    def __init__(self, master, size,  **kw):
        super().__init__( master, bg='#253545', **kw)  
        self.size = size        
        self.root = master.winfo_toplevel()
        self.imageobj = None
        self.page = None
        self.objs = []
        w, h = size
        self.configure(width=w, height=h)
        self.selectframe = SelectFrame(self)
        self.bind('<ButtonPress-1>', self.on_press)
        self.bind('<ButtonRelease-1>', self.on_release)  
        self.bind('<Motion>', self.on_motion)
        self.create_rectangle(1, 1, w, h, outline='#777',width=3, tag='border')
        self.create_text(10, 10, text='info', fill='yellow', anchor='nw', font=('mono', 12), tag=('info', 'fg')) 
                
    def reset(self):
        self.clear_all()
        self.imageobj = None
        self.page = None
        self.objs = []
        
        self.selectframe = SelectFrame(self)
         
    def on_motion(self, event):
        x, y = event.x, event.y
        if self.selectframe.dragging != False:
            self.selectframe.on_motion(event)
            
    def on_press(self, event):
        x, y = event.x, event.y
        if self.selectframe.includep((x, y)):
            s = str((x, y, 'press'))
            self.selectframe.on_press(event)
        else:
            item = self.find_closest(x, y)
            obj = self.select_obj(item)
            s = str((x, y, item))    
            if obj != None:
                self.selectframe.on_press(event)
        self.itemconfig('info', text=s)
                
    def on_release(self, event):
        x, y = event.x, event.y        
        
        if self.selectframe.dragging != False:
            s = str((x, y, 'release'))
            self.selectframe.on_release(event)
        else:
            item = self.find_closest(x, y)
            obj = self.select_obj(item)
            s = str((x, y, item))
        self.itemconfig('info', text=s)
        
    def select_obj(self, item):
        for obj in self.objs:
            if obj.canvas_item in item:
                self.selectframe.set_obj(obj)
                return obj
        return None
        
    def set_bkg(self, tkimage):
        self.tkimage = tkimage
        self.image_item = self.create_image(0, 0, image=tkimage, anchor='nw', tag='bkg')  
        
    def add_sprite(self, obj):
        x, y = obj.pos
        obj.canvas_item = self.create_image(x, y, image=obj.tkimage, anchor='nw', tag=('obj',obj.tag))  
        self.selectframe.set_obj(obj)
        self.objs.append(obj)
        
    def get_selection(self):
        return self.selectframe.obj
        
    def set_page(self, page):
        self.page = page
        self.clear_all()
        self.set_bkg(page.tkimage)
        for obj in page.objs:
            self.add_sprite(obj)      
        self.tag_lower('bkg')  
        self.tag_raise('fg')
        
    def set_item_image(self, tag, image):
        self.itemconfig(tag, image=image)   

    def draw_to_image(self, imageobj):
        draw = imageobj.get_draw()
        bkg = self.page.bkg
        imageobj.draw_image((0, 0), bkg)
        for obj in self.objs:
            imageobj.draw_image(obj.pos, obj.imageobj)        
                
    def on_save_image(self):        
        w, h = self.size
        imageobj = ImageObj(size=(w, h))
        self.draw_to_image(imageobj)  
        print('on_save_image')
        filename = self.root.ask('saveasfile', ext='img')
        if filename == None or len(filename) == 0:
            filename = '/home/athena/tmp/canvas.png'
        imageobj.save(filename)    
        
    def clear_all(self):
        self.delete('bkg')
        self.delete('obj')
        
class StageFrame(tk.Frame):
    def __init__(self, master, stage, **kw):
        tk.Frame.__init__(self, master, bg='#354555', relief='sunken', **kw)
        self.root = master.winfo_toplevel()
        self.stage = stage
        lst = [('Clear bkg', self.on_clear_bkg),
               ('Delete Sprite', self.on_delete_sprite),
               ('Export Image', self.on_export_image),
              ]  
        w, h = stage.size
        menu = Panel(self, style='h', items=lst, height=1)
        menu.place(x=10, y=2, width=w+4, height=53)  
        
        self.size = w, h
        self.canvas = StageCanvas(self, stage.size)
        y = 60
        self.canvas.place(x=10, y=y, width=w+4, height=h+y)  
        
    def reset(self):
        self.update_stage()
        
    def on_clear_bkg(self, event):
        self.stage.curpage.remove_bkg()
        self.stage.set_update('curpage')
        
    def on_export_image(self, event=None):
        self.canvas.on_save_image()
        
    def on_delete_sprite(self, event):
        obj = self.canvas.get_selection()
        if obj == None:
            return
        self.stage.curpage.remove_sprite(obj)
        self.stage.set_update('curpage')
    
    def update_stage(self):
        page = self.stage.curpage
        self.canvas.set_page(page)
        tk.Frame.update(self)     
        

class PageGrid(ImageGrid):
    def __init__(self, master, stage):
        ImageGrid.__init__(self, master)
        self.stage = stage  
        
    def on_click_page(self, event):                
        obj = event.widget        
        self.stage.set_page(obj.page)
        
    def add_page(self, page):
        image = page.get_thumb(size=(64, 48))
        s = 'Page ' + str(page.index+1)
        obj = ImageThumb(self.tframe, filename=s, image=image, name=s, action=self.on_click_page)
        page.thumb = obj
        obj.page = page
        self.add_obj(obj)        
        
    def update_all(self):
        self.clear_all()
        for page in self.stage.pages:            
            self.add_page(page)
            
    def update_page(self):
        page = self.stage.curpage
        obj = page.thumb
        image = page.get_thumb(size=(64, 64))
        obj.update_image(image)             

class MainFrame(aFrame, StageMenu):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.vars = {'size':(1024, 768)}
        self.history = []
        self.filename = ''        
        
        self.path = realpath('~/data/')        
             
        self.stage = Stage(self)       
        layout = Layout(self)
        menu = self.add_menubar(self)       
        layout.add_left(menu, 100)
        
        f1 = self.add('frame')
        f2 = self.add('frame')
        layout.add_H2(f1, f2, 0.35)         
           
        self.init_left(f1)
        self.init_center(f2)        
        
        self.filepath = dirname(realpath(__file__))        
        self.lastfile = None
        self.load_ini()        
        if self.lastfile != None:
            self.filepath = dirname(self.lastfile)
            self.load_stage(self.lastfile)    
            
        self.bind("<<update_stage>>", self.update_stage)          
        print(self.filepath)
        print(self.lastfile)
        
    def on_new_stage(self):
        self.fstage.reset()
        self.canvas.clear_all()
        self.stage.reset(self.vars['size'])
        self.page_grid.update_all()
        self.update_stage()
        
    def set_size(self, w, h):
        if self.canvas.size == (w, h):
            return
        #self.canvas.on_resize_image(size=(w, h))
        self.set_status('Size', self.canvas.size)
        self.vars['size'] = (w, h)
        
    def get_data(self, tag=None):
        dct = {}        
        dct['size'] = self.stage.size
        return dct
        
    def set_data(self, dct):
        pass
        
    def load_stage(self, fn):
        self.filename = fn
        self.add_history(fn)
        text = fread(fn).strip()
        if text == '':
            return
        try:
             dct = eval(text)
        except Exception as e:    
             print('dct errot', e)    
        self.stage.set_data(dct)
        self.image_grid.set_list(self.stage.imagelist)
        self.winfo_toplevel().title('Stage Editor  -    ' + fn)
        self.page_grid.update_all()
        self.update_stage()
        
    def save_stage(self, fn):
        dct = self.stage.get_data()
        from pprint import pformat
        text = pformat(dct)
        fwrite(fn, text)
        self.filename = fn
        self.winfo_toplevel().title('Stage Editor  -    ' + fn)
        
    def init_center(self, master):
        frame = self.twoframe(master, style='v', sep=0.7 )   
        fstage = StageFrame(frame.top, self.stage)
        self.fstage = fstage     
        fstage.pack(fill='both', expand=True)  
        self.canvas = fstage.canvas 

        notebook = Notebook(frame.bottom)       
        notebook.pack(fill='both', expand=True) 
        
        self.page_grid = PageGrid(frame.bottom, self.stage)
        self.page_grid.pack(fill='both', expand=True)        
        self.page_grid.update_all()
        notebook.add_frame(self.page_grid, 'Page')
        
        self.msg = msg = self.add_msg(frame.bottom)
        notebook.add_frame(msg, 'Message')
        self.root.msg = msg
        sys.stdout = msg       

        return frame
        
    def init_left(self, master):        
        frame = self.twoframe(master, style='v', sep=0.5)  
        lst1 = [
            ('Remove', self.on_remove_image),
            ('Set bkg', self.on_set_bkg),
            ('Put stage', self.on_put_on_stage), 
        ]
        layout1 = Layout(frame.top)
        panel1 = Panel(frame.top, style='h', items=lst1)        
        layout1.add_top(panel1, 45)
        grid1 = self.image_grid = ImageGrid(frame.top)
        layout1.add_box(grid1)
        
        lst = [('Add to images', self.on_add_to_images)]
        layout2 = Layout(frame.bottom)
        panel2 = Panel(frame.bottom, style='h', items=lst)        
        layout2.add_top(panel2, 45)
        grid2 = self.dir_grid = DirGrid(frame.bottom)   
        layout2.add_box(grid2)
        grid2.set_dir(self.path + os.sep + 'gallery')        
        return frame
        
    def add_button(self, frame, text, action):
        button = tk.Button(frame, text=text, bg='#eaeaea')
        button.pack(side='left', fill='none', expand=False)
        button.bind('<ButtonRelease-1>', action)
        
    def update_stage(self, event=None):
        self.fstage.update_stage()
        self.page_grid.update_page()

    def put_on_stage(self, lst):
        w, h = self.stage.size
        w2, h2 = int(w/2), int(h/2)
        for imgobj in lst:
            self.stage.curpage.put_image((w2, h2), imgobj.filename)
        self.update_stage()
                 
    def on_put_on_stage(self, event=None):
        lst = self.image_grid.get_selection(clear=True)        
        self.put_on_stage(lst)
        
    def set_bkg(self, filename):
        self.stage.curpage.set_bkg(filename, size=self.vars['size'])        
        self.update_stage()
        
    def on_set_bkg(self, event=None):
        lst = self.image_grid.get_selection(clear=True)          
        if lst != []:
            self.set_bkg(lst[0].filename)      
        
    def add_image(self, filename):
        if not filename in self.stage.imagelist:
           self.stage.add_image(filename)
           self.image_grid.add_image(filename)
           
    def add_images(self, images):
        for obj in images:
            if obj.name == '..':
                continue
            self.add_image(obj.filename)
            
    def on_remove_image(self, event=None):
        lst = self.image_grid.get_selection(clear=True)   
        for obj in lst:
            fn = obj.filename
            if self.stage.remove_image(fn) == True:
               self.image_grid.remove_image(obj)
               self.image_grid.update()
        
    def on_add_image(self, event=None):   
        filename = self.file_dialog(filedialog.askopenfile, 'Open', 'r', 'image')   
        print('Filedialog return (%s)'%filename) 
        if filename == None or filename == '':
            return
        self.add_image(filename)        
        
    def on_add_to_images(self, event=None):           
        lst = self.dir_grid.get_selection(clear=True)  
        self.add_images(lst)
        
    def destroy(self):
        try:
            self.save_ini()
            print('save_ini done')
        except:
            print('destroy save_ini error') 


if __name__ == "__main__":       
    app = App(title='APP', size=(1920,1080), Frame=None)
    frame = MainFrame(app)
    frame.pack(fill='both', expand=True)
    app.mainloop()



