# Whitespace
* Use spaces instead of tabs for indentation.
* Use four spaces for each level of syntactically significant indenting.
* Lines should be 120 characters in length or less.
* Continuations of long expressions onto additional lines should be indented by four extra spaces from their normal indentation level.
* In a file, functions and classes should be separated by two blank lines.
* Don't put spaces around
    * List indexes
    * Function calls
    * Keyword argument assignments
* Put one space
    * Before and after variable assignments.
    * After colon separating `key: value` in dictonary.
    * After comma separating items in list, dict, tuple.

# Naming
* Functions, variables, and attributes should be in `lowercase_underscore` format.
* Protected instance attributes should be in `_leading_underscore` format.
* Private instance attributes should be in `__double_leading_underscore`
format.
* Classes and exceptions should be in `CapitalizedWord` format.
* Module-level constants should be in `ALL_CAPS` format.
* Instance methods in classes should use `self` as the name of the first parameter (which refers to the object).
* Class methods should use `cls` as the name of the first parameter (which refers to the class).

# Expressions and Statements
* Don't check for empty values (like [] or '') by checking the length 
`if len(somelist) == 0)`. Use `if not somelist` and assume empty values implicitly evaluate to False.
* The same thing goes for non-empty values (like [1] or 'hello'). The statement `if somelist` is implicitly True for non-empty values.
* If you want to check if a value is None. Use `if var is None`. Do not do `if not var`.it will return True even if var value is 0. 
* Always put import statements at the top of a file.
* Never user `import *`.
* Imports should be in sections in the following order: standard library modules, thirdparty modules, your own modules.

```python
# Standard library modules
import datetime
import sys

# Thirdparty modules
from django.core.cache import caches
from django.db.models import Q

# App imports
from ner_v2.detectors.numeral.number import number_detection

```

* Python's syntax makes it all too easy to write single-line expressions that are overly complicated and difficult to read. Move complex expressions into helper functions, especially if you need to use the same logic repeatedly.
* Prefer using List comprehensions instead of map and filter. Its easier to read as they don't require extra lambda expressions.
```python
# list comprehension
even_squares = [x**2 for x in a if x % 2 == 0]

# map and filter
even_squares = list(map(lambda x: x**2, filter(lambda x: x % 2 == 0, a)))
```
* Dictonary also support comprehension expressions
```python
names = ['James', 'Jack', 'Alley']
names_len = {a: len(a) for a in names }
```
* List comprehensions with more than two expressions are very difficult to read and should be avoided.
* List comprehensions can cause problems for large inputs by using too much
memory. Use Generator expressions to avoid memory issues by producing outputs one at a time as an iterator.

```python
# List comprehension
values = [len(x) for x in open('/tmp/my_file.txt')]

# Generator expression
it = (len(x) for x in open('/tmp/my_file.txt'))
print next(it)
```

# Functions
* Use None to specify dynamic default parameters. Default argument values are evaluated only once per module load, which usually happens when a program starts up.

```python
# Do not do this
def log(message, when=datetime.now()):
    print('%s: %s' % (when, message))

log('Hi')
sleep(1)
log('Hello')

>>
2017-11-15 21:10:10.371432: Hi
2017-11-15 21:10:10.371432: Hello

# Do this
def log(message, when=None):
    when = datetime.now() if when is None else when
    print('%s: %s' % (when, message))
    
log('Hi')
sleep(1)
log('Hello')

>>
2017-11-15 21:10:10.371432: Hi
2017-11-15 21:10:11.371432: Hello
```

* Using None for default argument values is especially important when the arguments are `mutable` i.e dict or list.

```python
def decode(data, default={}):
    try:
        return json.loads(data)
    except ValueError:
        return default
        
foo = decode('bad data')
foo['stuff'] = 5
bar = decode('also bad')
bar['meep'] = 1
print('Foo:', foo)
print('Bar:', bar)

>>
Foo: {'stuff': 5, 'meep': 1}  # Expected Foo: {'stuff': 5}
Bar: {'stuff': 5, 'meep': 1}  # Expected Bar: {'meep': 1}
```
You'd expect two different dictionaries, each with a single key and value. But modifying one seems to also modify the other as they are using same dictionary object.

```python
def decode(data, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(data)
    except ValueError:
        return default
        
foo = decode('bad data')
foo['stuff'] = 5
bar = decode('also bad')
bar['meep'] = 1
print('Foo:', foo)
print('Bar:', bar)
>>>
Foo: {'stuff': 5}
Bar: {'meep': 1}
```

