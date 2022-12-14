from collections.abc import MutableMapping
from re import compile
from types import LambdaType

from .helpers import flat
from .paths import as_path


class MatcherResult(object):
    def __init__(self):
        self.contexts = []

    @property
    def is_match(self):
        return len(self.contexts) > 0

    def add_contexts(self, contexts):
        self.contexts.extend(c for c in contexts if c.is_match)

    def analyse_contexts(self):
        if any(len(c.delayed_matchers) > 0 for c in self.contexts):
            print(
                "WARNING: some matcher generators where not executed due to missing variables"
            )
            for c in self.contexts:
                for bc in c.delayed_matchers:
                    missing_vars = set(bc.matcher.vars) - set(c.bindings)
                    code = bc.matcher.fun.__code__
                    file = code.co_filename
                    line = code.co_firstlineno
                    print(
                        f' * generator misses variables {missing_vars} to be executed ("{file}", L{line})'
                    )

    @property
    def bindings(self):
        return [c.bindings for c in self.contexts]

    def __str__(self):
        return f"<{self.is_match} - {self.bindings}>"

    def __bool__(self):
        return self.is_match


class Context(MutableMapping):
    def __init__(self, truth=True):
        self.bindings = {}
        self._is_match = truth
        self.truth = truth
        self.delayed_matchers = []

    def __getitem__(self, key):
        return self.bindings[key]

    def __setitem__(self, key, value):
        self.bindings[key] = value
        ctx = []
        for gencontext in tuple(self.delayed_matchers):
            if gencontext.can_execute(self):
                ctx.extend(gencontext.execute(self))
                self.delayed_matchers.remove(gencontext)
        if any(not c.is_match for c in ctx):
            self.is_match = property(lambda self: False)

    def __delitem__(self, key):
        del self.bindings[key]

    def __iter__(self):
        return iter(self.bindings)

    def __len__(self):
        return len(self.bindings)

    @property
    def is_match(self):
        return self._is_match is self.truth

    @is_match.setter
    def is_match(self, value):
        self._is_match = value

    def copy(self):
        instance = self.__class__(self.truth)
        instance.bindings.update(self.bindings)
        instance.delayed_matchers.extend(self.delayed_matchers)
        return instance


class Matcher(object):
    def as_matcher(self):
        return self

    @property
    def is_collection_matcher(self):
        return False

    @property
    def is_list_wildcard(self):
        return False

    def match(self, obj):
        result = MatcherResult()
        contexts = self.match_context(obj, Context())
        result.add_contexts(contexts)
        result.analyse_contexts()
        return result

    def __or__(self, right):
        return OrMatcher(self, as_matcher(right))

    def save_as(self, alias):
        return SaveNodeMatcher(alias, self)

    def __matmul__(self, alias):
        return SaveNodeMatcher(alias, self)

    def __eq__(self, other):
        return self.match(other)


class extended(object):
    def __init__(self, o):
        self.o = o
        self.result = None

    def __eq__(self, other):
        self.result = other == self.o
        return self.result

    def __iter__(self):
        return iter([self.o, self.result])


class SaveNodeMatcher(Matcher):
    def __init__(self, alias, matcher):
        self.alias = alias
        self.matcher = matcher

    @property
    def is_collection_matcher(self):
        return self.matcher.is_collection_matcher

    @property
    def is_list_wildcard(self):
        return self.matcher.is_list_wildcard

    def match_context(self, obj, context):
        context[self.alias] = obj
        return self.matcher.match_context(obj, context)


class IdentityMatcher(Matcher):
    def __init__(self, value):
        self.value = value

    def match_context(self, obj, context):
        context.is_match = obj is self.value
        return [context]


class LiteralMatcher(Matcher):
    def __init__(self, value):
        self.value = value

    def match_context(self, obj, context):
        context.is_match = obj == self.value
        return [context]


class LogicalMatcher(Matcher):
    ...


class NotMatcher(Matcher):
    def __init__(self, matcher):
        self.matcher = matcher

    @property
    def is_collection_matcher(self):
        return self.matcher.is_collection_matcher

    def match_context(self, obj, context):
        truth = not context.truth
        contexts = self.matcher.match_context(obj, context)
        if not contexts:
            return [context]
        contexts = [c for c in contexts if c.is_match is truth]
        for c in contexts:
            c.is_match = not truth
        return contexts


