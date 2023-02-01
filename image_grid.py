import os
import sys
import tkinter as tk
import tkinter.ttk as ttk
from PIL import Image, ImageTk
from aui import ImageObj, Panel, aFrame, App


thumbdct = {}


class ImageThumb(tk.Frame):
    def __init__(self, master, filename, image=None, name=None, action=None):           
        tk.Frame.__init__(self, master)
        self.selected = False
        self.action = action
        self.name = name
        self.filename = filename
        if self.name == None:
            self.name = os.path.basename(filename)
        self.bg = self.cget('background')
        self.config(cursor='hand1')
        self.selected = False
        self.rollover = False        
        self.init_image(filename, image)
        self.init_canvas(86, 86, self.imgobj)
 
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)  
        self.canvas.bind('<ButtonRelease-1>', self.on_click)          
        self.event_time = 0
    
    def init_canvas(self, w, h, image):    
        canvas = tk.Canvas(self, width=w, height=h, bg='#fff')
        canvas.pack(fill='both', expand=True, padx=5, pady=5)
        canvas.master = self
        self.canvas = canvas
        self.image = image
        self.tkimage = self.image.get_tkimage() 
        canvas.create_image(12, 5, image=self.tkimage, anchor='nw', tag='imageobj')     
        fn = os.path.basename(self.filename)
        n = len(fn)
        if n > 13:
            fn = fn[0:13] 
        canvas.create_text(w/2, h-20, text=fn, anchor='n', tag='text', font=('mono',8))  
        
    def load(self, filename):
        filename = os.path.realpath(filename)    
        image = ImageObj.thumbnail(filename, size=(64, 64))
        return image     
        
    def update_image(self, image):
        self.image = image
        self.tkimage = image.get_tkimage()
        self.canvas.itemconfig('imageobj', image=self.tkimage)
        
    def init_image(self, filename, image):       
        if image == None:
           image = self.load(filename)     
        self.tkimage = image.get_tkimage()
        self.imgobj = image   
                        
    def load(self, filename):
        if filename in thumbdct:
            return thumbdct[filename] 
        image = ImageObj.thumbnail(filename, size=(64, 64))
        thumbdct[filename] = image
        return image    
        
    def update(self):
        if self.rollover:
            if self.selected:
               self.config(bg='#aa0')
            else:
               self.config(bg='yellow')
        else:  
            if self.selected:
                self.config(bg='gray')
            else:    
                self.config(bg=self.bg)
        if self.selected:
            self.config(relief='sunken')
        else:
            self.config(relief='flat')                
        tk.Frame.update(self)    
        
    def on_select(self, selected, event=None):        
        self.set_selected(selected)
            
    def set_selected(self, selected):
        self.selected = selected        
        self.update()
       
    def on_enter(self, event):
        self.rollover = True
        self.update()
        
    def on_leave(self, event):
        self.rollover = False
        self.update()
  
    def on_click(self, event=None):        
        if self.action != None:
            event.widget = self
            self.action(event)
        else:
            self.selected = not self.selected
            self.update()
                    
class ImageGrid(Panel):
    def __init__(self, master, items=None, **kw):          
        super().__init__(master, cursor='arrow', bg='#d9d9d9', **kw)        
        self.menuitems = items
        self.tframe = self
        self.bg = '#ccc'
        self.config(state='disable')
        self.config(bg='#ccc')          
        self.config(spacing1=10)    # Spacing above the first line in a block of text
        self.config(spacing2=10)    # Spacing between the lines in a block of text
        self.config(spacing3=10)    # Spacing after the last line in a block of text
        self.objs = []
        self.add_scrollbar()              
        if self.menuitems != None:
           self.menu = self.add_menu(self.menuitems)
        
    def on_click(self, event):        
        for obj in self.objs:
            if obj == event.widget:                
                obj.on_select(True, event)
            elif obj.selected:
                obj.on_select(False) 
        
    def clear_all(self):
        self.config(state='normal')
        self.delete('1.0', 'end')       
        self.config(state='disable')
        self.objs = []
        if self.menuitems != None:
           self.menu = self.add_menu(self.menuitems)
            
    def set_list(self, lst):
        self.clear_all()
        for fn in lst:
            self.add_image(fn)         
                
    def add_obj(self, obj):
        self.objs.append(obj)
        idx1 = self.index('insert')
        self.window_create('insert', window=obj)        
        self.insert('insert', ' ')
        idx2 = self.index('insert')
        obj.range = (idx1, idx2)
        obj.event_time = 0        
        self.update()
        
    def add_image(self, filename, image=None, action=None):
        if action == None:
            action = self.on_click
        obj = ImageThumb(self.tframe, filename, image=image, action=action)        
        self.add_obj(obj)

    def remove_image(self, obj):
        idx1, idx2 = obj.range
        self.delete(idx1, idx2)
        self.objs.remove(obj)
                
    def get_selection(self, clear=False):
        lst = []
        for obj in self.objs:
            if obj.selected:
                lst.append(obj)
        if clear == True:
            self.clear_selection()         
        return lst                
            
    def clear_selection(self):
        for obj in self.objs:
            obj.set_selected(False)
            
            
