import numpy as np
import autograd
from abc import abstractmethod
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
from pymoo.model.problem import Problem as PymooProblem
from pymoo.model.problem import at_least2d, evaluate_in_parallel

'''
Problem definition built upon Pymoo's Problem class, added some custom features
'''

class Problem(PymooProblem):

    def __init__(self, *args, ref_point=None, **kwargs):
        super().__init__(*args, **kwargs)
        if ref_point is None:
            self.ref_point = np.zeros(self.n_obj)
        else:
            self.ref_point = ref_point

    def set_ref_point(self, ref_point):
        self.ref_point = ref_point

    def _evaluate(self, x, out, *args, **kwargs):
        out['F'] = np.column_stack([*np.atleast_2d(self.evaluate_performance(x))])
        out['G'] = self.evaluate_constraint(x)
        if out['G'] is not None:
            out['G'] = np.column_stack([*np.atleast_2d(out['G'])])

    @abstractmethod
    def evaluate_performance(self, x, **kwargs):
        pass

    def evaluate_constraint(self, x, **kwargs):
        return None
    
    def evaluate(self,
                 X,
                 *args,
                 return_values_of="auto",
                 return_as_dictionary=False,
                 **kwargs):

        """
        Evaluate the given problem.

        The function values set as defined in the function.
        The constraint values are meant to be positive if infeasible. A higher positive values means "more" infeasible".
        If they are 0 or negative, they will be considered as feasible what ever their value is.

        Parameters
        ----------

        X : np.array
            A two dimensional matrix where each row is a point to evaluate and each column a variable.

        return_as_dictionary : bool
            If this is true than only one object, a dictionary, is returned. This contains all the results
            that are defined by return_values_of. Otherwise, by default a tuple as defined is returned.

        return_values_of : list of strings
            You can provide a list of strings which defines the values that are returned. By default it is set to
            "auto" which means depending on the problem the function values or additional the constraint violation (if
            the problem has constraints) are returned. Otherwise, you can provide a list of values to be returned.

            Allowed is ["F", "CV", "G", "dF", "dG", "dCV", "feasible"] where the d stands for
            derivative and h stands for hessian matrix.


        Returns
        -------

            A dictionary, if return_as_dictionary enabled, or a list of values as defined in return_values_of.

        """

        # call the callback of the problem
        if self.callback is not None:
            self.callback(X)

        # make the array at least 2-d - even if only one row should be evaluated
        only_single_value = len(np.shape(X)) == 1
        X = np.atleast_2d(X)

        # check the dimensionality of the problem and the given input
        if X.shape[1] != self.n_var:
            raise Exception('Input dimension %s are not equal to n_var %s!' % (X.shape[1], self.n_var))

        # automatic return the function values and CV if it has constraints if not defined otherwise
        if type(return_values_of) == str and return_values_of == "auto":
            return_values_of = ["F"]
            if self.n_constr > 0:
                return_values_of.append("CV")

        # all values that are set in the evaluation function
        values_not_set = [val for val in return_values_of if val not in self.evaluation_of]

        # have a look if gradients are not set and try to use autograd and calculate grading if implemented using it
        gradients_not_set = [val for val in values_not_set if val.startswith("d")]

        # whether gradient calculation is necessary or not
        calc_gradient = (len(gradients_not_set) > 0)

        # set in the dictionary if the output should be calculated - can be used for the gradient
        out = {}
        for val in return_values_of:
            out[val] = None

        # calculate the output array - either elementwise or not. also consider the gradient
        self._evaluate(X, out, *args, calc_gradient=calc_gradient, **kwargs)
        at_least2d(out)

        calc_gradient_of = [key for key, val in out.items()
                            if "d" + key in return_values_of and
                            out.get("d" + key) is None and
                            (type(val) == autograd.numpy.numpy_boxes.ArrayBox)]

        if len(calc_gradient_of) > 0:
            deriv = self._calc_gradient(out, calc_gradient_of)
            out = {**out, **deriv}

        # convert back to conventional numpy arrays - no array box as return type
        for key in out.keys():
            if type(out[key]) == autograd.numpy.numpy_boxes.ArrayBox:
                out[key] = out[key]._value

        # if constraint violation should be returned as well
        if self.n_constr == 0:
            CV = np.zeros([X.shape[0], 1])
        else:
            CV = Problem.calc_constraint_violation(out["G"])

        if "CV" in return_values_of:
            out["CV"] = CV

        # if an additional boolean flag for feasibility should be returned
        if "feasible" in return_values_of:
            out["feasible"] = (CV <= 0)

        # if asked for a value but not set in the evaluation set to None
        for val in return_values_of:
            if val not in out:
                out[val] = None

        # remove the first dimension of the output - in case input was a 1d- vector
        if only_single_value:
            for key in out.keys():
                if out[key] is not None:
                    out[key] = out[key][0, :]

        if return_as_dictionary:
            return out
        else:
            # if just a single value do not return a tuple
            if len(return_values_of) == 1:
                return out[return_values_of[0]]
            else:
                return tuple([out[val] for val in return_values_of])

    def __str__(self):
        return '========== Problem Definition ==========\n' + super().__str__()