#! /usr/bin/env python3
# vim:fileencoding=utf-8

"""
Type in your equation using Reverse Polish Notation.  Numbers are added to the
stack. Operators act upon the values in the stack.  Values/operators can be
input individually (pressing ENTER after every number/operator) or by
separating the tokens with spaces.  Values get "pulled" from the stack when
operated upon.

For example: 4 22 7 / + will divide 22 by 7 then add 4 to the result.

A complete list of operators can be displayed by typing in: "help op"
"""

version = 'RPN Calc version 1.07'

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
# Only labels and storage register names ARE case sensitive.
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
# Python 3.8.5 (www.python.org)
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
# Only known bug I know of is that the display doesn't show really
# small numbers in scientific notation.  It just shows them as '0.0'

import math
import os
import ast
import random

# Global variables:
# stack_size can be changed below (4 is the minimum), but only if
# there isn't a .mem file to read the stack from.
# memnam is the file that stores the calculator's memory settings.
# prognam is a text file that contains user defined programs.
# op_dict is a help file for all commands.
stack_size = 4     # size of the stack.
stack_min  = 4     # minimum stack size.
stack      = []    # List of ? size to hold the stack's values.
mem        = {}    # Dictionary of storage registers.
memnam     = os.path.splitext(__file__)[0] + '.mem'
prognam    = os.path.splitext(__file__)[0] + '.txt'

if os.name == 'posix': # M$ doesn't handle these properly:
  RED = '\033[91m'
  YLW = '\033[93m'
  WHT = '\033[0m'
else:
  RED = ''
  YLW = ''
  WHT = ''

# just so we don't have to use shift.
kbsc2 = {
        'c.f'  :'c>f',
        'f.c'  :'f>c',
        'p.r'  :'p>r',
        'r.p'  :'r>p',
        'x,0?' :'x<0?',
        'x,=0?':'x<=0?',
        'x,=y?':'x<=y?',
        'x,y?' :'x<y?',
        'x.0?' :'x>0?',
        'x.=0?':'x>=0?',
        'x.=y?':'x>=y?',
        'x.y?' :'x>y?',
        '='    :'+', # we don't use '=' in RPN, so save the shift key.
        '**'   :'^' # This one's just for Python compatibility.
        }

