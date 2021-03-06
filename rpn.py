#! /usr/bin/env python3
# vim:fileencoding=utf-8

"""
Type in your equation using Reverse Polish Notation.  Values (numbers) are
added to the stack. Operators act upon the values in the stack.
Values/operators can be input individually (pressing ENTER after every
number/operator) or by separating the tokens with spaces.  Values get "pulled"
from the stack when operated upon.

For example: the equation "4+22/7=" can be keyed in as "4 22 7 / +" this will
divide 22 by 7 then add 4 to the result. Unary operators work on what is in the
x register. Binary operators use the x & y registers.

A complete list of operators can be displayed by typing in: "help op"
"""

version = "RPN Calculator version 1.09"

# Notes:
# ------
# All numbers are stored in floating point notation and are accurate
# to within about 15 decimal places.  Use the 'show' operator to
# display the internal value.
# -
# The '%' & '%c' operators do NOT consume the y value.  This is so
# it can be used in subsequent computations.  Also, because that's
# how the HP-15c does it.
# -
# The trig functions assume the angle to be in radians.
# -
# Operators are not case sensitive.  SIN, sin and sIn are the same.
# Only labels and memory register names ARE case sensitive.
# -
# Some operators return two values, these will be placed in the x
# & y registers.
# -
# 'fix' uses the absolute value of the integer supplied
# -
# The ',' & '.' can be used in place of the '<' & '>' symbols.
# -
# Type 'k' to see keyboard shortcuts.
# -
# Type 'help op' for a list of available operators.
# """

# Products currently used to create this script:
# Python 3.9.1 (www.python.org)
# Vim 8.1.1401 (www.vim.org)

# The next line is for the VIM text editor:
# vim: tabstop=2 expandtab shiftwidth=2 softtabstop=2

# Going to keep it simple.  This calculator reads the input
# line and anything that it determines to be a number gets
# pushed onto the stack's bottom while everything in the stack
# gets "lifted" up one position (what was in "t:" gets
# discarded.
#
# Every value determined NOT to be a number is assumed to be an
# operator.  Every number or operator must be separated by
# either a [space] or an [enter].  All operators operate on the
# contents of the stack.
#
# Every value used by an operator gets pulled from the stack
# causing the stack to "drop" (exceptions made for '%' & '%c")
# everytime a value is used.  When the stack "drops" the "t:"
# value is copied to the "z:" register and stays in the "t:"
# register.
#
# The size of the stack can be changed below to something larger
# than 4, but caution: this might upset programs that rely on
# a fixed stack size.  I suppose one could easily edit this
# program to have an 'infinite' stack just by replacing the body
# of 'push()' & 'pull()' with stack.append(x) & stack.pop().
#
# Only known issue I know of is that the display doesn't show really
# small numbers in scientific notation.  It just shows them as '0.0'

import math
import os
import ast
import random
import readline  # all you need to recall command history.

# Global variables:
# stack_size can be changed below (4 is the minimum), but only if
# there isn't a .mem file to read the stack from.
# memnam is the file that stores the calculator's memory settings.
# prognam is a text file that contains user defined programs.
# op_dict is a help file for all commands.
stack_size = 4  # size of the stack.
stack_min = 4  # minimum stack size.
stack = []  # List of ? size to hold the stack's values.
mem = {}  # Dictionary of memory registers.
memnam = os.path.splitext(__file__)[0] + ".mem"
prognam = os.path.splitext(__file__)[0] + ".txt"

# common usage: print(f'{XXX}')
if os.name == "posix":  # other OS might not handle these properly:
  RED = "\033[91m"  # Makes the text following it red
  GRN = "\033[92m"  # Green
  YLW = "\033[93m"  # Yellow
  BLU = "\033[94m"  # Blue
  PUR = "\033[35m"  # Purple
  CYN = "\033[36m"  # Cyan
  WHT = "\033[0m"  # White (default)
  CLS = "\x1b[2J"  # Clears the screen above the stack
  SIG = "\u03A3"  # Sigma character
  LSG = "\u03C3"  # Lowercase Sigma character
  SS2 = "\u00B2"  # Superscript 2 (as in ^2)
  OVR = "\u0304"  # Puts a line over the char that precedes it
  SQR = "\u221A"  # square root symbol
else:
  RED = ""
  GRN = ""
  YLW = ""
  BLU = ""
  PUR = ""
  CYN = ""
  WHT = ""
  CLS = ""
  SIG = "E"
  LSG = "o"
  SS2 = "^2"
  OVR = "(mn)"
  SQR = ""

kbsc2 = {  # just so we don't have to use shift key very much
  "c.f": "c>f",
  "f.c": "f>c",
  "p.r": "p>r",
  "r.p": "r>p",
  "x,0?": "x<0?",
  "x,=0?": "x<=0?",
  "x,=y?": "x<=y?",
  "x,y?": "x<y?",
  "x.0?": "x>0?",
  "x.=0?": "x>=0?",
  "x.=y?": "x>=y?",
  "x.y?": "x>y?",
  "=": "+",  # we don't use '=' in RPN, so save the shift key.
  "**": "^",  # This one's just for Python compatibility.
}

