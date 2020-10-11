import tkinter as tk
from .view import StopEvalView


class StopEvalController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.view = StopEvalView(self.root_view)

        self.view.widget['disp_n_row'].config(
            default=1, 
            valid_check=lambda x: x > 0, 
            error_msg='number of rows must be positive',
        )
        self.view.widget['disp_n_row'].set(1)
        self.view.widget['set_n_row'].configure(self.update_table)

        max_n_rows = self.root_controller.table.n_rows
        self.view.widget['rowid_excel'].config(
            valid_check=[lambda x: x > 0 and x <= max_n_rows],
        )

        self.view.widget['stop'].configure(command=self.stop_eval_worker)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def update_table(self):
        '''
        Update excel table of rowids to be stopped
        '''
        n_row = self.view.widget['disp_n_row'].get()
        self.view.widget['rowid_excel'].update_n_row(n_row)

    def stop_eval_worker(self):
        '''
        Stop evaluation workers
        '''
        try:
            rowids = self.view.widget['rowid_excel'].get_column(0)
        except:
            tk.messagebox.showinfo('Error', 'Invalid row numbers', parent=self.view.window)
            return

        self.view.window.destroy()
        
        worker_agent = self.root_controller.worker_agent

        for rowid in rowids:
            worker_agent.stop_eval_worker(rowid)