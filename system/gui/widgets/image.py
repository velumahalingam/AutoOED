import tkinter as tk
from PIL import ImageTk, Image
from system.gui.utils.grid import grid_configure


class ImageFrame(tk.Frame):
    def __init__(self, master, img_path, *pargs):
        tk.Frame.__init__(self, master, *pargs)
        self.image = Image.open(img_path)
        width, height = self.image.size
        self.ratio = width / height
        self.img_copy = self.image.copy()
        self.background_image = ImageTk.PhotoImage(self.image)
        self.background = tk.Label(self, image=self.background_image)
        self.background.grid(row=0, column=0, sticky='NSEW')
        self.background.bind('<Configure>', self._resize_image)
        grid_configure(self, [0], [0])

    def _resize_image(self, event):
        new_width = event.width
        new_height = event.height
        new_ratio = new_width / new_height
        if new_ratio > self.ratio:
            new_width = int(self.ratio * new_height)
        else:
            new_height = int(new_width / self.ratio)
        self.image = self.img_copy.resize((new_width, new_height))
        self.background_image = ImageTk.PhotoImage(self.image)
        self.background.configure(image=self.background_image)