from datetime import datetime
import tkinter as tk
from .view import PanelLogView


class PanelLogController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.view = PanelLogView(self.root_view)

        self.view.widget['clear'].configure(command=self.clear_log)
        self.view.widget['clear'].disable()

    def log(self, string):
        '''
        Log texts to ScrolledText widget
        '''
        if string == []: return
        self.view.widget['log'].enable()
        time = datetime.now().strftime('\n%Y-%m-%d %H:%M:%S\n')
        if isinstance(string, str):
            log_str = string
        elif isinstance(string, list):
            log_str = '\n'.join(string)
        else:
            raise NotImplementedError
        self.view.widget['log'].widget.insert(tk.INSERT, time + log_str + '\n')
        self.view.widget['log'].disable()
        self.view.widget['log'].widget.yview_pickplace('end')

    def clear_log(self):
        '''
        Clear texts in GUI log
        '''
        self.view.widget['log'].enable()
        self.view.widget['log'].widget.delete('1.0', tk.END)
        self.view.widget['log'].disable()