op_dict = {  # dictionary of operators for 'help' function
  "+": "Sums the contents of x and y.",
  "-": "Subtracts x from y.",
  "*": "Multiplies x times y.",
  "/": "Divide y by x.",
  "xroot": "The xth root of base y.",
  "r>p": "Rectangular to polar (y = angle, x = magnitude)",
  "p>r": "Polar to rectangular (y = angle, x = magnitude)",
  "%": "x percent of y (y remains in stack).",
  "%c": "Percentage change from y to x (y remains in stack).",
  "cnr": "Combinations of x in y items.",
  "pnr": "Permutations of x in y items.",
  "sqrt": "Square root of x.",
  "sq": "Square of x.",
  "e": "Natural antilogaritm of x (e^x).",
  "ln": "Natural logarithm of x.",
  "tx": "Base 10 raised to the x (10^x).",
  "log": "Base 10 log of x.",
  "rcp": "reciprocal of x (1/x).",
  "chs": "Change the current sign of x (+/-).",
  "abs": "Absolute value of x (|x|).",
  "ceil": "raises x to the next highest integer.",
  "floor": "lowers x to the next lowest integer.",
  "!": "Factorial of integer x (x!).",
  "gamma": "The Gamma of x.",
  "frac": "Fractional portion of x.",
  "int": "Integer portion of x.",
  "rnd": "Rounds x to the displayed value.",
  "ratio": "Convert x to a ratio of 2 integers (y/x).",
  "sin": "Sine of angle in x (x is in radians).",
  "cos": "Cosine of angle in x (x is in radians).",
  "tan": "Tangent of angle in x (x is in radians).",
  "asin": "Arcsine of y/r ratio in x (returns angle in radians).",
  "acos": "Arccosine of x/r ratio in x (returns angle in radians).",
  "atan": "Arctangent of y/x ratio in x (returns angle in radians).",
  "sinh": "Hyperbolic sine of angle in x (x in radians).",
  "cosh": "Hyperbolic cosine of angle in x (x in radians).",
  "tanh": "Hyperbolic tangent of angle in x (x in radians).",
  "asinh": "Hyperbolic arcsine of ratio x (result in radians).",
  "acosh": "Hyperbolic arccosine of ratio x (result in radian).",
  "atanh": "Hyperbolic arctangent of ratio x (result in radians).",
  "atan2": "Arctangent of y/x (considers signs of x & y).",
  "hyp": "Hypotenuse of right sides x & y.",
  "rad": "Converts degrees to radians.",
  "deg": "Converts radians to degrees.",
  "in": "Converts centimeters to inches.",
  "cm": "Converts inches to centimeters.",
  "gal": "Converts litres to gallons.",
  "ltr": "Converts gallons to litres.",
  "lbs": "Converts kilograms to lbs.",
  "kg": "Converts lbs. to kilograms.",
  "c>f": "Converts celsius to fahrenheit.",
  "f>c": "Converts fahrenheit to celsius.",
  "pi": "Returns an approximate value of pi.",
  "tau": "Returns approximate value of 2pi.",
  "swap": "Exchanges the values of x and y.",
  "dup": "Duplicates the value x in y (lifting the stack).",
  "clr": "Clears all values in the stack.",
  "rd": "Rolls the contents of stack down one postition.",
  "ru": "Rolls the contents of stack up one position.",
  "cs": "Copy the sign of y to the x value.",
  "rand": "Generate a random number between 0 and 1.",
  "fix": "Set the # of decimal places displayed by the value that follows.\n\
     If nothing follows it: returns # of decimal places to the stack.",
  "show": "Display the full value of x.",
  "sto": "Save the value in x to a named register (STO <ab0>).",
  "rcl": "Recall the value in a register (RCL <ab0>).",
  "mem": "Display the memory registers and their contents.",
  "clrg": "Clears the contents of all the registers.",
  "lbl": "Designates a label name to follow (LBL <a>).",
  "exc": "Executes a program starting at a label (EXC <a>).",
  "gsb": "Branches program to subroutine a label (GSB <a>).",
  "gto": "Sends program to a label (GTO <a>)",
  "rtn": "Designates end of program or subroutine.",
  "pse": "Pauses program and displays current result.",
  "nop": "Takes up a space. Does nothing else.",
  "x=0?": "Tests if x equals 0. Skips the next 2 objects if false.",
  "x!=0?": "Tests if x does not equal 0. Skips the next 2 objects on false.",
  "x>0?": "Tests if x is greater than 0. Skips the next 2 objects on false.",
  "x<0?": "Tests if x is less than 0. Skips the next 2 objects on false.",
  "x>=0?": "Tests if x is greater than or equal to 0. Skips the next 2 objects on false.",
  "x<=0?": "Tests if x is less than or equal to 0. Skips then next 2 objects on false.",
  "x=y?": "Tests if x is equal to y. Skips the next 2 objects on false.",
  "x!=y?": "Tests if x is not equal to y. Skips the next 2 objects on false.",
  "x>y?": "Tests if x is greater than y. Skips the next 2 objects on false.",
  "x<y?": "Tests if x is less than y. Skips the next 2 objects on false.",
  "x>=y?": "Tests if x is greater than or equal to y. Skips the next 2 objects on false.",
  "x<=y?": "Tests if x is less than or equal to y. Skips the next 2 objects on false.",
  "del": "Delete a register by name (DEL x).",
  "^": "Raises y(base) to the x(exponent).",
  "quit": "Exits the program and saves the contents of the stack and registers.",
  "ptr": "Returns the value of the command line's pointer.",
  "dh": "Converts h.mmss to decimal equivalent.",
  "hms": "Convert decimal time to h.mmss.",
  "prog": "Print programming memory.",
  "gcd": "Greatest common divisor of integers x & y.",
  "cls": "Clear screen of any messages.",
  "edit": "Enter programming memory.",
  "scut": "Displays keyboard shortcuts.",
  "scutadd": "Add a keyboard shortcut: scutadd <shortcut> <operator/value>",
  "scutdel": "Delete a keyboard shortcut: scutdel <shortcut>",
  "help": "I'm being repressed! Also: followed by an operator gives detailed info\n\
on that operator, while 'op' will list all operators.",
  "version": "Display the current version number.",
  "stat": "When not followed by a modifier adds x & y to the data set.\n\
  Following with a number will enter x & y into the data set that many times.\n\
  Following with 'show' displays stat info without adding to it.\n\
  Following with 'undo' subtracts the values of x & y from the data sets.\n\
  Following with 'clear' resets data to zero.\n\
  Following with 'save' copies the statistic registers to the user registers.\n\
  Following with 'est' uses 'x' to return an estimated 'y'.\n\
  Follow with 'n', 'Ex', 'Ey', 'Ex2', 'Ey2', 'Exy', 'x', 'y', 'ox', 'oy',\n\
    'r', 'a', or 'b' to return that value to the stack.",
}

