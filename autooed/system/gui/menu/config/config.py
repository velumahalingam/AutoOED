import os
import tkinter as tk
from multiprocessing import cpu_count

from autooed.problem import get_problem_config, get_problem_list
from autooed.mobo import get_algorithm_list
from autooed.mobo.hyperparams import get_hp_class_names, get_hp_class_by_name, get_hp_name_by_class

from autooed.system.config import config_map, load_config
from autooed.system.gui.widgets.utils.grid import grid_configure
from autooed.system.gui.widgets.factory import create_widget
from autooed.system.gui.menu.config.ref_point import RefPointController
from autooed.system.gui.menu.config.hyperparam import HyperparamController


class MenuConfigView:

    def __init__(self, root_view, first_time):
        self.root_view = root_view
        self.first_time = first_time

        title = 'Create Configurations' if self.first_time else 'Change Configurations'
        self.window = create_widget('toplevel', master=self.root_view.root, title=title)

        self.widget = {}

        # parameter section
        frame_param = tk.Frame(master=self.window)
        frame_param.grid(row=0, column=0)
        grid_configure(frame_param, 2, 0)

        # problem subsection
        frame_problem = create_widget('labeled_frame', master=frame_param, row=0, column=0, text='Problem')
        grid_configure(frame_problem, 0, 0)

        self.widget['problem_name'] = create_widget('labeled_combobox', 
            master=frame_problem, row=0, column=0, text=config_map['problem']['name'], values=get_problem_list(), width=15, required=True)
        self.widget['set_ref_point'] = create_widget('button',
            master=frame_problem, row=1, column=0, text='Set Reference Point', sticky=None)
        self.widget['set_ref_point'].disable()

        # algorithm subsection
        frame_algorithm = create_widget('labeled_frame', master=frame_param, row=1, column=0, text='Algorithm')
        grid_configure(frame_algorithm, 0, 0)
        self.widget['algo_name'] = create_widget('labeled_combobox', 
            master=frame_algorithm, row=0, column=0, text=config_map['algorithm']['name'], values=get_algorithm_list(), required=True)
        self.widget['n_process'] = create_widget('labeled_entry', 
            master=frame_algorithm, row=1, column=0, text=config_map['algorithm']['n_process'], class_type='int', default=cpu_count(),
            valid_check=lambda x: x > 0, error_msg='number of processes to use must be positive')
        self.widget['async'] = create_widget('labeled_combobox',
            master=frame_algorithm, row=2, column=0, text=config_map['algorithm']['async'], default='None',
            values=get_hp_class_names('async'))
        self.widget['set_advanced'] = create_widget('button', master=frame_algorithm, row=3, column=0, text='Advanced Settings', sticky=None)
        
        # initialization subsection
        if self.first_time:
            frame_init = create_widget('labeled_frame', master=frame_param, row=2, column=0, text='Initialization')
            grid_configure(frame_init, 1, 0)

            self.widget['init_type'] = create_widget('radiobutton',
                master=frame_init, row=0, column=0, text_list=['Random', 'Provided'], default='Random')

            frame_random_init = create_widget('frame', master=frame_init, row=1, column=0, padx=0, pady=0)
            frame_provided_init = create_widget('frame', master=frame_init, row=1, column=0, padx=0, pady=0)

            self.widget['n_init'] = create_widget('labeled_entry', 
                master=frame_random_init, row=0, column=0, text=config_map['experiment']['n_random_sample'], class_type='int', required=True,
                valid_check=lambda x: x > 0, error_msg='number of random initial samples must be positive')

            self.widget['set_x_init'], self.widget['disp_x_init'] = create_widget('labeled_button_entry',
                master=frame_provided_init, row=0, column=0, label_text='Path of initial design variables', button_text='Browse', width=30, required=True,
                valid_check=lambda x: os.path.exists(x), error_msg='file of initial design variables does not exist')
            self.widget['set_y_init'], self.widget['disp_y_init'] = create_widget('labeled_button_entry',
                master=frame_provided_init, row=1, column=0, label_text='Path of initial performance values', button_text='Browse', width=30,
                valid_check=lambda x: os.path.exists(x), error_msg='file of initial performance values does not exist')

            def set_random_init():
                frame_provided_init.grid_remove()
                frame_random_init.grid()

            def set_provided_init():
                frame_random_init.grid_remove()
                frame_provided_init.grid()

            for text, button in self.widget['init_type'].widget.items():
                if text == 'Random':
                    button.configure(command=set_random_init)
                elif text == 'Provided':
                    button.configure(command=set_provided_init)
                else:
                    raise NotImplementedError

            set_random_init()

        # evaluation subsection
        frame_experiment = create_widget('labeled_frame', master=frame_param, row=3 if self.first_time else 2, column=0, text='Experiment')
        grid_configure(frame_experiment, 0, 0)
        self.widget['n_worker'] = create_widget('labeled_entry',
            master=frame_experiment, row=0, column=0, text=config_map['experiment']['n_worker'], class_type='int', default=1,
            valid_check=lambda x: x > 0, error_msg='max number of evaluation workers must be positive')

        # action section
        frame_action = tk.Frame(master=self.window)
        frame_action.grid(row=1, column=0, columnspan=3)
        self.widget['save'] = create_widget('button', master=frame_action, row=0, column=0, text='Save')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')

        self.cfg_widget = {
            'problem': {
                'name': self.widget['problem_name'],
            },
            'algorithm': {
                'name': self.widget['algo_name'],
                'n_process': self.widget['n_process'],
                'async': self.widget['async'],
            },
            'experiment': {
                'n_worker': self.widget['n_worker'],
            }
        }


