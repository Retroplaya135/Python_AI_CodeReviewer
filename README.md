# Code Reviewer

A minimalistic Python static code analysis tool for clean and maintainable code.

## Installation
1. Install the required package:
   ```bash
   pip install pycodestyle
   ```

## Usage
1. Run the script:
   ```bash
   python Codereviewer.py
   ```

2. Example Input:
   ```python
   sample_code = '''
   import math, os

   class TestClass:
       def __init__(self):
           pass

   def foo():
       print("hello");print("world")
       eval("1+1")
       try:
           return
           print("unreachable")
       except:
           pass
   '''
   ```

3. Example Output:
   ```plaintext
   - Multiple imports on one line at line 1.
   - Class 'TestClass' naming style.
   - Print statement at line 6.
   - Eval usage at line 7.
   - Unreachable code after return in line 9.
   - Empty block at line 13.
   ```