# function to initialize the size of the stack and fill it with zeros:
def initstack(st_size):
  """Initializes the stack.
  Fills it with zeros if the .mem file is missing."""
  stack = []
  st_size = max(st_size, stack_min)
  while st_size:
    stack.append(0.0)
    st_size -= 1
  return stack


# push a number onto the bottom of the stack raising everything
# else up.
def push(num):
  """Push a number onto the stack."""
  i = len(stack) - 1
  while i:
    stack[i] = stack[i - 1]
    i -= 1
  stack[0] = float(num)


# pull a number off the bottom of stack and drop everything down one.
def pull():
  """Pull a number off the stack."""
  i = 0
  num = stack[i]
  while i < len(stack) - 1:
    stack[i] = stack[i + 1]
    i += 1
  return num


# pull the program data from the text file.
# apparently, 'for line in...' closes the file for you
#   after reading the last line.  Thanks, Python!
def program_data(progf):
  """Copies .txt file to memory."""
  if os.path.exists(progf):
    prog = ""
    for line in open(progf, "r", encoding="utf-8"):
      line = line.split("#")[0]
      prog += line
    prog = prog.split()
    return prog


# This is the guts of the whole thing...
def calc(stack, mem, prog_listing, decimal_places, stat_regs):
  """Processes all input."""
  # statistical variables:
  Sn = stat_regs["Sn"]
  Sx = stat_regs["Sx"]
  Sy = stat_regs["Sy"]
  Sx2 = stat_regs["Sx2"]
  Sy2 = stat_regs["Sy2"]
  Sxy = stat_regs["Sxy"]
  if Sn > 1 and Sn * Sx2 != Sx ** 2 and Sn * Sy2 != Sy ** 2:
    Mx = Sx / Sn  # mean of x
    My = Sy / Sn  # mean of y
    SDx = math.sqrt((Sn * Sx2 - Sx ** 2) / (Sn * (Sn - 1)))
    SDy = math.sqrt((Sn * Sy2 - Sy ** 2) / (Sn * (Sn - 1)))
    # correlation coefficent(r):
    CCr = (Sn * Sxy - Sx * Sy) / math.sqrt(
      (Sn * Sx2 - Sx ** 2) * (Sn * Sy2 - Sy ** 2)
    )
    Sa = (Sn * Sxy - Sx * Sy) / (Sn * Sx2 - Sx ** 2)  # slope(a):
    YIb = Sy / Sn - Sa * Sx / Sn  # y intercept(b):
  else:
    Mx = My = SDx = SDy = CCr = Sa = YIb = 0

  incr = True  # in case you want to stop the pointer (it_r) from incrementing

  print(f"{CLS}{YLW}Type 'help' for documentation.")
  print(f"Type 'help op' for a list of available operators.")
  print(f"Type 'help <operator>' (without braces) for specifics on an operator.")
  print(f"Type 'scut' for a list of keyboard shortcuts.{WHT}\n")

  while True:  # loop endlessly until a break statement

    it_r = 0  # token iterator

    # Display the stack and prompt for input:
    reg = ["x:", "y:", "z:", "t:"]  # our stack labels
    i = len(reg) - 1  # index of the last label
    while i:  # prints out 'y', 'z' and 't'
      print(f"{YLW}{reg[i]}{WHT} {stack[i]:,.{decimal_places}f}")
      i -= 1
    # Now display x and prompt for the command line:
    # note: cmd_ln is the input line as a Python list.
    cmd_ln = input(f"{RED}{reg[0]}{WHT} {stack[0]:,.{decimal_places}f} ").split()

    # clear the screen; probably shouldn't be here.
    # this works in linux on my chromebook.
    # remove if you're a history buff.
    if os.name == "posix":  # not sure this will work on other systems
      print(f"{CLS}")  # clear the screen.

    try:
      if cmd_ln[it_r].lower() in ["quit", "exit", "close"]:
        fh = open(memnam, "w", encoding="utf-8")
        fh.write(f"{stack}\n{mem}\n{decimal_places}\n{kbsc}\n")
        stat_regs["Sn"] = Sn
        stat_regs["Sx"] = Sx
        stat_regs["Sy"] = Sy
        stat_regs["Sx2"] = Sx2
        stat_regs["Sy2"] = Sy2
        stat_regs["Sxy"] = Sxy
        fh.write(f"{stat_regs}")
        fh.close()
        break
    except IndexError:  # just pressing ENTER is the same as 'dup'
      x = pull()
      push(x)
      push(x)

    # Execute the command line
    #
    while it_r < len(cmd_ln):
      try:
        # make the space delimited string object a token:
        token = cmd_ln[it_r].lower()  # is anything NaN.
        #
        # substitute a type shortcut for its operator.
        if token in kbsc.keys():
          token = kbsc[token]
        if token in kbsc2.keys():  # shift not needed.
          token = kbsc2[token]
        #
        # convoluted way to figure out if the token is a number:
        if token[0].isdigit() or (token[0] in ".+-" and len(token) > 1):
          push(token)
        #
        # if it doesn't satisfy the above criteria for being a number
        # it's assumed to be an operator.
        #
        # binary operators:
        #
        # addition:
        elif token == "+":
          x = pull()
          y = pull()
          push(x + y)
        #
        # subtraction:
        elif token == "-":
          x = pull()
          y = pull()
          push(y - x)
        #
        # multiplication:
        elif token == "*":
          x = pull()
          y = pull()
          push(x * y)
        #
        # division:
        elif token == "/":
          x = pull()
          y = pull()
          push(y / x)
        #
        # raise y to the x:
        elif token == "^":
          x = pull()
          y = pull()
          push(y ** x)
        #
        # x root of y:
        elif token == "xroot":
          x = pull()
          y = pull()
          push(y ** (1 / x))
        #
        # rectangular to polar conversion:
        elif token == "r>p":
          x = pull()
          y = pull()
          push(math.atan2(y, x))  # angle
          push(math.hypot(x, y))  # magnitude
          print(
            f"{YLW}Angle(y): {WHT}{math.atan2(y,x):.4f}{YLW};"
            + f" Magnitude(x): {WHT}{math.hypot(x,y):.4f}\n"
          )
        #
        # polar to rectangular conversion:
        elif token == "p>r":
          x = pull()  # magnitude
          y = pull()  # angle
          push(x * math.sin(y))  # y
          push(x * math.cos(y))  # x
        #
        # x percent of y (leaves y in the stack):
        elif token == "%":
          x = pull()
          y = pull()
          push(y)
          push((x / 100) * y)
        #
        # percentage change from y to x (leaves y in the stack):
        elif token == "%c":
          x = pull()
          y = pull()
          push(y)
          push((x / y - 1) * 100)
        #
        # combinations of x into y:
        elif token == "cnr":
          x = int(pull())  # forced int here to prevent push line from
          y = int(pull())  # from getting too long.
          push(
            math.factorial(y) / (math.factorial(x) * math.factorial(y - x))
          )
        #
        # permutations of x in y:
        elif token == "pnr":
          x = int(pull())  # see "cnr" above
          y = int(pull())
          push(math.factorial(y) / math.factorial(y - x))
        #
        # greatest common divisor of x & y:
        elif token == "gcd":
          x = pull()
          y = pull()
          push(math.gcd(int(x), int(y)))  # different method forcing ints
        #
        # unary operators:
        #
        # square root of x:
        elif token == "sqrt":
          x = pull()
          push(math.sqrt(x))
        #
        # square of x:`
        elif token == "sq":
          x = pull()
          push(x ** 2)
        #
        # e to the x (e^x):
        elif token == "e":
          x = pull()
          push(math.exp(x))
        #
        # natural log of x:
        elif token == "ln":
          x = pull()
          push(math.log(x))
        #
        # Base of 10 raised to x:
        elif token == "tx":
          x = pull()
          push(10 ** x)
        #
        # base 10 log of x:
        elif token == "log":
          x = pull()
          push(math.log10(x))
        #
        # reciprocal of x (1/x):
        elif token == "rcp":
          x = pull()
          push(1 / x)
        #
        # change sign of x:
        elif token == "chs":
          x = pull()
          push(x * -1)
        #
        # absolute value of x:
        elif token == "abs":
          x = pull()
          push(math.fabs(x))
        #
        # ceiling of x:
        elif token == "ceil":
          x = pull()
          push(math.ceil(x))
        #
        # floor of x:
        elif token == "floor":
          x = pull()
          push(math.floor(x))
        #
        # factorial of x:
        elif token == "!":
          x = pull()
          push(math.factorial(int(x)))
        #
        # gamma of x:
        elif token == "gamma":
          x = pull()
          push(math.gamma(x))
        #
        # fractional portion of x:
        elif token == "frac":
          x = pull()
          push(math.modf(x)[0])
        #
        # integer portion of x:
        elif token == "int":
          x = pull()
          push(math.modf(x)[1])
        #
        # round a number to the display value
        elif token == "rnd":
          x = pull()
          push(round(x, decimal_places))
        #
        # convert a float into a ratio (y/x):
        elif token == "ratio":
          x = pull()
          push(x.as_integer_ratio()[0])
          push(x.as_integer_ratio()[1])
        #
        # trigonometry operators:
        #
        elif token == "sin":
          x = pull()
          push(math.sin(x))
        elif token == "cos":
          x = pull()
          push(math.cos(x))
        elif token == "tan":
          x = pull()
          push(math.tan(x))
        elif token == "asin":
          x = pull()
          push(math.asin(x))
        elif token == "acos":
          x = pull()
          push(math.acos(x))
        elif token == "atan":
          x = pull()
          push(math.atan(x))
        elif token == "sinh":
          x = pull()
          push(math.sinh(x))
        elif token == "cosh":
          x = pull()
          push(math.cosh(x))
        elif token == "tanh":
          x = pull()
          push(math.tanh(x))
        elif token == "asinh":
          x = pull()
          push(math.asinh(x))
        elif token == "acosh":
          x = pull()
          push(math.acosh(x))
        elif token == "atanh":
          x = pull()
          push(math.atanh(x))
        elif token == "atan2":  # arctangent of y/x (considers signs of x & y):
          x = pull()
          y = pull()
          push(math.atan2(y, x))
        elif token == "hyp":  # hypotenuse of x & y:
          x = pull()
          y = pull()
          push(math.hypot(x, y))
        #
        # angle conversions:
        #
        # convert angle in degrees to radians:
        elif token == "rad":
          x = pull()
          push(math.radians(x))
        #
        # convert angle in radians to degrees:
        elif token == "deg":
          x = pull()
          push(math.degrees(x))
        #
        # metric/imperial conversions:
        #
        # convert length in centimeters to inches:
        elif token == "in":
          x = pull()
          push(x / 2.54)
        #
        # convert length in inches to centimeters:
        elif token == "cm":
          x = pull()
          push(x * 2.54)
        #
        # convert volume in litres to gallons:
        elif token == "gal":
          x = pull()
          push((((x * 1000) ** (1 / 3) / 2.54) ** 3) / 231)
        #
        # convert volume in gallons to litres:
        elif token == "ltr":
          x = pull()
          push(x * 231 * 2.54 ** 3 / 1000)
        #
        # convert weight in kilograms to lbs.:
        elif token == "lbs":
          x = pull()
          push(x * 2.204622622)
        #
        # convert weight in lbs. to kilograms:
        elif token == "kg":
          x = pull()
          push(x / 2.204622622)
        #
        # convert temperature from celsius to fahrenheit:
        elif token == "c>f":
          x = pull()
          push(x * 9 / 5 + 32)
        #
        # convert temperature from celsius to fahrenheit:
        elif token == "f>c":
          x = pull()
          push((x - 32) * 5 / 9)
        #
        # convert h.mmss to a decimal value:
        elif token == "dh":
          x = pull()
          h = int(x)
          m = int((x - h) * 100)
          s = round((x - h - (m / 100)) * 10000, 4)
          print(f"{YLW}{h}h:{m}m:{s}s{WHT}\n")
          push(h + (m / 60) + (s / (60 ** 2)))
        #
        # convert decimal time value to h.mmss:
        elif token == "hms":
          x = pull()
          h = int(x)
          m = int((x * 60) % 60)
          s = round((x * 3600) % 60, 4)
          print(f"{YLW}{h}h:{m}m:{s}s{WHT}\n")
          push(h + m / 100 + s / 10000)
        #
        # constant(s):
        #
        # the approximate value of pi:
        elif token == "pi":
          push(math.pi)
        #
        # the approximate value of 2pi:
        elif token == "tau":
          push(math.tau)
        #
        # stack manipulators:
        #
        # swap x and y:
        elif token == "swap":
          x = pull()
          y = pull()
          push(x)
          push(y)
        #
        # duplicate the value in x:
        elif token == "dup":
          x = pull()
          push(x)
          push(x)
        #
        # clear the contents of the stack:
        elif token == "clr":
          i = len(stack)
          while i:
            push(0.0)
            i -= 1
        #
        # 'roll' the stack down one:
        elif token == "rd":
          i = 0
          t = stack[0]
          while i < len(stack) - 1:
            stack[i] = stack[i + 1]
            i += 1
          stack[i] = t
        #
        # 'roll' the stack up one:
        elif token == "ru":
          i = len(stack) - 1
          t = stack[i]
          while i:
            stack[i] = stack[i - 1]
            i -= 1
          stack[i] = t
        #
        # miscellaneous:
        #
        # copy the sign of y to x:
        elif token == "cs":
          x = pull()
          y = pull()
          push(y)
          push(math.copysign(x, y))
        #
        # return the value of the cmd line pointer
        elif token == "ptr":
          push(it_r)
        #
        # generate a pseudo random number between 0 and 1:
        elif token == "rand":
          push(random.random())
        #
        # set the number of decimals to the following value:
        elif token == "fix":
          it_r += 1
          if it_r == len(cmd_ln):  # there's nothing after 'fix'
            push(decimal_places)
          else:
            decimal_places = abs(int(cmd_ln[it_r]))
        #
        # show the whole value of the x register:
        elif token == "show":
          x = pull()
          push(x)
          print(f"{YLW}{x:,}{WHT}\n")
        #
        # store x in a named 'register':
        elif token == "sto":
          x = pull()
          push(x)
          it_r += 1
          mem[cmd_ln[it_r]] = x
        #
        # recall a value from 'memory':
        elif token == "rcl":
          it_r += 1
          if cmd_ln[it_r] in mem.keys():
            push(mem[cmd_ln[it_r]])
            print(f"{YLW}{cmd_ln[it_r]}{WHT}\n")
          else:
            print(
              f"{RED}Register {WHT}{cmd_ln[it_r]}{RED} not found.{WHT}\n"
            )
        #
        # delete a register:
        elif token == "del":
          it_r += 1
          if cmd_ln[it_r] in mem.keys():
            del mem[cmd_ln[it_r]]
          else:
            print(
              f"{RED}Register {WHT}{cmd_ln[it_r]}{RED} not found.{WHT}\n"
            )
        #
        # display the contents of the memory regsiters:
        elif token == "mem":
          print(f"{YLW}Memory registers:")
          print(f"{str(mem)[1:-1]}{WHT}\n")
        #
        # display keyboard shortcuts:
        elif token == "scut":
          print(f"{YLW}Keyboard shortcuts:")
          print(f'{str(kbsc)[1:-1].replace(": ",":")}{WHT}\n')
        #
        # add a shortcut to the list:
        elif token == "scutadd":
          it_r += 1
          key = cmd_ln[it_r]
          it_r += 1
          kbsc[key] = cmd_ln[it_r]
        #
        # delete a shortcut from the list:
        elif token == "scutdel":
          it_r += 1
          key = cmd_ln[it_r]
          if key in kbsc:
            del kbsc[key]
          else:
            print(f"{RED}Shortcut {WHT}{key}{RED} not found.{WHT}\n")
        #
        # clear the contents of the memory registers:
        elif token == "clrg":
          mem.clear()
          print(f"{YLW}Registers cleared.{WHT}\n")
        #
        # clear the screen of unwanted messages:
        elif token == "cls":
          print(f"{CLS}")
        #
        # Programming related commands
        #
        # label: only purpose is to be ignored,
        # along with the token immediately after it.
        # EXC, GSB, GTO & RTN will use labels.
        elif token == "lbl":
          it_r += 1  # now points to the labels descriptor
          # the it_r += 1 at the end will step over the label's
          # descriptor
        #
        # executes the program starting at label x:
        # Things got a lot more complicated when I decided
        # to allow basic calculator style programming...
        elif token == "exc":
          # setup a few things to allow jumping around
          it_r += 1
          x = 0
          pdict = {}
          # build dict of labels in the format: {name: location}
          while x < len(prog_listing):
            if prog_listing[x].lower() == "lbl":
              x += 1
              pdict[prog_listing[x]] = x
            x += 1
          # if the label exists replace the command line
          # and set the pointer (it_r) to the start.
          if cmd_ln[it_r] in pdict:
            lbl_nam = cmd_ln[it_r]
            lbl_rtn = []
            cmd_ln = prog_listing
            it_r = pdict[lbl_nam]
          else:
            print(f"{RED}Label {WHT}{cmd_ln[it_r]}{RED} not found.{WHT}\n")
        #
        # gosub routine:
        # This tosses the calling location onto the lbl_rtn
        # stack we created in 'EXC' so we'll know where to
        # return to.
        elif token == "gsb":
          it_r += 1
          lbl_rtn.append(it_r)
          it_r = pdict[cmd_ln[it_r]]
        #
        # goto routine:
        # Just like 'gsb' but no need to go back.
        elif token == "gto":
          it_r += 1
          it_r = pdict[cmd_ln[it_r]]
        #
        # return - for end of program or subroutine:
        # if called by a 'gsb' will go back to the token
        # following the 'gsb'.  Otherwise it will end the
        # program.
        elif token == "rtn":
          if len(lbl_rtn):
            it_r = lbl_rtn.pop()
          else:
            it_r = 0
            cmd_ln = ["nop", "nop"]
        #
        # pauses a running program
        elif token == "pse":
          input(f"\n{YLW}Press ENTER to continue.{WHT}")
        #
        # does nothing.  Short for "No OPeration"
        elif token == "nop":
          pass
        #
        # tests: lots of tests. No branching, just jumping if
        # false. if true, continues execution at the the next
        # token, otherwise: skip the next two(2) tokens.
        #
        # test if x is equal to 0:
        elif token == "x=0?":
          x = pull()
          push(x)
          if x:  # same as "if not x=0"
            it_r += 2
        #
        # test if x in not equal to 0:
        elif token == "x!=0?":
          x = pull()
          push(x)
          if not x:
            it_r += 2
        #
        # test if x is greater than 0:
        elif token == "x>0?":
          x = pull()
          push(x)
          if not x > 0:
            it_r += 2
        #
        # test if x is less than 0:
        elif token == "x<0?":
          x = pull()
          push(x)
          if not x < 0:
            it_r += 2
        #
        # test if x is greater than or equal to 0:
        elif token == "x>=0?":
          x = pull()
          push(x)
          if not x >= 0:
            it_r += 2
        #
        # test if x is less than or equal to 0:
        elif token == "x<=0?":
          x = pull()
          push()
          if not x <= 0:
            it_r += 2
        #
        # test if x is equal to y:
        elif token == "x=y?":
          x = pull()
          y = pull()
          push(y)
          push(x)
          if x != y:
            it_r += 2
        #
        # test if x is NOT equal to y:
        elif token == "x!=y?":
          x = pull()
          y = pull()
          push(y)
          push(x)
          if x == y:
            it_r += 2
        #
        # test if x is greater than y:
        elif token == "x>y?":
          x = pull()
          y = pull()
          push(y)
          push(x)
          if not x > y:
            it_r += 2
        #
        # test if x is less than y:
        elif token == "x<y?":
          x = pull()
          y = pull()
          push(y)
          push(x)
          if not x < y:
            it_r += 2
        #
        # test if x is greater than or equal to y:
        elif token == "x>=y?":
          x = pull()
          y = pull()
          push(y)
          push(x)
          if not x >= y:
            it_r += 2
        #
        # test if x is less than or equal to y:
        elif token == "x<=y?":
          x = pull()
          y = pull()
          push(y)
          push(x)
          if not x <= y:
            it_r += 2
        #
        # dump the program listing:
        elif token == "prog":
          print(f"{YLW}Programming space:\n ", end="")
          print(f" ".join(i for i in prog_listing).replace("RTN", "RTN\n"))
          print(f"{WHT}")
        #
        # edit the program data file:
        elif token == "edit":
          if os.name == "posix":
            os.system(
              "vim {}".format(os.path.splitext(__file__)[0] + ".txt")
            )
            prog_listing = program_data(prognam)  # reload
            print(f"{CLS}")
        #
        # print the version number:
        elif token == "version":
          print(f"{RED}{version}{WHT}\n")
        #
        # display help (in a convoluted fashion, but this *is*
        # an exercise in learning how to program).
        elif token == "help":
          it_r += 1
          if it_r < len(cmd_ln):
            if cmd_ln[it_r].lower() in ["op", "o"]:  # list operators
              s = str(op_dict.keys())[11:-2]
              s = s.replace("'", "")
              s = s.replace(",", "")
              s = s.upper()
              s = s.split()
              s.sort()
              print(
                f"{YLW}Type 'help xxx' for specific help on an operator."
              )
              print(f"Available operators are:")
              for x in s:
                print(f"'{x}'", end=" ")
              print(f"\nOperators are not case sensitive.")
              print(f"Shortcut key shows in parentheses.{WHT}\n")
            # look up help on a particular operator:
            elif cmd_ln[it_r].lower() in op_dict:
              print(f"{YLW}{cmd_ln[it_r].upper()}", end="")
              if cmd_ln[it_r].lower() in kbsc.values():
                # confusing way to sort a dictionary for printing.
                print(
                  f"({list(kbsc.keys())[list(kbsc.values()).index(cmd_ln[it_r].lower())]})",
                  end="",
                )
              print(f": {str(op_dict[cmd_ln[it_r].lower()])}{WHT}\n")
            else:
              print(
                f"{RED}Operator {WHT}{cmd_ln[it_r]}{RED} not found.{WHT}\n"
              )
          else:  # just print the __doc__ string from the top
            print(f"{YLW}{__doc__}{WHT}")
        #
        #
        # 2 variable statistics:
        elif token == "stat":
          x = pull()
          y = pull()
          push(y)  # put the stack back the way you found it
          push(x)
          # Note that the stat identifiers for the user do not match what's used
          # internally by the script. So we made a new dictionary just for the
          # user to retrieve these values.
          stat_dict = {
            "n": Sn,
            "Ex": Sx,
            "Ey": Sy,
            "Ex2": Sx2,
            "Ey2": Sy2,
            "Exy": Sxy,
            "x": Mx,
            "y": My,
            "ox": SDx,
            "oy": SDy,
            "r": CCr,
            "a": Sa,
            "b": YIb,
          }

          num = 0
          if it_r + 1 == len(cmd_ln):  # blank after 'stat'?
            num = 1  # then just make one entry
          else:
            it_r += 1  # increment to the next item in cmd_ln
          if cmd_ln[it_r].isdigit():
            num = int(cmd_ln[it_r])
          if num > 0:
            i = 0
            while i < num:  # All the statistical variables we need
              Sn += 1  # incr it_r - tracks # of xy pairs
              Sx += x  # sum of the x entries
              Sy += y  # sum of the y entries
              Sx2 += x ** 2  # sum of the squares of the x entries
              Sy2 += y ** 2  # sum of the squares of the y entries
              Sxy += x * y  # sum of the product of the x & y entries
              i += 1
          if cmd_ln[it_r].lower() == "undo":
            Sn -= 1
            Sx -= x
            Sy -= y
            Sx2 -= x ** 2
            Sy2 -= y ** 2
            Sxy -= x * y
          if Sn > 1 and Sn * Sx2 != Sx ** 2 and Sn * Sy2 != Sy ** 2:
            Mx = Sx / Sn  # mean of x
            My = Sy / Sn  # mean of y
            # ox = sqrt((n*Ex^2-(Ex)^2)/(n*(n-1))) std deviation of x
            SDx = math.sqrt((Sn * Sx2 - Sx ** 2) / (Sn * (Sn - 1)))
            # oy = sqrt((n*Ey^2-(Ey)^2)/(n*(n-1))) std deviation of y
            SDy = math.sqrt((Sn * Sy2 - Sy ** 2) / (Sn * (Sn - 1)))
            # correlation coefficent(r):
            CCr = (Sn * Sxy - Sx * Sy) / math.sqrt(
              (Sn * Sx2 - Sx ** 2) * (Sn * Sy2 - Sy ** 2)
            )
            Sa = (Sn * Sxy - Sx * Sy) / (Sn * Sx2 - Sx ** 2)  # slope(a):
            YIb = Sy / Sn - Sa * Sx / Sn  # y intercept(b):
          if cmd_ln[it_r].lower() == "clear":
            Sn = (
              Sx
            ) = (
              Sy
            ) = Sx2 = Sy2 = Sxy = Mx = My = SDx = SDy = CCr = Sa = YIb = 0
          elif (
            cmd_ln[it_r].lower() == "save"
          ):  # Add the stat regs to the user regs
            mem.update(stat_dict)
          # mem = mem | stat_dict # << I think this method requires Python 3.9.
          #
          elif cmd_ln[it_r].lower() == "est":
            x = pull()  # just to clear the estimate off the stack
            push(Sa * x + YIb)  # y=ax+b; put y onto the stack
            print(f"{YLW}x: {WHT}{x}{YLW}, ~y: {WHT}{Sa * x + YIb}\n")
          elif cmd_ln[it_r] in stat_dict.keys():
            push(stat_dict[cmd_ln[it_r]])
          # Essentially anything after 'stat' will stop x & y from being added.
          # Originally required 'show' to display stat data, but now you can
          # type anything that's not a number or specified above.
          print(f"{YLW}n:   {WHT}{Sn:.0f}")
          print(f"{YLW}{SIG}x:  {WHT}{Sx:.4f}")
          print(f"{YLW}{SIG}y:  {WHT}{Sy:.4f}")
          print(f"{YLW}{SIG}x{SS2}: {WHT}{Sx2:.4f}")
          print(f"{YLW}{SIG}y{SS2}: {WHT}{Sy2:.4f}")
          print(f"{YLW}{SIG}xy: {WHT}{Sxy:.4f}")
          if Sn > 1:  # need 2 or more data points for these
            print(f"{YLW}x{OVR}:   {WHT}{Mx:.4f}")
            print(f"{YLW}y{OVR}:   {WHT}{My:.4f}")
            if Sn > 2:  # Std Deviation appears to need at least 3 sets
              print(f"{YLW}{LSG}x:  {WHT}{SDx:.4f}")
              print(f"{YLW}{LSG}y:  {WHT}{SDy:.4f}")
            print(f"{YLW}r:   {WHT}{CCr:.4f}")
            print(f"{YLW}a:   {WHT}{Sa:.4f}")
            print(f"{YLW}b:   {WHT}{YIb:.4f}")
          print(f"{WHT}")  # blank line
        #
        # it didn't match any token above, check to see if it's
        # a register. If not, assume it's an error.
        #
        # last chance to do something with the token.
        # note that if you name a register the same as a command
        # you'll need to use 'rcl'.
        elif token in mem.keys():
          push(mem[cmd_ln[it_r]])
        #
        # it's not recognized.
        else:
          print(f"{RED}Invalid Operator: {WHT}{token}\n")
        #
        # increment the command line pointer to the next token
        # and go back through this loop:
        if incr == True:
          it_r += 1
        incr = True

      # exception list
      except ValueError:
        print(f"{RED}Value error: {WHT}{token}\n")
        break
      except ZeroDivisionError:
        print(f"{RED}Division by zero error: {WHT}{token}\n")
        break
      except OverflowError:
        print(f"{RED}Overflow error: {WHT}{token}\n")
        break
      except IndexError:
        print(f"{RED}Index Error: {WHT}{token}\n")
      except KeyError:
        print(f"{RED}Key Error: {WHT}{token}\n")
  # end of the very long looping function calc()


