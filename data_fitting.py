import pickle
import numpy as np

#  load data
with open("logs_examples/log_20150418-16_03_54.pckl") as fp:
    values = pickle.load(fp)

#  build value relations
res_to_tmp = map(lambda val: [int(val["resistor_val"]), int(val["digi_temp"])], values)

# additional values collected later, cold environment, manual tweak to give them more weight (the coefficient)
res_to_tmp += [[43, 20], [44,21], [550, 100], [600, 110]] * 50
res_to_tmp = sorted(res_to_tmp)

# fit curve and create conversion function
from scipy import stats
slope, intercept, r_value, p_value, std_err = stats.linregress(np.array(res_to_tmp))

convert_from_tmp = lambda temperature: (temperature-intercept)/slope
convert_from_res = lambda res_value: res_value*slope + intercept
#  Hmm, linear may not cut it.. let's try something more complex
from scipy.optimize import curve_fit
def func(x, a, b, c, d):
    return a*x**3 + b*x**2 +c*x + d

x, y = np.array(res_to_tmp)[:,0], np.array(res_to_tmp)[:,1]
popt, pcov = curve_fit(func, x, y)
x_rng = np.arange(0, 650) # resistor values..


# visualise result

import matplotlib.pyplot as plt
line_data,          = plt.plot(x, y)
line_fitted_linear, = plt.plot(x_rng, map(convert_from_res, x_rng))
line_fitted_exp,    = plt.plot(x_rng, func(x_rng, *popt), label="Fitted Curve")
plt.xlabel("resistor RAW reading")
plt.ylabel("temperature C")
plt.legend([line_data, line_fitted_linear, line_fitted_exp], ["collected data", "linear fit", "exp fit"], loc=2)




plt.show()
