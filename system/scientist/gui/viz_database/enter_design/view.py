import tkinter as tk
from system.gui.widgets.factory import create_widget
from system.gui.widgets.excel import Excel


class EnterDesignView:

    def __init__(self, root_view, n_var):
        self.root_view = root_view

        self.window = tk.Toplevel(master=self.root_view.frame)
        self.window.title('Enter Design Variables')
        self.window.resizable(False, False)

        self.widget = {}

        frame_n_row = create_widget('frame', master=self.window, row=0, column=0, sticky=None, pady=0)
        self.widget['disp_n_row'] = create_widget('labeled_entry',
            master=frame_n_row, row=0, column=0, text='Number of rows', class_type='int')
        self.widget['set_n_row'] = create_widget('button', master=frame_n_row, row=0, column=1, text='Update')

        self.widget['design_excel'] = Excel(master=self.window, rows=1, columns=n_var, width=10, 
            title=[f'x{i + 1}' for i in range(n_var)], dtype=[float] * n_var, required=[True] * n_var)
        self.widget['design_excel'].grid(row=1, column=0)

        self.widget['eval_var'] = create_widget('checkbutton', master=self.window, row=2, column=0, text='Automatically evaluate')

        frame_action = create_widget('frame', master=self.window, row=3, column=0, sticky=None, pady=0)
        self.widget['save'] = create_widget('button', master=frame_action, row=0, column=0, text='Save')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')