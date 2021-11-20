import numpy as np
import tkinter as tk

from autooed.system.gui.widgets.factory import create_widget
from autooed.system.gui.widgets.excel import Excel


class EnterPerformanceView:

    def __init__(self, root_view, obj_name):
        self.root_view = root_view
        n_obj = len(obj_name)

        self.window = create_widget('toplevel', master=self.root_view.root, title='Enter Performance')

        self.widget = {}

        frame_n_row = create_widget('frame', master=self.window, row=0, column=0, sticky=None, pady=0)
        self.widget['disp_n_row'] = create_widget('labeled_entry',
            master=frame_n_row, row=0, column=0, text='Number of rows', class_type='int')
        self.widget['set_n_row'] = create_widget('button', master=frame_n_row, row=0, column=1, text='Update')

        self.widget['performance_excel'] = Excel(master=self.window, rows=1, columns=n_obj + 1, width=10, 
            title=['Row number'] + list(obj_name), dtype=[int] + [float] * n_obj, default=None, required=[True] * (n_obj + 1), required_mark=False)
        self.widget['performance_excel'].grid(row=1, column=0)

        frame_action = create_widget('frame', master=self.window, row=2, column=0, sticky=None, pady=0)
        self.widget['save'] = create_widget('button', master=frame_action, row=0, column=0, text='Save')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')


class EnterPerformanceController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        problem_cfg = self.root_controller.get_problem_cfg()
        n_obj, obj_name = problem_cfg['n_obj'], problem_cfg['obj_name']

        self.view = EnterPerformanceView(self.root_view, obj_name)

        self.view.widget['disp_n_row'].config(
            default=1, 
            valid_check=lambda x: x > 0,
            error_msg='number of rows must be positive',
        )
        self.view.widget['disp_n_row'].set(1)
        self.view.widget['set_n_row'].configure(command=self.update_table)

        table = self.root_controller.table
        self.view.widget['performance_excel'].config(
            valid_check=[lambda x: x > 0 and x <= table.n_rows] + [lambda x: True] * n_obj,
        )

        self.view.widget['save'].configure(command=self.add_performance)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def update_table(self):
        '''
        Update excel table of design variables to be added
        '''
        n_row = self.view.widget['disp_n_row'].get()
        self.view.widget['performance_excel'].update_n_row(n_row)

    def add_performance(self):
        '''
        Add performance values
        '''
        try:
            rowids = self.view.widget['performance_excel'].get_column(0)
            if len(np.unique(rowids)) != len(rowids):
                raise Exception('Duplicate row numbers')
        except:
            tk.messagebox.showinfo('Error', 'Invalid row numbers', parent=self.view.window)
            return

        problem_cfg = self.root_controller.get_problem_cfg()
        obj_name_list = problem_cfg['obj_name']
        table = self.root_controller.table
        agent = self.root_controller.agent

        # check for overwriting
        overwrite = False
        for rowid in rowids:
            for obj_name in obj_name_list:
                if table.get(rowid - 1, obj_name) != 'N/A':
                    overwrite = True
        if overwrite and tk.messagebox.askquestion('Overwrite Data', 'Are you sure to overwrite evaluated data?', parent=self.view.window) == 'no': return

        try:
            Y = self.view.widget['performance_excel'].get_grid(column_start=1)
        except:
            tk.messagebox.showinfo('Error', 'Invalid performance values', parent=self.view.window)
            return
        
        self.view.window.destroy()

        # update database
        agent.update_evaluation(Y, rowids)