class MenuConfigController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.problem_cfg = {} # problem config
        self.exp_cfg = {} # experiment config (for reference point)
        self.algo_cfg = {} # advanced algorithm config

        self.first_time = True
        self.algo_selected = None

        self.view = None

    def get_config(self):
        return self.root_controller.get_config()

    def set_config(self, *args, **kwargs):
        return self.root_controller.set_config(*args, **kwargs)

    def load_config_from_file(self):
        '''
        Load experiment configurations from file
        '''
        filename = tk.filedialog.askopenfilename(parent=self.root_view.root)
        if not isinstance(filename, str) or filename == '': return

        try:
            config = load_config(filename)
        except:
            tk.messagebox.showinfo('Error', 'Invalid yaml file', parent=self.root_view.root)
            return
            
        self.set_config(config)

    def build_config_window(self):
        '''
        Build configuration window (for create/change)
        '''
        self.view = MenuConfigView(self.root_view, self.first_time)

        self.view.widget['problem_name'].widget.bind('<<ComboboxSelected>>', self.select_problem)
        self.view.widget['set_ref_point'].configure(command=self.set_ref_point)

        self.view.widget['algo_name'].widget.bind('<<ComboboxSelected>>', self.select_algorithm)
        self.view.widget['set_advanced'].configure(command=self.set_algo_advanced)

        if self.first_time:
            self.view.widget['set_x_init'].configure(command=self.set_x_init)
            self.view.widget['set_y_init'].configure(command=self.set_y_init)

        self.view.widget['save'].configure(command=self.save_config)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

        # load current config values to entry if not first time setting config
        if not self.first_time:
            self.load_curr_config()

        # disable widgets
        if self.first_time:
            self.view.widget['set_advanced'].disable()
        else:
            self.view.widget['problem_name'].disable()

    def create_config(self):
        '''
        Create experiment configurations
        '''
        self.first_time = True
        self.build_config_window()

    def change_config(self):
        '''
        Change experiment configurations
        '''
        self.first_time = False
        self.build_config_window()

    def select_problem(self, event):
        '''
        Select problem to configure
        '''
        # find problem static config by name selected
        name = event.widget.get()
        config = get_problem_config(name)

        self.problem_cfg.clear()
        self.problem_cfg.update(config)

        if config['n_obj'] == 1:
            self.view.widget['set_ref_point'].disable()
        else:
            self.view.widget['set_ref_point'].enable()

    def set_ref_point(self):
        '''
        Set reference point
        '''
        RefPointController(self)
        
    def set_x_init(self):
        '''
        Set path of provided initial design variables
        '''
        filename = tk.filedialog.askopenfilename(parent=self.view.window)
        if not isinstance(filename, str) or filename == '': return
        self.view.widget['disp_x_init'].set(filename)

    def set_y_init(self):
        '''
        Set path of provided initial performance values
        '''
        filename = tk.filedialog.askopenfilename(parent=self.view.window)
        if not isinstance(filename, str) or filename == '': return
        self.view.widget['disp_y_init'].set(filename)

    def select_algorithm(self, event):
        '''
        Select algorithm
        '''
        self.algo_selected = event.widget.get()
        self.view.widget['set_advanced'].enable()

    def set_algo_advanced(self):
        '''
        Set advanced settings of the algorithm
        '''
        HyperparamController(self)

    def load_curr_config(self):
        '''
        Set values of widgets as current configuration values
        '''
        curr_config = self.get_config()
        for cfg_type, val_map in self.view.cfg_widget.items():
            for cfg_name, widget in val_map.items():
                widget.enable()
                if cfg_name == 'async':
                    widget.set(get_hp_name_by_class('async', curr_config[cfg_type][cfg_name]['name'])) # TODO: support other hyperparams
                else:
                    widget.set(curr_config[cfg_type][cfg_name])
                widget.select()
        self.problem_cfg.update(curr_config['problem'])
        self.algo_cfg.update(curr_config['algorithm'])
        self.algo_cfg.pop('name')
        self.algo_cfg.pop('n_process') # TODO: check
        self.view.widget['set_advanced'].enable()

    def save_config(self):
        '''
        Save specified configuration values
        '''
        config = self.get_config()
        if config is None:
            config = {
                'problem': {},
                'experiment': {},
                'algorithm': {},
            }

        # specifically deal with initial samples (TODO: clean)
        if self.first_time:
            init_type = self.view.widget['init_type'].get()

            if init_type == 'Random':
                try:
                    config['experiment']['n_random_sample'] = self.view.widget['n_init'].get()
                except Exception as e:
                    tk.messagebox.showinfo('Error', e, parent=self.view.window)
                    return

            elif init_type == 'Provided':
                try:
                    x_init_path = self.view.widget['disp_x_init'].get()
                except Exception as e:
                    tk.messagebox.showinfo('Error', e, parent=self.view.window)
                    return
                try:
                    y_init_path = self.view.widget['disp_y_init'].get()
                except Exception as e:
                    tk.messagebox.showinfo('Error', e, parent=self.view.window)
                    return

                assert x_init_path is not None, 'Path of initial design variables must be provided'
                if y_init_path is None: # only path of initial X is provided
                    config['experiment']['init_sample_path'] = x_init_path
                else: # both path of initial X and initial Y are provided
                    config['experiment']['init_sample_path'] = [x_init_path, y_init_path]

            else:
                raise Exception()

        # set config values from widgets
        for cfg_type, val_map in self.view.cfg_widget.items():
            for cfg_name, widget in val_map.items():
                try:
                    if cfg_name == 'async':
                        config[cfg_type][cfg_name] = {}
                        config[cfg_type][cfg_name]['name'] = get_hp_class_by_name('async', widget.get())
                    else:
                        config[cfg_type][cfg_name] = widget.get()
                except Exception as e:
                    tk.messagebox.showinfo('Error', e, parent=self.view.window)
                    return

        config['experiment'].update(self.exp_cfg)
        config['algorithm'].update(self.algo_cfg)

        success = self.set_config(config, self.view.window)
        if success:
            self.view.window.destroy()