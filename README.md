# Crockpot control software

## Screenshots of the web interface

![Curve fitting](https://raw.github.com/petrklus/crockpot/master/images/screen_1.png)

## Requirements/dependencies

The requirements.txt is only relevant to the webservice. Curve fitting and data
exploration done in data_fitting.py requires additional packages - numpy, scipy and matplotlib

## First step - line fitting 
... to determine on-board resistor value

![Curve fitting](https://raw.github.com/petrklus/crockpot/master/images/figure_1.png)

## arduino code compilation

- command line ready
- enter directory crockpot_work
- issue: ```make; make upload```
- requires arduino package to be installed (tested on Rasbperry PI)