op_dict = {
  '+':
'Sums the contents of x and y.',
  '-':
'Subtracts x from y.',
  '*':
'Multiplies x times y.',
  '/':
'Divide y by x.',
  'xroot':
'The xth root of base y.',
  'r>p':
'Rectangular to polar (y = angle, x = magnitude)',
  'p>r':
'Polar to rectangular (y = angle, x = magnitude)',
  '%':
'x percent of y (y remains in stack).',
  '%c':
'Percentage change from y to x (y remains in stack).',
  'cnr':
'Combinations of x in y items.',
  'pnr':
'Permutations of x in y items.',
  'sqrt':
'Square root of x.',
  'sq':
'Square of x.',
  'e':
'e raised to the x (e^x).',
  'ln':
'Natural log of x.',
  'tx':
'Base 10 raised to the x (10^x).',
  'log':
'Base 10 log of x.',
  'inv':
'Inverse of x (1/x).',
  'chs':
'Change the current sign of x (+/-).',
  'abs':
'Absolute value of x (|x|).',
  'ceil':
'raises x to the next highest integer.',
  'floor':
'lowers x to the next lowest integer.',
  '!':
'Factorial of integer x (x!).',
  'gamma':
'The Gamma of x.',
  'frac':
'Fractional portion of x.',
  'int':
'Integer portion of x.',
  'rnd':
'Rounds x to the displayed value.',
  'ratio':
'Convert x to a ratio of 2 integers (y/x).',
  'sin':
'Sine of angle in x (x is in radians).',
  'cos':
'Cosine of angle in x (x is in radians).',
  'tan':
'Tangent of angle in x (x is in radians).',
  'asin':
'Arcsine of y/r ratio in x (returns angle in radians).',
  'acos':
'Arccosine of x/r ratio in x (returns angle in radians).',
  'atan':
'Arctangent of y/x ratio in x (returns angle in radians).',
  'sinh':
'Hyperbolic sine of angle in x (x in radians).',
  'cosh':
'Hyperbolic cosine of angle in x (x in radians).',
  'tanh':
'Hyperbolic tangent of angle in x (x in radians).',
  'asinh':
'Hyperbolic arcsine of ratio x (result in radians).',
  'acosh':
'Hyperbolic arccosine of ratio x (result in radian).',
  'atanh':
'Hyperbolic arctangent of ratio x (result in radians).',
  'atan2':
'Arctangent of y/x (considers signs of x & y).',
  'hyp':
'Hypotenuse of right sides x & y.',
  'rad':
'Converts degrees to radians.',
  'deg':
'Converts radians to degrees.',
  'in':
'Converts centimeters to inches.',
  'cm':
'Converts inches to centimeters.',
  'gal':
'Converts litres to gallons.',
  'ltr':
'Converts gallons to litres.',
  'lbs':
'Converts kilograms to lbs.',
  'kg':
'Converts lbs. to kilograms.',
  'c>f':
'Converts celsius to fahrenheit.',
  'f>c':
'Converts fahrenheit to celsius.',
  'pi':
'Returns an approximate value of pi.',
  'tau':
'Returns approximate value of 2pi.',
  'swap':
'Exchanges the values of x and y.',
  'dup':
'Duplicates the value x in y (lifting the stack).',
  'clr':
'Clears all values in the stack.',
  'rd':
'Rolls the contents of stack down one postition.',
  'ru':
'Rolls the contents of stack up one position.',
  'cs':
'Copy the sign of y to the x value.',
  'rand':
'Generate a random number between 0 and 1.',
  'fix':
'Set the # of decimal places displayed by the value that follows.',
  'show':
'Display the full value of x.',
  'sto':
'Save the value in x to a named register (STO <ab0>).',
  'rcl':
'Recall the value in a register (RCL <ab0>).',
  'mem':
'Display the storage registers and their contents.',
  'clrg':
'Clears the contents of all the registers.',
  'lbl':
'Designates a label name to follow (LBL <a>).',
  'exc':
'Executes a program starting at a label (EXC <a>).',
  'gsb':
'Branches program to subroutine a label (GSB <a>).',
  'gto':
'Sends program to a label (GTO <a>)',
  'rtn':
'Designates end of program or subroutine.',
  'pse':
'Pauses program and displays current result.',
  'nop':
'Takes up a space. Does nothing else.',
  'x=0?':
'Tests if x equals 0. Skips the next 2 objects if false.',
  'x!=0?':
'Tests if x does not equal 0. Skips the next 2 objects on false.',
  'x>0?':
'Tests if x is greater than 0. Skips the next 2 objects on false.',
  'x<0?':
'Tests if x is less than 0. Skips the next 2 objects on false.',
  'x>=0?':
'Tests if x is greater than or equal to 0. Skips the next 2 objects on false.',
  'x<=0?':
'Tests if x is less than or equal to 0. Skips then next 2 objects on false.',
  'x=y?':
'Tests if x is equal to y. Skips the next 2 objects on false.',
  'x!=y?':
'Tests if x is not equal to y. Skips the next 2 objects on false.',
  'x>y?':
'Tests if x is greater than y. Skips the next 2 objects on false.',
  'x<y?':
'Tests if x is less than y. Skips the next 2 objects on false.',
  'x>=y?':
'Tests if x is greater than or equal to y. Skips the next 2 objects on false.',
  'x<=y?':
'Tests if x is less than or equal to y. Skips the next 2 objects on false.',
  'del':
'Delete a register by name (DEL x).',
  '^':
'Raises y(base) to the x(exponent).',
  'quit':
'Exits the program and saves the contents of the stack and registers.',
  'ptr':
'Returns the value of the command line\'s pointer.',
  'dh':
'Converts h.mmss to decimal equivalent.',
  'hms':
'Convert decimal time to h.mmss.',
  'prog':
'Print programming memory.',
  'gcd':
'Greatest common divisor of x & y.',
  'cls':
'Clear screen of any messages.',
  'edit':
'Enter programming memory.',
  'scut':
'Displays keyboard shortcuts.',
  'scutadd':
'Add a keyboard shortcut: scutadd <shortcut> <operator/value>',
  'scutdel':
'Delete a keyboard shortcut: scutdel <shortcut>',
  'help':
'I\'m being repressed! Also: followed by an operator gives detailed info on \
that operator, while \'op\' will list all operators.'
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
  return(stack)

# push a number onto the bottom of the stack raising everything
# else up.
def push(num):
  """Push a number onto the stack."""
  i = len(stack) - 1
  while i:
    stack[i] = stack[i-1]
    i -= 1
  stack[0] = float(num)

# pull a number off the bottom of stack and drop everything down one.
def pull():
  """Pull a number off the stack."""
  i   = 0
  num = stack[i]
  while i < len(stack) - 1:
    stack[i] = stack[i+1]
    i += 1
  return(num)

# pull the program data from the text file.
# apparently, 'for line in...' closes the file for you
#   after reading the last line.  Thanks, Python!
def program_data(progf):
  """Copies .txt file to memory."""
  if os.path.exists(progf):
    prog = ""
    for line in open(progf, 'r', encoding='utf-8'):
      line = line.split('#')[0]
      prog += line
    prog = prog.split()
    return(prog)

# This is the guts of the whole thing...
def calc(stack, mem, prog_listing, decimal_places):
  """Processes all input."""

  incr = True # in case you want to stop the pointer (n) from incrementing

  print(f"\x1b[2J{YLW}Type 'help' for documentation.")
  print(f"Type 'help op' for a list of available operators.")
  print(f"Type 'help <oper>' (without braces) for specifics on an operator.")
  print(f"Type 'scut' for a list of keyboard shortcuts.{WHT}\n")

  while True: # loop endlessly until a break statement

    n = 0 # token iterator

    # Display the stack and prompt for input:
    reg = ['x:', 'y:', 'z:', 't:'] # our stack labels
    i = len(reg) - 1 # index of the last label
    while i: # prints out 'y', 'z' and 't'
      print(reg[i], f'{stack[i]:,.{decimal_places}f}')
      i -= 1
    # Now display x and prompt for the command line:
    # note: cmd_ln is the input line as a Python list.
    cmd_ln = input(f'{reg[i]} {stack[0]:,.{decimal_places}f} ').split()

    # clear the screen; probably shouldn't be here.
    # this works in linux on my chromebook.
    # remove if you're a history buff.
    if os.name == 'posix': #not sure this will work on other systems
      print(f'\x1b[2J') # clear the screen.

    try:
      if cmd_ln[n].lower() in ['quit', 'exit', 'close']:
        fh = open(memnam, 'w', encoding='utf-8')
        fh.write(str(stack) + '\n' + \
            str(mem) + '\n' + \
            str(decimal_places) + '\n' + \
            str(kbsc))
        fh.close()
        # this print statement is a test and should be
        # deleted when done testing.
        # print(f'\n' + \
        #        str(stack) + '\n' + \
        #        str(mem) + '\n' + \
        #        str(prog_listing) + '\n' + \
        #        __file__ + '\n' + \
        #        memnam + '\n' + \
        #        prognam + '\n')
        break
    except IndexError: # just pressing ENTER is the same as 'dup'
      x = pull()
      push(x)
      push(x)

    # Execute the command line
    #
    while n < len(cmd_ln):
      try:
        # make the space delimited string object a token:
        token = cmd_ln[n].lower()
        #
        # substitute a type shortcut for its operator.
        if token in kbsc.keys():
          token = kbsc[token]
        # shift not needed...
        if token in kbsc2.keys():
          token = kbsc2[token]
        #
        # convoluted way to figure out if the token is a number:
        if token[0].isdigit() or (token[0] in '.+-' and len(token) > 1):
          push(float(token))
        #
        # if it doesn't satisfy the above criteria for being a number
        # it's assumed to be an operator.
        #
        # binary operators:
        #
        # addition:
        elif token == '+':
          x = pull()
          y = pull()
          push(x+y)
        #
        # subtraction:
        elif token == '-':
          x = pull()
          y = pull()
          push(y-x)
        #
        # multiplication:
        elif token == '*':
          x = pull()
          y = pull()
          push(x*y)
        #
        # division:
        elif token == '/':
          x = pull()
          y = pull()
          push(y/x)
        #
        # raise y to the x:
        elif token == '^':
          x = pull()
          y = pull()
          push(y**x)
        #
        # x root of y:
        elif token == 'xroot':
          x = pull()
          y = pull()
          push(y**(1/x))
        #
        # rectangular to polar conversion:
        elif token == 'r>p':
          x = pull()
          y = pull()
          push(math.atan2(y,x)) # angle
          push(math.hypot(x,y)) # magnitude
          print(f'{YLW}Angle(y): {WHT}{math.atan2(y,x):.4f}{YLW};' + \
                f' Magnitude(x): {WHT}{math.hypot(x,y):.4f}\n')
        #
        # polar to rectangular conversion:
        elif token == 'p>r':
          x = pull() # magnitude
          y = pull() # angle
          push(x * math.sin(y)) # y
          push(x * math.cos(y)) # x
        #
        # x percent of y (leaves y in the stack):
        elif token == '%':
          x = pull()
          y = pull()
          push(y)
          push((x/100)*y)
        #
        # percentage change from y to x (leaves y in the stack):
        elif token == '%c':
          x = pull()
          y = pull()
          push(y)
          push((x/y-1)*100)
        #
        # combinations of x into y:
        elif token == 'cnr':
          x = pull()
          y = pull()
          push(math.factorial(y)/(math.factorial(x)\
              *math.factorial(y-x)))
        #
        # permutations of x in y:
        elif token == 'pnr':
          x = pull()
          y = pull()
          push(math.factorial(y)/math.factorial(y-x))
        #
        # unary operators:
        #
        # square root of x:
        elif token == 'sqrt':
          x = pull()
          push(math.sqrt(x))
        #
        # square of x:`
        elif token == 'sq':
          x = pull()
          push(x**2)
        #
        # e to the x (e^x):
        elif token == 'e':
          x = pull()
          push(math.exp(x))
        #
        # natural log of x:
        elif token == 'ln':
          x = pull()
          push(math.log(x))
        #
        # Base of 10 raised to x:
        elif token == 'tx':
          x = pull()
          push(10**x)
        #
        # base 10 log of x:
        elif token == 'log':
          x = pull()
          push(math.log10(x))
        #
        # inverse of x (1/x):
        elif token == 'inv':
          x = pull()
          push(1/x)
        #
        # change sign of x:
        elif token == 'chs':
          x = pull()
          push(x * -1)
        #
        # absolute value of x:
        elif token == 'abs':
          x = pull()
          push(math.fabs(x))
        #
        # ceiling of x:
        elif token == 'ceil':
          x = pull()
          push(float(math.ceil(x)))
        #
        # floor of x:
        elif token == 'floor':
          x = pull()
          push(float(math.floor(x)))
        #
        # factorial of x:
        elif token == '!':
          x = pull()
          push(float(math.factorial(int(x))))
        #
        # gamma of x:
        elif token == 'gamma':
          x = pull()
          push(math.gamma(x))
        #
        # fractional portion of x:
        elif token == 'frac':
          x = pull()
          push(math.modf(x)[0])
        #
        # integer portion of x:
        elif token == 'int':
          x = pull()
          push(math.modf(x)[1])
        #
        # round a number to the display value
        elif token == 'rnd':
          x = pull()
          push(round(x, decimal_places))
        #
        # convert a float into a ratio (y/x):
        elif token == 'ratio':
          x = pull()
          push(float(x.as_integer_ratio()[0]))
          push(float(x.as_integer_ratio()[1]))
        #
        # trig functions:
        #
        # self explanatory?
        elif token == 'sin':
          x = pull()
          push(math.sin(x))
        elif token == 'cos':
          x = pull()
          push(math.cos(x))
        elif token == 'tan':
          x = pull()
          push(math.tan(x))
        elif token == 'asin':
          x = pull()
          push(math.asin(x))
        elif token == 'acos':
          x = pull()
          push(math.acos(x))
        elif token == 'atan':
          x = pull()
          push(math.atan(x))
        elif token == 'sinh':
          x = pull()
          push(math.sinh(x))
        elif token == 'cosh':
          x = pull()
          push(math.cosh(x))
        elif token == 'tanh':
          x = pull()
          push(math.tanh(x))
        elif token == 'asinh':
          x = pull()
          push(math.asinh(x))
        elif token == 'acosh':
          x = pull()
          push(math.acosh(x))
        elif token == 'atanh':
          x = pull()
          push(math.atanh(x))
        #
        # arctangent of y/x (considers signs of x & y):
        elif token == 'atan2':
          x = pull()
          y = pull()
          push(math.atan2(y,x))
        #
        # hypotenuse of x & y:
        elif token == 'hyp':
          x = pull()
          y = pull()
          push(math.hypot(x,y))
        #
        # angle conversions:
        #
        # convert angle in degrees to radians:
        elif token == 'rad':
          x = pull()
          push(math.radians(x))
        #
        # convert angle in radians to degrees:
        elif token == 'deg':
          x = pull()
          push(math.degrees(x))
        #
        # metric/imperial conversions:
        #
        # convert length in centimeters to inches:
        elif token == 'in':
          x = pull()
          push(x/2.54)
        #
        # convert length in inches to centimeters:
        elif token == 'cm':
          x = pull()
          push(x*2.54)
        #
        # convert volume in litres to gallons:
        elif token == 'gal':
          x = pull()
          push((((x*1000)**(1/3)/2.54)**3)/231)
        #
        # convert volume in gallons to litres:
        elif token == 'ltr':
          x = pull()
          push(x*231*2.54**3/1000)
        #
        # convert weight in kilograms to lbs.:
        elif token == 'lbs':
          x = pull()
          push(x*2.204622622)
        #
        # convert weight in lbs. to kilograms:
        elif token == 'kg':
          x = pull()
          push(x/2.204622622)
        #
        # convert temperature from celsius to fahrenheit:
        elif token == 'c>f':
          x = pull()
          push(x*9/5+32)
        #
        # convert temperature from celsius to fahrenheit:
        elif token == 'f>c':
          x = pull()
          push((x-32)*5/9)
        #
        # convert h.mmss to a decimal value:
        elif token == 'dh':
          x = pull()
          h = int(x)
          m = int((x-h)*100)
          s = (round((x-h-(m/100))*10000,4))
          print(f'{YLW}{h}h:{m}m:{s}s{WHT}\n')
          push(h+(m/60)+(s/(60**2)))
        #
        # convert decimal time value to h.mmss:
        elif token == 'hms':
          x = pull() #3.755555555555555
          h = int(x) #3
          m = int((x*60) % 60)
          s = (round((x*3600) % 60,4))
          print(f'{YLW}{h}h:{m}m:{s}s{WHT}\n')
          push(h+m/100+s/10000)
        #
        # constant(s):
        #
        # the approximate value of pi:
        elif token == 'pi':
          push(math.pi)
        #
        # the approximate value of 2pi:
        elif token == 'tau':
          push(math.tau)
        #
        # greatest common divisor of x & y:
        elif token == 'gcd':
          x=pull()
          y=pull()
          push(math.gcd(int(x),int(y)))
        #
        # stack manipulators:
        #
        # swap x and y:
        elif token == 'swap':
          x = pull()
          y = pull()
          push(x)
          push(y)
        #
        # duplicate the value in x:
        elif token == 'dup':
          x = pull()
          push(x)
          push(x)
        #
        # clear the contents of the stack:
        elif token == 'clr':
          i = len(stack)
          while i:
            push(0.0)
            i -= 1
        #
        # 'roll' the stack down one:
        elif token == 'rd':
          i = 0
          t = stack[0]
          while i < len(stack) - 1:
            stack[i] = stack[i+1]
            i += 1
          stack[i] = t
        #
        # 'roll' the stack up one:
        elif token == 'ru':
          i = len(stack) - 1
          t = stack[i]
          while i:
            stack[i] = stack[i-1]
            i -= 1
          stack[i] = t
        #
        # miscellaneous:
        #
        # copy the sign of y to x:
        elif token == 'cs':
          x = pull()
          y = pull()
          push(y)
          push(math.copysign(x, y))
        #
        # return the value of the cmd line pointer
        elif token == 'ptr':
          push(float(n))
        #
        # generate a pseudo random number between 0 and 1:
        elif token == 'rand':
          push(random.random())
        #
        # set the number of decimals to the following value:
        elif token == 'fix':
          n += 1
          decimal_places = abs(int(cmd_ln[n]))
        #
        # show the whole value of the x register:
        elif token == 'show':
          x = pull()
          push(x)
          print(f'{YLW}{x:,}{WHT}\n')
        #
        # store x in a named 'register':
        elif token == 'sto':
          x = pull()
          push(x)
          n += 1
          mem[cmd_ln[n]] = x
        #
        # recall a value from 'memory':
        elif token == 'rcl':
          n += 1
          if cmd_ln[n] in mem.keys():
            push(mem[cmd_ln[n]])
          else:
            print(f'{RED}Register {WHT}{cmd_ln[n]}{RED} not found.{WHT}\n')
        #
        # delete a register:
        elif token == 'del':
          n += 1
          if cmd_ln[n] in mem:
            del mem[cmd_ln[n]]
          else:
            print(f'{RED}Register {WHT}{cmd_ln[n]}{RED} not found.{WHT}\n')
        #
        # display the contents of the storage regsiters:
        elif token == 'mem':
          print(f'{YLW}Storage registers:\n{str(mem)[1:-1]}{WHT}\n')
        #
        # display keyboard shortcuts:
        elif token == 'scut':
          print(f'{YLW}' + \
          f'Keyboard shortcuts:\n{str(kbsc)[1:-1].replace(": ",":")}{WHT}\n')
        #
        # add a shortcut to the list:
        elif token == 'scutadd':
          n += 1
          key = cmd_ln[n]
          n += 1
          val = cmd_ln[n]
          kbsc[key] = val
        #
        # delete a shortcut from the list:
        elif token == 'scutdel':
          n += 1
          key = cmd_ln[n]
          if key in kbsc:
            del kbsc[key]
          else:
            print(f'{RED}Shortcut {WHT}{key}{RED} not found.{WHT}\n')
        #
        # clear the contents of the storage registers:
        elif token == 'clrg':
          mem.clear()
          print(f'{YLW}Registers cleared.{WHT}\n')
        #
        # clear the screen of unwanted messages:
        elif token == 'cls':
          print(f'\x1b[2J')
        #
        # Programming related commands
        #
        # label: only purpose is to be ignored,
        # along with the token immediately after it.
        # EXC, GSB, GTO & RTN will use labels.
        elif token == 'lbl':
          n += 1 # now points to the labels descriptor
          # the n+=1 at the end will step over the label's
          # descriptor
        #
        # executes the program starting at label x:
        # Things got a lot more complicated when I decided
        # to allow basic calculator style programming...
        elif token == 'exc':
          # setup a few things to allow jumping around
          n += 1
          x = 0
          pdict = {}
          # build dict of labels in the format: {name: location}
          while x < len(prog_listing):
            if prog_listing[x].lower() == 'lbl':
              x += 1
              pdict[prog_listing[x]] = x
            x += 1
          # if the label exists replace the command line
          # and set the pointer (n) to the start.
          if cmd_ln[n] in pdict:
            lbl_nam = cmd_ln[n]
            lbl_rtn = []
            cmd_ln = prog_listing
            n = pdict[lbl_nam]
          else:
            print(f'{RED}Label {WHT}{cmd_ln[n]}{RED} not found.{WHT}\n')
        #
        # gosub routine:
        # This tosses the calling location onto the lbl_rtn
        # stack we created in 'EXC' so we'll know where to
        # return to.
        elif token == 'gsb':
          n += 1
          lbl_rtn.append(n)
          n = pdict[cmd_ln[n]]
        #
        # goto routine:
        # Just like 'gsb' but no need to go back.
        elif token == 'gto':
          n += 1
          n = pdict[cmd_ln[n]]
        #
        # return - for end of program or subroutine:
        # if called by a 'gsb' will go back to the token
        # following the 'gsb'.  Otherwise it will end the
        # program.
        elif token == 'rtn':
          if len(lbl_rtn):
            n = lbl_rtn.pop()
          else:
            n = 0
            cmd_ln = ['nop', 'nop']
        #
        # pauses a running program
        elif token == 'pse':
          input(f"\n{YLW}Press ENTER to continue.{WHT}")
        #
        # does nothing.  Short for "No OPeration"
        elif token == 'nop':
          pass
        #
        # tests: lots of tests. No branching, just jumping if
        # false. if true, continues execution at the the next
        # token, otherwise: skip the next two(2) tokens.
        #
        # test if x is equal to 0:
        elif token == 'x=0?':
          x = pull()
          push(x)
          if x: # same as "if not x=0"
            n += 2
        #
        # test if x in not equal to 0:
        elif token == 'x!=0?':
          x = pull()
          push(x)
          if not x:
            n += 2
        #
        # test if x is greater than 0:
        elif token == 'x>0?':
          x = pull()
          push(x)
          if not x > 0:
            n += 2
        #
        # test if x is less than 0:
        elif token == 'x<0?':
          x = pull()
          push(x)
          if not x < 0:
            n += 2
        #
        # test if x is greater than or equal to 0:
        elif token == 'x>=0?':
          x = pull()
          push(x)
          if not x >= 0:
            n += 2
        #
        # test if x is less than or equal to 0:
        elif token == 'x<=0?':
          x = pull()
          push()
          if not x <= 0:
            n += 2
        #
        #test if x is equal to y:
        elif token == 'x=y?':
          x = pull()
          y = pull()
          push(y)
          push(x)
          if x!=y:
            n += 2
        #
        # test if x is NOT equal to y:
        elif token == 'x!=y?':
          x = pull()
          y = pull()
          push(y)
          push(x)
          if x==y:
            n += 2
        #
        # test if x is greater than y:
        elif token == 'x>y?':
          x = pull()
          y = pull()
          push(y)
          push(x)
          if not x > y:
            n += 2
        #
        #test if x is less than y:
        elif token == 'x<y?':
          x = pull()
          y = pull()
          push(y)
          push(x)
          if not x < y:
            n += 2
        #
        # test if x is greater than or equal to y:
        elif token == 'x>=y?':
          x = pull()
          y = pull()
          push(y)
          push(x)
          if not x >= y:
            n += 2
        #
        # test if x is less than or equal to y:
        elif token == 'x<=y?':
          x = pull()
          y = pull()
          push(y)
          push(x)
          if not x <= y:
            n += 2
        #
        # dump the program listing:
        elif token == 'prog':
          print(f"{YLW}Programming space:")
          print(f' '.join(i for i in prog_listing).replace('RTN','RTN\n'),f"{WHT}")
        #
        # edit the program data file:
        elif token == 'edit':
          if os.name == 'posix':
            os.system("vim {}".format(os.path.splitext(__file__)[0]+'.txt'))
            prog_listing = program_data(prognam) # reload
            print(f'\x1b[2J')

        #
        # print the version number:
        elif token == 'version':
            print(f'{RED}{version}{WHT}\n')
        #
        # display help (in a convoluted fashion, but this *is*
        # an exercise in learning how to program).
        elif token == 'help':
          n += 1
          if n < len(cmd_ln):
            if cmd_ln[n].lower() == 'op': # get a list of operators
              s = str(op_dict.keys())[11:-2]
              s = s.replace("'","")
              s = s.replace(",","")
              s = s.upper()
              s = s.split()
              s.sort()
              print(f"{YLW}Type 'help xxx' for specific help on an operator.")
              print(f"Available operators are:")
              for x in s:
                print(f'\'{x}\'', end=' ')
              print(f"\nOperators are not case sensitive.")
              print(f"Type 'scut' for shortcut keys.{WHT}\n")
            # look up help on a particular operator:
            elif cmd_ln[n].lower() in op_dict:
              print(f'{YLW}{cmd_ln[n].upper()}',end='')
              if cmd_ln[n] in kbsc.values():
                # vvv Clean this up. vvv
                print(f'({list(kbsc.keys())[list(kbsc.values()).index(cmd_ln[n])]})',end="")
              print(f': {str(op_dict[cmd_ln[n].lower()])}{WHT}\n')
            else:
              print(f"{RED}Operator {WHT}{cmd_ln[n]}{RED} not found.{WHT}\n")
          else: # just print the __doc__ string from the top
            print(f'{YLW}{__doc__}{WHT}')
        #
        # it didn't match any token above, check to see if it's
        # a register. If not, assume it's an error.
        #
        # note that if you name a register the same as a command
        # you'll need to use 'rcl'.
        else:
          if cmd_ln[n] in mem.keys():
            push(mem[cmd_ln[n]])
          else:
            print(f"{RED}Invalid Operator: {WHT}{token}\n")
        #
        # increment the command line pointer to the next token
        # and go back through this loop:
        if incr == True:
          n += 1
        incr = True

      # exception list
      except ValueError:
        print(f"{RED}Value error:{WHT}\n", token)
        break
      except ZeroDivisionError:
        print(f"{RED}Division by zero error{WHT}\n")
        break
      except OverflowError:
        print(f"{RED}Overflow error:{WHT}\n", token)
        break
      except IndexError:
        print(f"{RED}Index Error:{WHT}\n", token)
      except KeyError:
        print(f"{RED}Key Error:{WHT}\n", token)


# if the mem file exists use it instead of initstack()
if os.path.exists(memnam):
  fh=open(memnam, 'r', encoding='utf-8')
  stack = ast.literal_eval(fh.readline())
  mem = ast.literal_eval(fh.readline())
  decimal_places = int(ast.literal_eval(fh.readline()))
  kbsc = ast.literal_eval(fh.readline())
  fh.close()
else:
  stack = initstack(stack_size)
  decimal_places = 4
  mem = {}
  kbsc = {'#': 'rand', 'a': '+', 'b': 'xroot', 'c': 'chs',
      'd': '/', 'f': '!', 'g': 'gamma', 'h': 'help', 'i': 'inv',
      'j': 'rad', 'k': 'scut', 'l': 'ln', 'm': 'mem', 'n': 'frac',
      'o': '^', 'p': 'prog', 'q': 'exc', 'r': 'sqrt', 's': '-',
      't': 'sq', 'u': 'deg', 'v': 'int', 'w': 'show', 'x': '*',
      'y': 'swap', 'z': 'abs'}

# if a program file exists dump its contents into memory.
# we'll 'import' its contents into memory whether we use it or not
if os.path.exists(prognam):
  prog_listing = program_data(prognam)
else:
  prog_listing = []

if __name__ == '__main__':
  calc(stack, mem, prog_listing, decimal_places)

# Addenda.
# Differences between this and the HP15c include:
#   No complex number support (though it would be easy to implement).
#   No GOTO <line #> (no line numbers to go to).
#   No matrix support.
#   No DSE or ISG commands (they're useful if space is limited... it's not).
#   No integration.
#   No statistical functionality.
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
# To do:
#   Help text needs lots of improvement
#   Keyboard shortcuts display needs cleaning up (:1099):