class OrMatcher(Matcher):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def match_context(self, obj, context):
        contexts = self.left.match_context(obj, context)
        if any(c.is_match for c in contexts):
            return contexts
        return self.right.match_context(obj, context)


class KeyValueMatcher(object):
    def match_context(self, obj, context):
        context.is_match = True
        new_contexts = [context]
        for path, matcher in self.properties.items():
            results = []
            for context in new_contexts:
                if matcher.is_collection_matcher:
                    cpy = context.copy()
                    results.extend(matcher.match_context(path.resolve_from(obj), cpy))
                else:
                    results.extend(
                        flat(
                            [
                                matcher.match_context(o, context.copy())
                                for o in path.resolve_from(obj)
                            ]
                        )
                    )
            new_contexts = [c for c in results if c.is_match]
        return new_contexts


class ObjectMatcher(KeyValueMatcher, Matcher):
    def __init__(self, cls, properties=None, subclassmatch=False):
        self.properties = properties
        self.cls = cls
        self.subclassmatch = subclassmatch

    def match_context(self, obj, context):
        sametype = (
            isinstance(obj, self.cls)
            if self.subclassmatch
            else obj.__class__ == self.cls
        )
        if not sametype:
            context.is_match = False
            return [context]
        return super().match_context(obj, context)

    @property
    def properties(self):
        return self._properties

    @properties.setter
    def properties(self, properties):
        if properties is None:
            self._properties = {}
        else:
            props = {as_path(k): as_matcher(v) for k, v in properties.items()}
            self._properties = props


class DictMatcher(KeyValueMatcher, Matcher):
    def __init__(self, d):
        self.properties = {
            as_path(k, dictkey=True): as_matcher(v) for k, v in d.items()
        }


class LambdaBasedMatcher(Matcher):
    __self__ = "__self__"

    def __init__(self, fun):
        self.fun = fun
        self.vars = [*fun.__code__.co_varnames[: fun.__code__.co_argcount]]
        if self.__self__ in self.vars:
            self.has_self = True
            self.vars.remove(self.__self__)
        else:
            self.has_self = False

    def match_context(self, obj, context):
        try:
            kwargs = {k: context[k] for k in self.vars}
        except KeyError:
            context.delayed_matchers.append(BoundMatcherGenerator(self, context, obj))
            return [context]
        if self.has_self:
            kwargs[self.__self__] = obj
        return self.execute(obj, context, kwargs)


class MatcherGenerator(LambdaBasedMatcher):
    def execute(self, obj, context, kwargs):
        return as_matcher(self.fun(**kwargs)).match_context(obj, context)


class ConditionalMatcher(LambdaBasedMatcher):
    def execute(self, obj, context, kwargs):
        context.is_match = self.fun(**kwargs)
        return [context]


class BoundMatcherGenerator(object):
    def __init__(self, matcher, context, self_object):
        self.matcher = matcher
        self.context = context
        self.self_object = self_object

    def can_execute(self, context):
        return all(x in context for x in self.matcher.vars)

    def execute(self, context):
        return self.matcher.match_context(self.self_object, context.copy())


class RegexMatcher(Matcher):
    def __init__(self, regexp, label=None):
        self.regexp = compile(regexp)
        self.label = label

    def __rshift__(self, label):
        self.label = label
        return self

    def match_context(self, obj, context):
        result = self.regexp.match(obj)
        context.is_match = result is not None
        if self.label:
            context[self.label] = result
        return [context]


class RangeMatcher(Matcher):
    def __init__(self, range):
        self.range = range

    def match_context(self, obj, context):
        context.is_match = obj in self.range
        return [context]


class WildcardMatcher(Matcher):
    def __init__(self, alias):
        self.alias = alias

    @property
    def is_anonymous(self):
        return self.alias == "_"

    def match_context(self, obj, context):
        if self.is_anonymous:
            context.is_match = True
            return [context]
        if self.alias in context:
            context.is_match = context[self.alias] == obj
            return [context]
        context.is_match = True
        context[self.alias] = obj
        return [context]


