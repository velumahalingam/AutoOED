import tkinter as tk
from system.gui.widgets.factory import create_widget


class ScientistLoginView:

    def __init__(self, root):
        self.root = root

        frame_login = create_widget('frame', master=self.root, row=0, column=0)
        create_widget('logo', master=frame_login, row=0, column=0)

        self.widget = {}
        self.widget['ip'] = create_widget('labeled_entry', master=frame_login, row=1, column=0, width=20,
            text='Server IP Address', class_type='string', required=True, required_mark=False)
        self.widget['user'] = create_widget('labeled_entry', master=frame_login, row=2, column=0, width=20,
            text='Username', class_type='string', required=True, required_mark=False)
        self.widget['passwd'] = create_widget('labeled_entry', master=frame_login, row=3, column=0, width=20,
            text='Password', class_type='string', required=False)
        self.widget['task'] = create_widget('labeled_entry', master=frame_login, row=4, column=0, width=20,
            text='Task Name', class_type='string', required=True, required_mark=False)
        self.widget['login'] = create_widget('button', master=frame_login, row=5, column=0, text='Log in')
