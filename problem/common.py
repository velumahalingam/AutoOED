import importlib
import os
import glob
import yaml
import numpy as np
from pymoo.factory import get_from_list
from problem import Problem, GeneratedProblem
from algorithm.external import lhs


def get_subclasses(cls):
    '''
    Get all leaf subclasses of a given class
    '''
    subclasses = []
    for subclass in cls.__subclasses__():
        subsubclasses = get_subclasses(subclass)
        if subsubclasses == []:
            subclasses.append(subclass)
        else:
            subclasses.extend(subsubclasses)
    return subclasses


def find_predefined_python_problems():
    '''
    Find all predefined problems created by python files
    Output:
        problems: a dict of {name: python_class} of all predefined python problems
    '''
    # find modules of predefined problems
    modules = glob.glob(os.path.join(os.path.dirname(__file__), "predefined/*.py"))
    modules = ['predefined.' + os.path.basename(f)[:-3] for f in modules if os.path.isfile(f) and not f.endswith('__init__.py')]

    # check if duplicate exists
    assert len(np.unique(modules)) == len(modules), 'name conflict exists in defined python problems'

    # build problem dict
    problems = {}
    for module in modules:
        for key, val in importlib.import_module(f'problem.{module}').__dict__.items():
            key = key.lower()
            if not key.startswith('_') and val in get_subclasses(Problem):
                problems[key] = val
    return problems


def find_custom_python_problems():
    '''
    Find all custom problems created by python files
    Output:
        problems: a dict of {name: python_class} of all custom python problems
    '''
    # find modules of custom problems
    modules = glob.glob(os.path.join(os.path.dirname(__file__), "custom/python/*.py"))
    modules = ['custom.python.' + os.path.basename(f)[:-3] for f in modules if os.path.isfile(f) and not f.endswith('__init__.py')]

    # check if duplicate exists
    assert len(np.unique(modules)) == len(modules), 'name conflict exists in defined python problems'

    # build problem dict
    problems = {}
    for module in modules:
        for key, val in importlib.import_module(f'problem.{module}').__dict__.items():
            key = key.lower()
            if not key.startswith('_') and not key.startswith('exampleproblem') and val in get_subclasses(Problem):
                problems[key] = val
    return problems


def find_python_problems():
    '''
    Find all problems created by python files
    Output:
        problems: a dict of {name: python_class} of all python problems
    '''
    problems = {}
    problems.update(find_predefined_python_problems())
    problems.update(find_custom_python_problems())
    return problems


def get_yaml_problem_dir():
    '''
    Return directory of yaml problems
    '''
    return os.path.join(os.path.dirname(__file__), 'custom', 'yaml')


def find_yaml_problems():
    '''
    Find all problems created by yaml files
    Output:
        problems: a dict of {name: yaml_path} of all yaml problems
    '''
    configs = {}
    config_dir = get_yaml_problem_dir()
    for name in os.listdir(config_dir):
        if name.endswith('.yml'):
            configs[name[:-4]] = os.path.join(config_dir, name)
    return configs


def save_yaml_problem(config):
    '''
    Save problem config as yaml file
    '''
    name = config['name']
    config_path = os.path.join(get_yaml_problem_dir(), f'{name}.yml')
    try:
        with open(config_path, 'w') as fp:
            yaml.dump(config, fp, default_flow_style=False, sort_keys=False)
    except:
        raise Exception('not a valid problem config')
    

