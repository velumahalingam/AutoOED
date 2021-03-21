from system.gui.widgets.factory import create_widget


class RemoveTaskView:

    def __init__(self, root_view):
        self.window = create_widget('toplevel', master=root_view.root, title='Remove Task')

        self.widget = {}
        self.widget['task_name'] = create_widget('labeled_combobox', master=self.window, row=0, column=0, columnspan=2, 
            text='Task name', required=True)
        self.widget['remove'] = create_widget('button', master=self.window, row=1, column=0, text='Remove')
        self.widget['cancel'] = create_widget('button', master=self.window, row=1, column=1, text='Cancel')