# This part initializes/recalls everything now
# if the mem file exists use it instead of initstack()
if os.path.exists(memnam):
  fh = open(memnam, "r", encoding="utf-8")
  stack = ast.literal_eval(fh.readline())  # a list of floats
  mem = ast.literal_eval(fh.readline())  # dictionary of memory registers
  decimal_places = int(ast.literal_eval(fh.readline()))  # single int
  kbsc = ast.literal_eval(fh.readline())  # dictionary of keyboard shortcuts
  stat_regs = ast.literal_eval(fh.readline())  # statistical registers
  fh.close()
else:  # no mem file? Just create everything from scratch
  stack = initstack(stack_size)
  mem = {}
  decimal_places = 4
  kbsc = {
    "#": "rand",
    "[": "stat",
    "a": "+",
    "b": "xroot",
    "c": "chs",
    "d": "/",
    "f": "!",
    "g": "gamma",
    "h": "help",
    "i": "rcp",
    "j": "rad",
    "k": "scut",
    "l": "ln",
    "m": "mem",
    "n": "frac",
    "o": "^",
    "p": "prog",
    "q": "exc",
    "r": "sqrt",
    "s": "-",
    "t": "sq",
    "u": "deg",
    "v": "int",
    "w": "show",
    "x": "*",
    "y": "swap",
    "z": "abs",
  }
  stat_regs = {"Sn": 0, "Sx": 0, "Sy": 0, "Sx2": 0, "Sy2": 0, "Sxy": 0}

