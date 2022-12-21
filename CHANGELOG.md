# CHANGELOG

## 0.4.0

### Features

* Add support for classes with `__slots__`

### Fixes

* Fix issue with matcher wrappers and collections. When a container matcher (`SaveNodeMatcher` or `NotMatcher`) is used, it needs to be considered as a collection matcher only if the matcher it wrapps is a collection matcher.


### Misc.

* More tests

## 0.3.0

### Features

* Add support for logical "or" matching
* Add support/compatiblity with Python's pattern-matching syntax

## 0.2.0

### Features

* Add support for matcher generators (syntax is directly bound to lambdas)
* Add support for conditional matcher using lambdas
* Add support for regex matchers
* Add support for range matchers

## 0.1.0

Initial version of `iguala`:

### Features

* support for matching literals
* support for matching objects
* support for matching dictionary
* support for paths
    * direct
    * recursive
* support for negative matcher (first implementation)
* support for wildcards
* support for wildcards for sequences
* first version of documentation (in `README.md`)