class ListWildcardMatcher(WildcardMatcher):
    @property
    def is_list_wildcard(self):
        return True

    @property
    def is_anonymous(self):
        return not self.alias or super().is_anonymous


class SequenceMatcher(Matcher):
    def __init__(self, sequence):
        self.sequence = [as_matcher(m) for m in sequence]

    @property
    def is_collection_matcher(self):
        return True

    def match_context(self, obj, context):
        results = []
        try:
            cursor = Cursor(self.sequence, obj, context)
        except Exception:
            return results
        while cursor.has_next:
            found_combination = False
            while not found_combination and cursor.has_next:
                found_combination = self.match_next(obj, cursor, context)
            if found_combination:
                results.extend(cursor.contexts_for_current_pattern())
                cursor.forward = False
        return results

    def match_next(self, collection, cursor, context):
        contexts = [c.copy() for c in cursor.contexts_for_current_pattern()]
        if cursor.forward:
            if cursor.pattern_cursor >= cursor.pattern_size:
                if cursor.subject_cursor >= cursor.subject_size:
                    return True
                cursor.set_backward()
                cursor.decrement_pattern_cursor()
                cursor.clear_contexts_for_current_pattern()
        else:
            if cursor.pattern_cursor >= cursor.pattern_size:
                cursor.decrement_pattern_cursor()
                cursor.decrement_subject_cursor()
        if cursor.pattern_cursor < 0 or cursor.subject_cursor < 0:
            cursor.has_next = False
            return False
        pattern = self.sequence[cursor.pattern_cursor]
        if not pattern.is_list_wildcard:
            if cursor.forward and cursor.subject_cursor < cursor.subject_size:
                cursor.reset_has_next_current_pattern()
                cursor.clear_contexts_for_current_pattern()
                new_contexts = flat(
                    [
                        pattern.match_context(collection[cursor.subject_cursor], c)
                        for c in contexts
                    ]
                )
                if any(c.is_match for c in new_contexts):
                    cursor.set_has_next_current_pattern()
                    contexts = [c for c in new_contexts if c.is_match]
                    cursor.add_contexts_to_pattern(contexts)
                    cursor.increment_pattern_cursor()
                    cursor.increment_subject_cursor()
                else:
                    cursor.decrement_pattern_cursor()
                    cursor.set_backward()
            else:
                if cursor.subject_cursor < cursor.subject_size:
                    new_contexts = flat(
                        [
                            pattern.match_context(collection[cursor.subject_cursor], c)
                            for c in contexts
                        ]
                    )
                    if cursor.has_next_current_pattern() and any(
                        c.is_match for c in new_contexts
                    ):
                        contexts = [c for c in new_contexts if c.is_match]
                        cursor.reset_has_next_current_pattern()
                        cursor.add_contexts_to_pattern(contexts)
                        cursor.increment_pattern_cursor()
                        cursor.increment_subject_cursor()
                        cursor.set_forward()
                    else:
                        cursor.decrement_pattern_cursor()
                        cursor.decrement_subject_cursor()
                        cursor.set_backward()
                else:
                    cursor.decrement_pattern_cursor()
                    cursor.decrement_subject_cursor()
                    cursor.set_backward()
        else:
            if cursor.forward:
                cursor.lv_starts[cursor.pattern_cursor] = cursor.subject_cursor
                if cursor.pattern_cursor == (cursor.pattern_size - 1):
                    cursor.lv_lengths[cursor.pattern_cursor] = max(
                        cursor.subject_size - cursor.subject_cursor, 0
                    )
                else:
                    cursor.lv_lengths[cursor.pattern_cursor] = cursor.lv_min_lenghts[
                        cursor.pattern_cursor
                    ]
            else:
                cursor.lv_lengths[cursor.pattern_cursor] += 1
                cursor.set_forward()
                cursor.clear_contexts_for_current_pattern()
            length = cursor.lv_lengths[cursor.pattern_cursor]
            start = cursor.lv_starts[cursor.pattern_cursor]
            min = cursor.lv_min_lenghts[cursor.pattern_cursor]
            _max = cursor.lv_max_lenghts[cursor.pattern_cursor]

            if length > _max or (start + length) >= (cursor.subject_size + 1):
                cursor.subject_cursor = start
                cursor.set_backward()
                cursor.lv_lengths[cursor.pattern_cursor] = 0
                cursor.decrement_pattern_cursor()
                cursor.clear_contexts_for_current_pattern()
            else:
                subjects = collection[start : start + length]
                contexts = flat([pattern.match_context(subjects, c) for c in contexts])
                if any(c.is_match for c in contexts):
                    contexts = [c for c in contexts if c.is_match]
                    cursor.add_contexts_to_pattern(contexts)
                    cursor.increment_pattern_cursor()
                    cursor.subject_cursor = start + length
                else:
                    cursor.set_backward()
                    cursor.lv_lengths[cursor.pattern_cursor] = 0
                    cursor.decrement_pattern_cursor()
        return False