# if a program file exists dump its contents into memory.
# we'll 'import' its contents into memory whether we use it or not
if os.path.exists(prognam):
  prog_listing = program_data(prognam)
else:
  prog_listing = []

if __name__ == "__main__":
  calc(stack, mem, prog_listing, decimal_places, stat_regs)

# Addenda.
# Differences between this and the HP15c include:
#   No complex number support (though it would be easy to implement).
#   No GOTO <line #> (no line numbers to go to).
#   No matrix support. I'm lazy.
#   No DSE or ISG commands (they're useful if space is limited... it's not).
#   No integration. Slept thru calculus.
#   No statistical functionality. Shouldn't be hard. I should do this...
#   No solver (though the one in the 15c is really cool).
#   While 15c programs don't require a label or ending 'RTN', this does.
#   No H.M.S conversion (but would be easy to implement).
#   No "last x" register (forgot about this, should do it, might be useful).
#   Does include the 'atan2' function that the 15c lacks.
#   The 15c had 448 bytes of user memory for programs and storage.
#
# Known bugs and annoyances:
#   Really small numbers are displayed as 0.0 rather than say, 6.674e-11
#   for example, and really large numbers are displayed in full rather
#   than a fixed decimal number.
# Update 1.03:
#   Made it so that you don't have to use 'rcl' if the register name
#   is unique.
#   Fixed 'quit' so it now works with 'exit' and 'close'.
#   Added 'prog' keyword to display the users programs.
#   Added color to 'show', 'mem', and 'prog' results.
# Update 1.04 & 1.05
#   Numerous tweaks; cleaned out some useless code; tightend some functions.
#   Added a clear screen to end scrolling of previous results.
#   Added GCD function (added in Python 3.5).
#   Added 'edit' command to mod/add programs without leaving the calculator.
# Update 1.06
#   Got operators 'dh' and 'hms' working.
#   Added helpful info to 'r>p' operator upon use.
#   Made minor changes to some print statements.
#
# Update 1.08a
#   Added two variable statistics
#   Cleaned up some code.
#   used lots of f strings -- you'll need Python >= 3.6
#
# Update 1.08b
#   Think I finally got 'stat' to not do division by 0.
#   Ran it through Black just for fun.
#
# Update 1.08c
#   Just replaced 'n' with 'it_r' to avoid confusion over what 'n' is.
#   typing 'h o' is the same as 'help op'... unless 'o' becomes an operator.
#   fixed a minor bug where it wouldn't show short cut key when using 'help X'
#
# Update 1.09
#   Added standard deviation for x & y to the statistics engine.
#   Adjusted 'stat' logic to better display input results.
#   Renamed 'inv' 'rcp' i.e.: 1/x is referred to as the 'reciprocal' in HP-15c
#   manual.
#
# To do:
#   Help text needs lots of improvement.
#   Keyboard shortcuts display needs cleaning up.
