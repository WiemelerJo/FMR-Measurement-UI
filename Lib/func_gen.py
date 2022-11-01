# Skript for generating the Functions as a String
# Idea is, these Classes should create and return a string which in the end via excec(....., globals()) can be turned
# into a python function and in the end into a model for fitting using lmfit
import math as m
from asteval import asteval
from typing import List

class Fit_Models():
    # Todo: Make MODELS as Object; Args, Bounds, Stepsize... as property
    def __init__(self):
        self._load_models()

    def _load_models(self):
        # Loads a .txt file where the models are stored
        MODELS = dict()

        with open("Models.txt", 'r') as file:
            model = dict()
            #i = 0
            for line in file:
                if line[0] == "#": # Name
                    name = line[1:-1].replace(" ","-")
                    model["name"] = name
                    #print(name)
                elif line[:4] == "Args": # Arguments
                    args = line[6:-1]
                    args_fmt = args.replace(",", r"{0}") + r"{0}"
                    args_fmt = ", " + args_fmt.replace(" ", ", ")
                    model["args"] = args.split(",")
                    model["args_fmt"] = args_fmt
                    #print(args)
                elif line[:6] == "Bounds":
                    bounds_raw = line[8:-1].split(", ")
                    bounds = []
                    for tpl in bounds_raw:
                        big = "999999"
                        tpl = eval(tpl.replace('Nan', big).replace('nan', big).replace('NaN', big).replace('NAN', big))
                        bounds.append(tpl)
                    model["bounds"] = bounds
                elif line[:8] == "StepSize":
                    step_raw = line[9:-1].split(", ")
                    step = []
                    for stp in step_raw:
                        step.append(float(stp))
                    model["stepSize"] = step
                elif line[:8] == "InitVals":
                    init_raw = line[9:-1].split(", ")
                    init = []
                    for nt in init_raw:
                        init.append(float(nt))
                    model["initVals"] = init
                elif line[:4] == "Func": # Function
                    func = line[10:].replace("m.", "np.")
                    arg = args.split(", ")
                    arg_fmt = args_fmt.split(", ")
                    if arg_fmt[0] == '': # Remove empty entry
                        del arg_fmt[0]
                    func_fmt = func
                    for index, param in enumerate(arg):
                        func_fmt = func_fmt.replace(param, arg_fmt[index])
                    model["func"] = func
                    model["func_fmt"] = func_fmt
                    #print(func)
                elif line[0] == "/":
                    #print(name)
                    MODELS[name] = model
                    model = dict()
                    #i = 0
                #i += 1

        self.MODELS = MODELS

    def getModelFunc(self, models: List[str], spectra: int) -> List[str]:
        # From models list extract model names plus index number , eg. "Lorentz 1" + "Dyson 2" ....
        # Then get their func_fmt and format {} to index number.
        # Finally sum up all func_fmt and wrap it in a python function called  modelFitFunc_{}.format(self.i)
        # exec str to create global function
        # Return func name/reference

        func_args = str()  # Set empty str
        func_body = str()  # Set empty str

        for model in models:
            model = model.split(" ") # From "Lorentz 1" get ["Lorentz", "1"]
            name = model[0]
            index = model[1]

            func = self.MODELS[name]
            func_args += func['args_fmt'].format(index)
            func_body += '+' + func['func_fmt'].format(index)

        func = "def modelFitFunc_{0}(B{1}):\n\treturn({2})".format(spectra, func_args, func_body)
        return func, "modelFitFunc_{}".format(spectra), func_args


if __name__ == '__main__':
    Fit_Models()