def load_yaml_problem(name):
    '''
    Load problem config from yaml file
    '''
    config_path = os.path.join(get_yaml_problem_dir(), f'{name}.yml')
    try:
        with open(config_path, 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
    except:
        raise Exception('not a valid config file')
    return config


def remove_yaml_problem(name):
    '''
    Remove a problem from saved problems
    '''
    config_path = os.path.join(get_yaml_problem_dir(), f'{name}.yml')
    try:
        os.remove(config_path)
    except:
        raise Exception("problem doesn't exist")


def find_all_problems():
    '''
    Find all problems created by python and yaml files, also check for name conflict
    '''
    python_problems = find_python_problems()
    yaml_problems = find_yaml_problems()
    if len(np.unique(list(python_problems.keys()) + list(yaml_problems.keys()))) < len(python_problems) + len(yaml_problems):
        raise Exception('name conflict exists between defined python problems and yaml problems')
    else:
        return python_problems, yaml_problems


def get_predefined_python_problem_list():
    '''
    Get names of predefined python problems
    '''
    return list(find_predefined_python_problems().keys())


def get_custom_python_problem_list():
    '''
    Get names of custom python problems
    '''
    return list(find_custom_python_problems().keys())


def get_python_problem_list():
    '''
    Get names of all python problems
    '''
    return list(find_python_problems().keys())


def get_yaml_problem_list():
    '''
    Get names of (generated) yaml problems
    '''
    return list(find_yaml_problems().keys())


def get_problem_list():
    '''
    Get names of available problems
    '''
    python_problems, yaml_problems = find_all_problems()
    return list(python_problems.keys()) + list(yaml_problems.keys())


def get_problem_config(name):
    '''
    Get config dict of problem
    '''
    # check for custom python problems
    custom_problems = find_custom_python_problems()
    if name in custom_problems:
        return custom_problems[name].get_config()

    # check for custom yaml problems
    yaml_problems = find_yaml_problems()
    if name in yaml_problems:
        config_path = yaml_problems[name]
        try:
            with open(config_path, 'r') as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
        except:
            raise Exception('not a valid config file')
        if 'performance_eval' in config: config.pop('performance_eval')
        if 'constraint_eval' in config: config.pop('constraint_eval')
        return Problem.process_config(config)

    # check for predefined python problems
    predefined_problems = find_predefined_python_problems()
    if name in predefined_problems:
        return predefined_problems[name].get_config()
        
    raise Exception(f'problem {name} is not defined')


def generate_random_initial_samples(problem, n_sample):
    '''
    Generate feasible random initial samples
    Input:
        problem: the optimization problem
        n_sample: number of initial samples
    Output:
        X: initial samples (design parameters)
    '''
    X_feasible = np.zeros((0, problem.n_var))

    # NOTE: when it's really hard to get feasible samples, the program hangs here
    while len(X_feasible) < n_sample:
        X = lhs(problem.n_var, n_sample) # TODO: support other types of initialization
        X = problem.xl + X * (problem.xu - problem.xl)
        feasible = problem.evaluate_feasible(X) # NOTE: assume constraint evaluation is fast
        X_feasible = np.vstack([X_feasible, X[feasible]])

    X = X_feasible[:n_sample]
    return X


def load_provided_initial_samples(problem, init_sample_path):
    '''
    Load provided initial samples from file
    Input:
        problem: the optimization problem
        init_sample_path: path of provided initial samples
    Output:
        X, Y: initial samples (design parameters, performance values)
    '''
    # use problem default path if not specified
    if init_sample_path is None:
        init_sample_path = problem.get_config()['init_sample_path']
    assert init_sample_path is not None, 'path of initial samples is not provided'

    if isinstance(init_sample_path, list) and len(init_sample_path) == 2:
        X_path, Y_path = init_sample_path[0], init_sample_path[1] # initial X and initial Y are both provided
    elif isinstance(init_sample_path, str):
        X_path, Y_path = init_sample_path, None # only initial X is provided, initial Y needs to be evaluated
    else:
        raise Exception('path of initial samples must be specified as 1) a list [x_path, y_path]; or 2) a string x_path')

    def load_from_file(path):
        # NOTE: currently only support npy and csv format for initial sample path
        try:
            if path.endswith('.npy'):
                return np.load(path)
            elif path.endswith('.csv'):
                return np.genfromtxt(path, delimiter=',')
            else:
                raise NotImplementedError
        except:
            raise Exception(f'failed to load initial samples from path {path}')

    X = load_from_file(X_path)
    Y = load_from_file(Y_path) if Y_path is not None else None
    return X, Y


def build_problem(config, get_pfront=False):
    '''
    Build optimization problem
    Input:
        config: problem configuration
        get_pfront: if return predefined true Pareto front of the problem
    Output:
        problem: the optimization problem
        pareto_front: the true Pareto front of the problem (if defined, otherwise None)
    '''
    config = config.copy()
    problem = None
    
    # build problem
    name = config.pop('name')
    python_problems, yaml_problems = find_all_problems()
    if name in python_problems:
        problem = python_problems[name](**config)
    elif name in yaml_problems:
        with open(yaml_problems[name], 'r') as fp:
            problem_cfg = yaml.load(fp, Loader=yaml.FullLoader)
        problem = GeneratedProblem(problem_cfg, **config)
    else:
        raise Exception(f'Problem {name} not found')

    # get true pareto front
    if get_pfront:
        try:
            pareto_front = problem.pareto_front()
        except:
            pareto_front = None
        return problem, pareto_front
    else:
        return problem


def get_initial_samples(config, problem):
    '''
    Getting initial samples of the problem
    Input:
        config: problem configuration
        problem: the optimization problem
    Output:
        X_init_evaluated:
        X_init_unevaluated:
        Y_init_evaluated:
    '''
    X_init_evaluated, X_init_unevaluated, Y_init_evaluated = None, None, None

    random_init = config['n_init_sample'] > 0
    provided_init = config['init_sample_path'] is not None or problem.get_config()['init_sample_path'] is not None
    assert random_init or provided_init, 'neither number of random initial samples nor path of provided initial samples is provided'
    
    if random_init:
        X_init_unevaluated = generate_random_initial_samples(problem, config['n_init_sample'])

    if provided_init:
        X_init_provided, Y_init_provided = load_provided_initial_samples(problem, config['init_sample_path'])
        if Y_init_provided is None:
            if random_init:
                X_init_unevaluated = np.vstack([X_init_unevaluated, X_init_provided])
            else:
                X_init_unevaluated = X_init_provided
        else:
            X_init_evaluated = X_init_provided
            Y_init_evaluated = Y_init_provided
    
    return X_init_evaluated, X_init_unevaluated, Y_init_evaluated