class Cursor(object):
    def __init__(self, matcher_sequence, sequence, original_context):
        self.subject_size = len(sequence)
        self.pattern_size = len(matcher_sequence)
        self.lv_starts = [None] * self.pattern_size
        self.lv_lengths = [None] * self.pattern_size
        self.lv_min_lenghts = [None] * self.pattern_size
        self.lv_max_lenghts = [None] * self.pattern_size
        self.subject_cursor = 0
        self.pattern_cursor = 0
        self.wildcard_pos = [
            i for i, m in enumerate(matcher_sequence) if m.is_list_wildcard
        ]
        self.num_nonlistwildcard = self.pattern_size - len(self.wildcard_pos)
        self.has_next = True
        self.forward = True
        self.orig_context = original_context
        self.contexts = [[] for _ in range(self.pattern_size)]
        self.pattern_has_next = [True] * self.pattern_size
        for i in self.wildcard_pos:
            self.lv_min_lenghts[i] = 0
            self.lv_max_lenghts[i] = self.subject_size - self.num_nonlistwildcard
            self.lv_starts[i] = 0
            self.lv_lengths[i] = 0

    def add_contexts_to_pattern(self, contexts):
        self.contexts[self.pattern_cursor].extend(contexts)

    def clear_contexts_for_current_pattern(self):
        index = self.pattern_cursor
        if index < 0:
            return
        self.contexts[index].clear()

    def contexts_for_current_pattern(self):
        index = self.pattern_cursor - 1
        if index < 0:
            return [self.orig_context]
        return self.contexts[index]

    def decrement_pattern_cursor(self):
        self.pattern_cursor -= 1

    def decrement_subject_cursor(self):
        self.subject_cursor -= 1

    def has_next_current_pattern(self):
        return self.pattern_has_next[self.pattern_cursor]

    def increment_pattern_cursor(self):
        self.pattern_cursor += 1

    def increment_subject_cursor(self):
        self.subject_cursor += 1

    def reset_has_next_current_pattern(self):
        self.pattern_has_next[self.pattern_cursor] = True

    def set_backward(self):
        self.forward = False

    def set_forward(self):
        self.forward = True

    def set_has_next_current_pattern(self):
        self.pattern_has_next[self.pattern_cursor] = False


def as_matcher(obj):
    if isinstance(obj, str):
        if obj.startswith("@"):
            return WildcardMatcher(obj[1:])
        if obj.startswith("*"):
            return ListWildcardMatcher(obj[1:])
    if isinstance(obj, bool):
        return IdentityMatcher(obj)
    if obj is None or isinstance(obj, (int, float, str)):
        return LiteralMatcher(obj)
    if obj is Ellipsis:
        return ListWildcardMatcher("")
    if isinstance(obj, list):
        return SequenceMatcher(obj)
    if isinstance(obj, dict):
        return DictMatcher(obj)
    if isinstance(obj, LambdaType):
        return MatcherGenerator(obj)
    if isinstance(obj, range):
        return RangeMatcher(obj)
    if isinstance(obj, type):
        return ObjectMatcher(obj, {})
    return obj.as_matcher()


cond = ConditionalMatcher
regex = RegexMatcher
is_ = IdentityMatcher
