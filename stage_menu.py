import tkinter as tk
from fileio import *
import aui
import DB

class StageMenu():        
    def add_menubar(self, frame):
        names = 'New,Open,,Reload,,History,,Save,Save as,,Clear,,Resize,,Add Image'
        menubar = aui.MenuBar(frame, items=names.split(',')) 
        menubar.pack(side='top', fill='x', expand=False)
        menubar.bind_action('New', self.on_new_file)
        menubar.bind_action('Open', self.on_open_file)        
        menubar.bind_action('Reload', self.on_reload_file)        
        menubar.bind_action('History', self.on_open_history)
        menubar.bind_action('Save', self.on_save_file)
        menubar.bind_action('Save as', self.on_saveas_file)        
        menubar.bind_action('Resize', self.on_resize)
        menubar.bind_action('Clear', self.on_clear_stage)
        #menubar.bind_action('Undo', self.on_undo)
        #menubar.bind_action('Redo', self.on_redo)
        menubar.bind_action('Add Image', self.on_add_image)
        self.hmenu = None
        return menubar
        
    def set_status(self, *info):
        print(str(info), end='\n')
        
    def on_clear_stage(self, event=None):
        self.on_new_stage()
        
    def new_file(self, size):
        w, h = size
        self.set_status('File', 'New file')
        self.set_status('Size', (w, h))
        self.on_new_stage()
        self.vars['size'] = (w, h)        
        
    def on_new_file(self, event=None):
        w, h = self.vars['size']
        s = '%d,%d' % (w, h)
        r = tk.simpledialog.askstring('New image', 'width, height', initialvalue=s)    
        if r == None:
            return
        if type(r) != str:
            self.msg.puts(type(r), r)
            return    
        w, h = eval(r)
        self.new_file(size=(w, h))
        return w, h
        
    def on_resize(self, event=None):
        w, h = self.vars['size']
        s = '%d,%d' % (w, h)
        r = tk.simpledialog.askstring('Resize image', 'width, height', initialvalue=s)    
        if r == None:
            return
        if type(r) != str:
            self.msg.puts(type(r), r)
            return    
        w, h = eval(r)
        self.set_size(w, h)
        return w, h
        
    def file_dialog(self, dialog, op='Open', mode='r', ftype='stage'):        
        if ftype == 'image':
            filetypes = [('Image files', '.*'), ('all files', '.*')]
            path = '/home/athena/Images/svg/'
            op += ' Image '
        elif ftype == 'stage':
            filetypes = [('Stage files', '.stg'), ('all files', '.*')]
            path = __file__
            op += ' Stage'
        else:
            filetypes = [('all files', '.*')]
            path = __file__
            
        filepath = os.path.dirname(os.path.realpath(path))        
        filename = dialog(defaultextension='.svg', mode = mode,
               filetypes = filetypes,
               initialdir = filepath,
               initialfile = '',
               parent = self,
               title = op + ' File dialog'
               )
        if filename == None:
            return None
        return filename.name
        
    def on_open_file(self, event=None):   
        filename = self.file_dialog(tk.filedialog.askopenfile, 'Open', 'r', 'stage')   
        print('Filedialog return (%s)'%filename) 
        if filename == None or filename == '':
            return
        self.open_file(filename)    
        
    def on_save_file(self, event=None):   
        if self.filename == '' or self.filename == None:
            self.on_saveas_file(event)
            return
        filename = self.filename
        print('save ', filename)
        self.save_file(filename)  

    def on_saveas_file(self, event=None): 
        filename = self.file_dialog(tk.filedialog.asksaveasfile, 'Save as', 'w', 'stage')           
        if filename == None or filename == '':
            print('Error : Filedialog return (%s)'%filename) 
            return
        print('Filedialog return (%s)'%filename)         
        self.saveas_file(filename)      
        
    def on_reload_file(self, event=None):
        self.open_file(self.filename)        
        
    def open_file(self, filename):
        self.filename = filename
        fn = os.path.basename(filename)        
        self.load_stage(filename)
        
        self.add_history(filename)        
        
    def save_file(self, filename):
        if filename == None:
            return  
        filename = os.path.realpath(filename)     
        self.save_stage(filename)       
        
    def saveas_file(self, filename):
        self.add_history(filename)
        self.save_stage(filename)         
        
    def unpost_history(self):
        if self.hmenu != None:
            self.hmenu.unpost()
            self.hmenu.unbind_all('<ButtonRelease-1>')
            self.hmenu = None  
        
    def add_history(self, filename):
        filename = os.path.realpath(filename)            
        if filename in self.history:
            index = self.history.remove(filename)         
        self.history.insert(0, filename)
            
    def on_select_history(self, event=None):
        menu = self.hmenu        
        if menu == None:
            return
        if event.x > menu.winfo_reqwidth():
            self.unpost_history()        
            return
        n = menu.index('end')
        y = event.y
        lst = []
        for i in range(n+1):
            lst.insert(0, (i, menu.yposition(i)))
        for i, py in lst:
            if y >= py:
                self.open_file(self.history[i-1])
                break                        
        self.unpost_history()        
        
    def on_open_history(self, event):
        if self.hmenu != None:
            self.unpost_history()          
            return
        menu = tk.Menu()        
        menu.bind_all('<ButtonRelease-1>', self.on_select_history) 
        for s in self.history:
            menu.add_command(label=s)          
        x, y = event.x, event.y  
        x1 = self.winfo_rootx() + menu.winfo_reqwidth() + 20  
        y1 = self.winfo_rooty()
        menu.post(x + x1, y + y1 + 100)  
        self.hmenu = menu         

    def get_ini_filename(self):        
        path = self.filepath
        fn = 'stage_editor.ini'
        if path != '':            
            fn = path + os.sep + fn
        return fn      
            
    def load_ini(self):
        self.data = {}
        self.update()
        db = DB.open('cache')
        text = db.getdata('ini', 'StageEditor.ini')      
        print('StageEditor.ini', text)            
        if text == None or text.strip() == '':
           return 
        try:   
            dct = eval(text)  
        except Exception as e:         
            print('load ini Error', e)
            dct = {}
        self.data = dct
      
        lastfile = None       
        
        #self.vars['size'] = dct.get('size')
        if type(dct) == list:
            dct = {}
        self.history = dct.get('history', ['/home/athena/src/StageED/test1.stg'])
        self.lastfile = db.getdata('ini', 'StageEditor.lastfile')
        return dct
                
    def save_ini(self):
        db = DB.open('cache')
        db.setdata('ini', 'StageEditor.lastfile', self.filename)
        dct = self.get_data('ini')
        
        n = len(self.history)
        if n > 15:
            n = 15
        dct['history'] = self.history[0:n]
        dct['filename'] = self.filename
        
        db.setdata('ini', 'StageEditor.ini', str(dct))   
        

if __name__ == "__main__":       
    from StageED import MainFrame
    from aui import App
    app = App(title='APP', size=(1500,860))
    frame = MainFrame(app)
    frame.pack(fill='both', expand=True)
    app.mainloop()

    