* You can enforce clarity in function call using keyword arguments.
```python
def send_automated_reply(msg, should_type, send_athena):
    # create msg
    if should_type:
        # send typing indicator
    
    if send_athena:
        # send msg to athena
        
send_automated_reply(msg, True, False)
```
The problem is that it's easy to confuse the position of the two Boolean arguments that control sending typing indicator and sending msg to athena. This can easily cause bugs that are hard to trackdown. To avoid this condition we should use keyword arguments.

```python
def send_automated_reply(msg, should_type=True, send_athena=True):
    # create msg
    if should_type:
        # send typing indicator
    
    if send_athena:
        # send msg to athena
        
send_automated_reply(msg, should_type=True, send_athena=False)
```

# Non Pythonic vs Pythonic
* Use range function to loop over a series of numbers
```python
# Non Pythonic
for i in [0, 1, 2, 3, 4, 5]:
    print i*i

# Pythonic
for i in xrange(0, 6): # python 2
    print i*i

for i in range(0, 6):  # python 3
    print i*i
```

* Looping over a collection
```python
# Non Pythonic
names = ['james', 'jack', 'alex', 'martin']
# Forward looping
for i in range(len(names)):
    print names[i]
# Reverse looping
for i in range(len(names)-1, -1, -1):
    print names[i]
# Print indeces with names
for i in range(len(names)):
    print i, '--->', names[i]

# Pythonic
names = ['james', 'jack', 'alex', 'martin']
# Forward looping
for name in names:
    print name
# Reverse looping of names
for name in reversed(names):
    print name
# Print indeces with names
for i, name in enumerate(names):
    print i, '---->', name
```
* looping over two collections together
```python
names = ['james', 'jack', 'alex', 'martin']
ages = [23, 34, 54]

# Non pythonic
n = min(len(names), len(ages))
for i in range(n):
    print names[i], '--->', ages[i]

# Pythonic
for name, age in zip(names, ages):
    print name, '---->', age
```
* Use named tuples instead of tuples
```python
# Non Pythonic
colour_heuristic = (170, 0.1, 0.6)
if colour_heuristic[1] > 0.5:
	print 'that is too bright'
if colour_heuristic[2] > 0.5:
	print 'wow this is light'

# Pythonic
from collections import namedtuple

colour = namedtuple('Colour', ['hue', 'saturation', 'luminosity'])
colour_heuristic = colour(170, 0.1, 0.6)

if colour_heuristic.saturation > 0.5:
	print 'that is too bright'
if colour_heuristic.luminosity > 0.5:
	print 'wow this is light'
```
* Use properties instead of getters methods
```python
# Non Pythonic
class NetworkElement(object):
    def get_name():
        return self.name
    def get_ipaddr():
        return self.ip_addr
ne = NetworkElement()
network_name =  ne.get_name()
ip_addr = ne.get_ipaddr()
create_connection(network_name, ip_addr)

# Pythonic
class NetworkElement(object):
    @property
    def name():
        return self.name
    @property
    def ip_addr():
        return self.ip_addr

ne = NetworkElement()
create_connection(ne.name, ne.ip_addr)
```
* Use `defaultdict` to assign default values for keys in dict

```python
names = ['jack', 'alex', 'martin', 'ruby', 'alex']

# Non Pythonic
name_count = {}
for name in names:
    if name not in name_count:
        name_count[name] = 0
    name_count[name] += 1

# Pythonic
name_count = defaultdict(int)
for name in names:
    name_count[name] += 1
```
* Unpacking of sequence
```python
# Non Pythonic
p = 'Jack', 23, 'jack@gmail.com'
name = p[0]
age = p[1]
email = p[2]

# Pythonic
name, age, email = 'Jack', 23, 'jack@gmail.com'
```
* use `join()` for concatenation of string

```python

# Non pythonic
names = ['jack', 'alex', 'martin', 'ruby', 'alex']
s = ''
for name in names:
    s += ', ' + name

# Pythonic
s =  ', '.join(names)
```

* Use `Deque` for updating sequence. Deques are a generalization of stacks and queues. Deques have O(1) speed for appendleft() and popleft() while lists have O(n) performance for insert(0, value) and pop(0).

```python
# Non Pythonic
names = ['jack', 'alex', 'martin', 'ruby', 'alex']
del names[0]
names.pop[0]
names.insert(0, 'mark')

# Pythonic
from collections import deque
names =  deque(['jack', 'alex', 'martin', 'ruby', 'alex'])
del names[0]
names.popleft(0)
names.appendleft('mark')
```

* Factor-out your setup logic and teardown logic with context managers. You can write your custom context manager using `__enter__()` and `__exit__()` functions. [Read more](https://jeffknupp.com/blog/2016/03/07/python-with-context-managers/)

```python
# Non Pythonic
f = open('data.txt')
try:
    data = f.read()
finally:
    f.close()

# Pythonic
with open('data.txt') as f:
    data = f.read()
```





















