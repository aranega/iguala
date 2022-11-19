# Iguala: non-linear pattern matching for Python's objects, or a regexp-like for objects

Iguala - from spanish "igual a", "equivalent to" or "iguala", "make it equivalent" - is a non-linear pattern matcher for Python's objects.
It is heavily inpired by query in graphs, term rewriting ([tom](http://tom.loria.fr/) or pattern matching in [rascal](https://www.rascal-mpl.org/)) and structural pattern matching.
The goal of this project is to provide an easy to use, but powerful, library for matching complex objects.
Patterns are defined in a declarative way and can match complex objects and extract data from them.
They support:

* logical composition ("or"),
* wildcards and variables,
* the reuse of variable accross patterns to express equality,
* wildcards and variables in collections,
* negative patterns,
* pattern/matchers compositions,
* composite and recursive paths,
* yield all combinations found when a pattern matches against an object,
* matching over dictionary the same way as for classes/objects (more or less),
* conditional matchers (you can capture variable and/or the tested object to test a condition),
* matcher generators (you can capture variables and/or the tested object to produce a new matcher),
* regex matchers,
* compatibility with the `match` of Python (using few tricks, documented below).

More operators/matchers will arrive

This implementation is derived from [MoTion](https://github.com/alesshosry/MoTion/), implemented in Smalltalk and based on work initiated with [Aless Hosry](https://github.com/alesshosry/) during her PhD.

## Quick example

Here is the example of a pattern that will check if an object is an instance of `MyObject` with the same value for `att1` and `att2`.

NOTE: in this document, the term `matcher` and `pattern` are used to refer to the same thing, but a matcher matches a single small entity while a pattern defines a composition of matchers (or a single matcher).

```python
# we consider that "MyObject" is an already known type
# and "instance" and instance of it with att1 = att2 = 4 and name = 'foo'
from iguala import match, is_not

pattern = match(MyObject) % {  # must be an instance of MyObject
    "att1": "@value",  # with att1 stored in "value"
    "att2": "@value",   # and att2 with the same value as the one from att1
    "name": is_not("bar") @ "name" # and name is not "bar", store the name in "name"
}
print(pattern.match(instance))
# displays: <True: [{'value': 4, 'name': 'foo'}]>

# An equivalent Python code would be:
if type(instance) == MyObject and instance.att1 == instance.att2 and instance.name != "bar":
    value = instance.att1
    name = instance.name
```

## Installation

```sh
pip install iguala
```

## Syntax, operators and special characters

For each pattern/matcher, there is a set of operators and special characters that controls the way data are matched.
For a most comprehensive way of how to use all of this, please refer to the sections belows that present small tutorials about how to match values against objects and dicts.
Here is a list of all currently supported operators.

### Paths operators for objects and dictionaries

Patterns over objects and dictionary supports the sub-patterns.
Each sub-patterns are connected by a path.
A path represent the way to navigate from a pattern to others.

There is different kind of paths:

* **named/direct paths**: they express a direct navigation through a relationship,
    * creating a direct path is done by using directly the name of the relation, e.g: `foo` or `bar`.
* **composed paths**: they express the navigation of different relationships one after each other,
    * creating a composed path is done by using the `>` operator between two names, e.g: `foo>bar` to express, 'first navigate `foo` then `bar`.
* **named recursive paths**: they express the recursive navigation of a relationship (unbound depth),
    * creating a named rec. path is done by using the `*` or `+` operator after a name, e.g: `foo*` expresses that `foo` needs to be followed 0 or many times and `foo+` expresses that `foo` needs to be followed 1 or many times.
* **children recursive paths**: they express the recursive navigation of all "instance variable" of an object.
    * creating a children rec. path is done by using `*` alone, e.g: `*` means all the "children" (the instance variable of the object/keys of the dict) and their children.

Those operators can be composed with `>`.
For examples:

* `bar>foo>*` means "`bar` then `foo` then all the children recursively"
* `*>foo` means "all the children recursively then `foo`" (if `foo` exists for each object)
* `child*>name` means "follow `child` recursively and get `name` each time"
* ...

### Wildcards/variables

Wildcards/variables stores information and checks if the same information appears many times.

* variable are strings starting by `@`, e.g: `@x`, `@name`...
* single `@` alone is considered as an anonymous variable, it is useful to ensure the presence of something without storing any data.
* variable starting by `*` represent a collection of elements in sequences: e.g: `*x` or `*y`, they are used in list/sequence matching (see sections below).
* `...` is used as an anonymous variable for collections of elements in sequences.


### Matchers/pattern operators

There is few pattern operators.

* `match(...)` with a type as parameter matches exactly a type, e.g: `match(A) % {}` means, match an instance of `A` (but not subclasses).
* `~` used in front of an object matcher expresses "and all its subclasses", e.g: `~match(object) % {}` means, match an instance of `object` or from its subclasses.
* `%` with a dictionnary on its right expresses the properties of an object, e.g: `match(A) % {'name': 'foo'}` means, match an instance of `A` where the `name` equals `foo`.
* `@` stores a data into a dedicated name, e.g: `match(A) % {'name': 'foo'} @ 'inst'` means, match an instance of `A` where the `name` equals `foo` and store the instance of `A` in `inst` for further usage.
* `is_not(...)` expresses a negation (needs to be imported `from iguala import is_not`), e.g: `match(A) % {'name': is_not('foo')}`, means match an instance of `A` where the `name` is not equal to `foo`,
* `regex(...)` expresses a regular expression matcher (needs to be imported `from iguala import regex`). The regex to match needs to be passed as a string, e.g: `match(A) % {'name': regex('[A-Z].*')}`, means match an instance of `A` where the `name` matches the regex `[A-Z].*`.
    * This matcher supports an additional operator `>>` that is used to store the matching result for further usage. This mecomes really handy to get matched groups (especially if named match group are used), e.g: `match(A) % {'name': regex('[A-Z].*') >> 'match_result'}` will store the "match" object obtained during the regex matching operation under the label `match_result`. This variable will be accessible as all variables, in the result procuded by `iguala`.
    * The same behavior as describe above can be achieved without using the `>>` by passing an extra argument to `regex(...)`, e.g: `match(A) % {'name': regex('[A-Z].*', label='match_result')}`. Using the operator or not is a matter of taste, the effect is exactly the same.
* `range(...)`, if you use the `range(...)` constructor (from builtins), a special "range matcher" is created, e.g: `match(A) % {'x': range(0, 5)}` means, match an instance of `A` where `x` is in the range `[0..4]`.
* `|` expresses a logical "or" between two patterns, e.g: `match(A) % {'name': is_not(m('foo') | 'bar')}`, means match an instance of `A` where `name` is neither `foo` nor `bar`. In this example, `m` is a renaming of the `as_matcher` function made this way: `from iguala import as_matcher as m`.

### Collections patterns

Here is a list of some examples of patterns that can be applied to collections:

* `[]`, means empty collection
* `[3]` means a collection with only one value: `3`
* `[3, 'r']` means a collection with only two values: `3` and `'r'`
* `[3, ...]` means `3` is first element
* `[..., 3]` means `3` is last element
* `[..., '@x']` means a last element stored in `x`
* `[..., '@x', ...]` means an element stored in `x` (will match all the element of a collection one after each others)
* `[..., '@x', '@y']` means the two last element stored in `x` and `y`
* `[..., '@x', ..., '@y']` means an element stored in `x` with the last element stored in `y`
* `[..., '@x', ..., '@x']` means a collection that have an element that is equal to the last element
* `['@x', ..., '@x']` means a collection where the first and the last element are the same
* `[..., '@x', '@x', ..]` means a collection that have two times the same element that follow each other
* `[..., '@x', ..., is_not('@x'), ..]` means a collection where two elements that are not the same (a collection where all elements are different)
* `is_not([..., '@x', ..., is_not('@x'), ...])` means a collection where there is no elements that are not the same (a collection where all elements are the same)

### Lambda based matchers

Lambdas are used to express patterns over captured variables:

* `lambda VAR1, VAR2, ....: SOMETHINGS WITHS VARS` is a matcher generator.
Matcher generators uses captured variable to generate new matchers that are executed when all necessary variables have been captured, e.g: `match(A): {'x': '@x', 'y': lambda x: x + 1}` means, match an instance of `A` that have an attribute `x` and an attribute `y` that is equals to `x + 1`.
* `cond(lambda ....)` is a condition matcher (needs to be imported `from iguala import cond`).
Condition matchers uses captured variable to execute a function and use the result as matching result. Consequently, the return type of the function must be a boolean, e.g: `match(A): {'x': '@x', 'y': cond(lambda x, __self__: x ==  __self__ + 1)}` means, match an instance of `A` that have an attribute `x` and an attribute `y` that is equals to `x + 1`.
* `__self__` is a meta-variable that can be passed as arguments of the matcher generator or conditional matcher. This variable resolves to the object currently matched.

Matcher generators and conditional matchers also works with sequence matchers, negative matchers, range matcher, regex matcher...etc.
Here is some examples:

* `[..., '@x', lambda x: x + 1, ...]` means a collection where one element is followed by its successor.
* `[..., '@x', is_not(lambda x: x + 1), ...]` means a collection where one element is not followed by its successor.
* `is_not([..., '@x', is_not(lambda x: x + 1), ...])` means a collection where there is no element that is not followed by its successor (a collection that is sorted).
* `match(A) % {'x': '@x', 'y': lambda x: range(0, x + 1)}` means match an instance of `A` which has an `x` value and a `y` value contained in the `[0..x]` interval.


NOTE: Argument names of the function used for the matcher generator or the conditional matcher have to match the name of variables defined in the pattern.
If other names are used, `iguala` will ignore the matcher, but will generate a warning message stating what are the missing variables and their positions in the pattern.

## Walkthrough - Draw me a pattern on an Object

To see how to match information from an object, let's create three of two kind.
We will consider that they already exists somewhere in memory.
We will then express patterns and see if those data (`a1`, `a2`, `b`) are matched by the patterns.

```python
from dataclasses import dataclass

@dataclass
class A(object):
    x: int
    y: int
    l: list[int]

@dataclass
class B(object):
    x: int

a1 = A(x=3, y=4, l=[1, 2, 2, 3, 4, 3, 5])
a2 = A(x=4, y=4, l = [2])
b = B(x=4)
```

Now let's define a first pattern.

```python
from iguala import match

# Simple pattern
pattern = match(A) % {}  # answers the question it's an instance of A?
```

This pattern will check if the data is actually an instance of `A`.
The `%` operator with the empty dictionnary after expresses the fact that we don't want to express any properties over `A`.

And now, we see if it matches:

```python
print(pattern.match(a1))
# displays: <True - [{}]>

print(pattern.match(a2))
# displays: <True - [{}]>

print(pattern.match(b))
# displays: <False - []>
```
No suprises, `a1` and `a2` are instances of `A` while `b` is not.

Let's now see if those objects are instances of `A` with an attribute `z` that equals 4, then if they own an attribute `x` equals to 4.

```python
pattern = match(A) % { 'z': 4 }  # is it an instance of A with 'z' == 4?

print(pattern.match(a1))  # and a2, b
# displays: <False - []>, they don't have 'z' properties

pattern = match(A) % { 'x': 4 }  # is it an instance of A with 'z' == 4?
print(pattern.match(a1))
# displays: <False - []>

print(pattern.match(a2))
# displays: <True - [{}]>
```

Now, let's deconstruct to get the value of `x`.
We will express in our pattern that the data should be an instance of `A` with an attribute `x` and that we want to store the value of `x` in a variable named `value`.

```python
pattern = match(A) % {  # is it an instance of A?
    'x': '@value'  # with an attribute "x"? (stored in "value")
}

result = pattern.match(a1)
print(result)
# displays: <True - [{'value': 3}]>
print(result.bindings[0]['value'])
# displays: 3

print(pattern.match(a2))
# displays: <True - [{'value': 4}]>
print(result.bindings[0]['value'])
# displays: 4
```

Each right side of the property dictionnary that starts with an `@` means that it's a variable.
If the name is found again in the pattern, then, it means that the data needs to have the same value for those variable in those positions.

Let's use that to check now if each data is an instance of `A` where `x` and `y` have the same value.

```python
pattern = match(A) % {  # is it an instance of A?
    'x': '@value'  # with an attribute "x"? (stored in "value")
    'y': '@value'  # with an attribute "y" with the same value as "x"
}

result = pattern.match(a1)
print(result)
# displays: <False - []>

print(pattern.match(a2))
# displays: <True - [{'value': 4}]>
```

Let's check now if we have an instance of `A` with a `2` in the collection `l`.

```python
pattern = match(A) % {  # is it an instance of A?
    'l': 2  # does "l" contains a 2?
}

print(pattern.match(a1))
# displays: <True - [{}, {}]>, there is two 2 in "l", so two combination, this information is returned by the matcher

print(pattern.match(a2))
# displays: <True - [{}]>, here there is only one 2 in "l"
```

Let's try more precise questions over the collection `l`:

```python
#
# Patterns over collections
#
pattern = match(A) % {  # is it an instance of A?
    'l': [2]  # does "l" contains only a 2?
}
print(pattern.match(a1))
# displays: <False: []>

print(pattern.match(a2))
# displays: <True: [{}]>


pattern = match(A) % {  # is it an instance of A?
    'l': [..., 2]  # does the last element of "l" is 2?
}
print(pattern.match(a1))
# displays: <False: []>

print(pattern.match(a2))
# displays: <True: [{}]>


pattern = match(A) % {  # is it an instance of A?
    'l': [..., '@value']  # does "l" has a last element?
}
print(pattern.match(a1))
# displays: <True: [{'value': 5}]>

print(pattern.match(a2))
# displays: <True: [{'value': 2}]>


pattern = match(A) % {  # is it an instance of A?
    'l': [..., '@value', '@value', ...]  # does "l" has two times the same element that follow each other?
}

print(pattern.match(a1))
# displays: <True: [{'value': 2}]>

print(pattern.match(a2))
# displays: <False: []>


pattern = match(A) % {  # is it an instance of A?
    'l': [..., '@value', ..., '@value', ...]  # does "l" has at least two times the same element?
}

print(pattern.match(a1))
# displays: <True - [{'value': 2}, {'value': 3}]>

print(pattern.match(a2))
# displays: <False: []>

pattern = match(A) % {  # is it an instance of A?
    'l': ["*l1", '@value', "*l2", '@value', "*l3"]  # does "l" has at least two times the same element? and store the collections around
}

print(pattern.match(a1))
# input for l was: [1, 2, 2, 3, 4, 3, 5]
# displays: <True - [
#    {'l1': [1], 'value': 2, 'l2': [], 'l3': [3, 4, 3, 5]},
#    {'l1': [1, 2, 2], 'value': 3, 'l2': [4], 'l3': [5]}
# ]>

```

Those are only few examples of what you can express over collections.
Obviously, it's possible to compose patterns and to express patterns elements in collections.

```python
from iguala import as_matcher

a3 = A(x=3, y=4, l=[])
col = [a1, a2, b, a3, b]

# does the collection contains two instances of A that have the same value for x
# and store the nodes in 'inst1' and 'inst2'
matcher = as_matcher(
    [...,
     match(A) % {'x': '@x'} @ 'inst1',
     ...,
     match(A) % {'x': '@x'} @ 'inst2',
     ...]
)

print(matcher.match(col))
# displays: <True - [{'inst1': A(x=3, y=4, l=[1, 2, 2, 3, 4, 3, 5]), 'x': 3, 'inst2': A(x=3, y=4, l=[])}]>
```
The `@` operator stores the results when a combination is found.
The example above shows us that there is only one combination where the data matches the pattern.

## Walkthrough - Draw me a pattern for an AST

This small tutorial shows how to match information from the Python's AST.
Please note that the library is not limited to Pyton's AST, but is supposed to work with any Python object.
This tutorial also suppose that you are used to the Python's AST.

In a first place, let's get a beautiful simple AST tree
```python
from ast import *

# What we parse
tree = parse("""
class A(object):
    Z = 0
    def __init__(self, x, y=3):
        self.x = x
        self.y = y
        self.z = 4

    class InnerCls(object):
        def __init__(self):
            self.inner_x = 1

class B(object):
    def __init__(self, w):
        if w > 0:
            self.w = w
        else:
            self. w = -1
""")
```

### Do we match something that has this shape?

Let's try to see if this module contains classes, which means: does the `tree` variable have the shape of a Module that contains Classes in this body?
Let's define the pattern to check that:

```python
# Pattern example 1
pattern = match(Module) % {  # we want a Module
    'body': match(ClassDef)  # that contains a ClassDef in 'body'
}
```
This pattern expresses that we want to match a `Module` using `match(Module)`, and in the `body` relation of this `Module`, must contain a `ClassDef`.
To express the content of a class instance, we use the `%` operator follows by a dictionnary where the key is the name of the relation and the value is against what the value needs to be matched.
The key is considered as a "path", we will see later what it means, while the value is a matcher.
In this case, `body` will yield a collection of ast nodes for `Module`.
Even if the path will resolve as a collection, as we use a simple matcher here, the semantic is equivalent to "contains".
Consequently, we can read this as does `body` contains a `ClassDef`.

Now that we have our matcher, we "execute it" against the `tree` object.

```python
result = pattern.match(tree)
print(result)
# displays: <True - [{}, {}]>
print(result.is_match)
# displays: True
print(result.contexts)
# displays: [<...Context object at 0x7f3736ae0280>, <...Context object at 0x7f3736ae0310>]
```

The `True - [{}, {}]` output means that yes, the pattern matches the data (`True`) and that it found exactly two combinations.
The matcher will always gives as result all the `Context` which are the equivalent of a matching combination.
We can conclude here that our `tree` variable is a `Module` that owns classes.

### Deconstruct/extract information from a pattern

Knowing if an object matches against a pattern is nice, but it's even better to be able to gather some data.
To have more details about what was matched by the pattern, we will introduce variables/wildcards.

```python
# Pattern example 2
pattern = match(Module) % {  # we want a Module
    'body': match(ClassDef) % {"name": "@name"} # that contains a ClassDef in 'body' and has a "name"
}

# Let's match the "tree"
result = pattern.match(tree)
print(result.is_match)  # True
print(result.bindings)
# displays: [{'name': 'A'}, {'name': 'B'}]
```

Obviously, we only have the classes that are directly under `body` in the module.
If we want all the modules, whereever there are defined, we will use instead the children recursive path operator.

NOTE: if you execute this code in IPython, it could be long, `parse(...)` seems to behave a little bit different in interactive environement.

```python
# Pattern exmaple 3
pattern = match(Module) % {  # we want a Module
    '*': match(ClassDef) % {"name": "@name"} # that contains a ClassDef in 'body' and has a "name"
}

# Let's match the "tree"
result = pattern.match(tree)
print(result.is_match)  # True
print(result.bindings)
# displays: [{'name': 'A'}, {'name': 'B'}, {'name': 'InnerCls'}]
```
The `*` performs a "wide first" traversal of all the data it encounters to give a feeling of "levels".
Consequently, `A` will always be followed by `B` here because they appear at the "same level".


Now, we will go further by trying to match a module that contains classes that contains a `__init__` method and the `__init__` method should have assignment with the form `self.XXX = SOMETHING`.

```python
from iguala import match

# defines the pattern we want to look for
# we want a Module
pattern = match(Module) % {
    # that owns in all its children, recursively (i.e: somewhere, at any depth)
    # a ClassDef instance
    '*': match(ClassDef) % {
        'name': '@name',  # where name is equivalent to "name" (store the node)
        'body': match(FunctionDef) % {  # that has a FunctionDef in body
            'name': '__init__',  # that is named "__init__"
            'body>*': match(Assign) % {  # and that has an Assign in it's body, somewhere (at any depth)
                'targets>value>id': 'self',  # where the target is "self"
                'targets>attr': '@attr',  # where the attr is equivalent to "attr" (store the node)
            }
        }
    }
}
result = matcher.match(tree)  # Find all combinations
print(result)
print(result.is_match)  # displays True
print(result.bindings)  # displays
# [{'name': 'A', 'attr': 'x'},
#  {'name': 'A', 'attr': 'y'},
#  {'name': 'A', 'attr': 'z'},
#  {'name': 'B', 'attr': 'w'},
#  {'name': 'B', 'attr': 'w'},
#  {'name': 'InnerCls', 'attr': 'inner_x'}]
```

And finally, as last pattern for this tutorial, we will try to match modules that have classes (at any level) which own an `__init__` method and that have instance variables assigned to a value that have the same name than the instance variable they are assigned to and which is coming from an argument of `__init__`.


```python
from iguala import match

# defines the pattern we want to look for
# we want a Module
pattern = match(Module) % {
    # that owns in all its children, recursively (i.e: somewhere, at any depth)
    # a ClassDef instance
    '*': match(ClassDef) % {
        'name': '@name',  # where name is equivalent to "name" (store the node)
        'body': match(FunctionDef) % {  # that has a FunctionDef in body
            'name': '__init__',  # that is named "__init__"
            'args>*': match(arg) % { '*': '@attr'},  # among the args, there is one that a field equals to "attr"
            'body>*': match(Assign) % {  # and that has an Assign in it's body, somewhere (at any depth)
                'targets>value>id': 'self',  # where the target is "self"
                'targets>attr': '@attr',  # where the attr is equivalent to "attr" (store the node)
                'value>id': "@attr",  # and the "id" of the "value" of the assignment as is equivalent to "attr"
            }
        }
    }
}
result = matcher.match(tree)  # Find all combinations
print(result)
print(result.is_match)  # displays True
print(result.bindings)  # displays
# [{"name": "A", "attr": "x"},
#  {"name": "A", "attr": "y"},
#  {"name": "B", "attr": "w"}]
```


## Make `iguala` works with Python's `match` syntax

Since version 3.9, Python owns a specific syntax for structural matching.
In this context, a pattern-matching in Python is a set of different pattern against which an object is tested.
The first pattern that answers "yes" to the question "do you match this object" triggers the execution of an indented block.
There is a kind of overlap between Python's pattern-matching and `iguala`.
Python's pattern-matching defines a syntax for: (1) defining structural patterns and (2) orchestring those patterns and test them one after the other on an input object (using different `case`).
`iguala` is an internal DSL to define structural and deep patterns only.
The patterns you can define with `iguala` are sometimes equivalent, but differs as they allow you to define patterns that returns many results.
Also, currently, there is no way of mixing definition of patterns between Python and `iguala`.
However, it's possible to use `iguala` patterns with the `case` syntax, but it requires a little trick.

### Defining a set of `iguala` patterns

The "problem" with Python's pattern-matching syntax is that you cannot reference an external variable.

```python
x = 3

match 4:
    case x:
        print("The variable x capture all values")
```

To overcome this "limitation" (it's not a limitation, but in our case, it can feel like it), we will define a class with all the patterns we want as class variable.

```python
from iguala import as_matcher as m

class Patterns(object):
    case1 = match(A) % {"x": "@x"}
    case2 = match(B) % {"y": 4}
    case3 = m([1, "*value", 3, ...])  # we want that the list starts with 1, then there is a bunch of 3 inside at any position
```

### Integrating `iguala` patterns with Python `case` syntax

Then, from here, we can pass them to the `case` syntax:

```python
instance = ...  # an existing object

match instance:
    case Patterns.case1 as x:
        print("I matched the first case", x)
    case Patterns.case2 as x:
        print("I matched the second case", x)
    case Patterns.case3 as x:
        print("I matched the third case", x)
    case 4:
        print("I matched the number 4")
    case _:
        print("I'm something else")
```

The `match` operation will try to see which of the `case` actually matches and, if it does, will store `instance` in `x` for the first 3 cases.

### Accessing the results/bindings of an `iguala` pattern

With the current version, there is no way of accessing all the bindings and results produced by an `iguala` matcher.
To do so, we need to cheat a little bit more and to ask for an `extended` match of `instance`.

```python
from iguala import extended

instance = ...  # an existing object

match extended(instance):
    case Patterns.case1 as x:
        o, result = x
        print("I matched the first case", result)
    case Patterns.case2 as x:
        o, result = x
        print("I matched the second case", result)
    case Patterns.case3 as x:
        o, result = x
        print("I matched the third case", result)
    case 4:
        print("I matched the number 4")
    case _:
        print("I'm something else")
```

This time, stored in `x` will not be the `instance` object, but a wrapper giving access to `o` the object that matched (`x.o`) and `result` the result of the match (`x.result`).
This wrapper that can be spread.
With that, in `result` we can access now all the combination that made that pattern match.

We can see that it is easy to integrate `iguala` patterns with Python's pattern-matching mecanism, providing thus a way to extend it for not so expensive.
The counterpart of this current solution is that if `extended(...)` is used, it's important to remember that the object that will be captured is a wrapper over the tested instance.

NOTE: the `extended` function is still a prototype and can be changed in further versions.
NOTE2: some more syntactic sugar could be added to ease the patterns set definition, but for a first PoC, it's sufficient.