class DirGrid(ImageGrid):
    def __init__(self, master, items=None, **kw):
        super().__init__(master, **kw)                
        self.folder_image = ImageObj('resource/Folder.png', size=(64, 64))
        self.path = os.path.realpath('.')
        self.menuitems = items        
        
    def add_folder(self, fn, name=None):
        if name == None:
            name = os.path.basename(fn)
        obj = ImageThumb(self.tframe, fn, image=self.folder_image, name=name)
        obj.action = self.on_click_folder
        self.add_obj(obj)
        
    def add_file(self, filename):
        name = os.path.basename(filename)
        obj = ImageThumb(self.tframe, filename, name=name)
        obj.action = self.on_click_file
        self.add_obj(obj)

    def is_image(self, fn):
        if not '.' in fn:
            return False
        ext = fn.split('.')[-1]
        if ext in ['svg', 'png', 'gif', 'jpg']:
            return True
        else:
            return False
            
    def set_dir(self, path):      
        self.path = path
        self.clear_all()  
        
        self.add_folder(self.path + '/..', name = '..')
        lst = os.listdir(path)
        lst.sort()
        if path[-1] != os.sep:
            path += os.sep
        for s in lst:
            fn = path + s
            if os.path.isdir(fn):
                self.add_folder(fn)
            elif os.path.isfile(fn) and self.is_image(fn):
                self.add_file(fn)      

    def go_upper_folder(self):
        p = self.path.split(os.sep)
        if p[-1] == '':
            p = p[0:-2]
        else:
            p = p[0:-1]
        p1 = os.sep.join(p)
        self.set_dir(p1)
                
    def on_doulble_click(self, obj):
        self.set_dir(obj.filename)
        return
        if obj.ftype == 'folder':
            if obj.name == '..':
                self.go_upper_folder()
            else:
                self.set_dir(obj.filename)
           
    def check_double_click(self, obj, event):
        d = event.time - obj.event_time        
        if d < 1000:
            double_click = True
            obj.event_time = 0
            self.on_doulble_click(obj)
            return True       
        else:
            return False
        
    def on_click_file(self, event):                
        obj = event.widget
        obj.set_selected(not obj.selected)
        
    def on_click_folder(self, event):  
        obj = event.widget           
        if obj.selected :
            self.clear_selection()
            obj.set_selected(True)
            if self.check_double_click(obj, event):
                return
        else:                     
            self.clear_selection()  
            obj.set_selected(True)
        obj.event_time = event.time      
        
        
if __name__ == "__main__":     
    path = '/link/data/svg'

    class TestFrame(aFrame):
        def __init__(self, master, **kw):
            super().__init__(master, **kw)    
            lst = [('Add file', self.on_open_file)]
            panel = self.get('panel', height=1)
            panel.add_menu(lst)
            panel.pack()
            self.grid = grid = DirGrid(self)       
            grid.set_dir(path)    
            grid.pack(fill='both', expand=True)            
                    
        def open_file(self, filename):  
            self.grid.add_image(filename)
            
        def on_open_file(self, event=None):   
            filename = self.root.ask('openfilename', ext='img')
            print('Filedialog return ', filename) 
            if filename == None or len(filename) == 0:
                return
            self.open_file(filename)
              

    app = App(title='Test FileDialog', size=(800,900))        
    TestFrame(app)
    app.mainloop()        




