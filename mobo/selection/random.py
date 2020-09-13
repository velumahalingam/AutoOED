import numpy as np
from .base import Selection


class Random(Selection):
    '''
    Random selection
    '''
    def select(self, solution, surrogate_model, transformation, curr_pset, curr_pfront):
        X = solution['x']
        X = transformation.undo(x=X)
        random_indices = np.random.choice(len(X), size=self.batch_size, replace=False)
        return X[random_indices], None