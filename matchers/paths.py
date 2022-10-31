from .helpers import IdentitySet, flat


class ObjectPath(object):
    def as_path(self):
        return self

    @property
    def is_recursive(self):
        return False


class DictPath(ObjectPath):
    def __init__(self, path):
        self.path = path

    def resolve_from(self, obj):
        try:
            return flat(obj.get(self.path, []))
        except AttributeError:
            return []


class DirectPath(ObjectPath):
    def __init__(self, path):
        self.path = path

    def resolve_from(self, obj):
        try:
            return flat(getattr(obj, self.path, []))
        except AttributeError:
            return []


class ComposedPath(ObjectPath):
    def __init__(self, paths):
        self.paths = paths

    def resolve_from(self, obj):
        tmp = [obj]
        for path in self.paths:
            copy = [*tmp]
            if not path.is_recursive:
                tmp.clear()
            for intermediate in copy:
                try:
                    result = path.resolve_from(intermediate)
                except Exception:
                    result = []
                tmp.extend(result)
        return tmp


class RecursivePath(ObjectPath):
    def _resolve_from(self, obj, seen, resolved):
        direct_objects = []
        o = flat(resolved)
        res = [x for x in o if x is not None and x not in seen]
        direct_objects.extend(res)
        seen |= res
        if obj not in seen:
            seen.add(obj)
        direct_objects.extend(
            flat([self._resolve_from(x, seen) for x in direct_objects])
        )
        return direct_objects

    def resolve_from(self, obj):
        res = self._resolve_from(obj, IdentitySet())
        return res

    @property
    def is_recursive(self):
        return True


class NamedRecursivePath(RecursivePath):
    def __init__(self, path):
        self.path = path

    def _resolve_from(self, obj, seen):
        o = self.path.resolve_from(obj)
        return super()._resolve_from(obj, seen, o)


class ChildrenRecursivePath(RecursivePath):
    def __init__(self):
        ...

    def _resolve_from(self, obj, seen):
        direct_objects = []
        try:
            visit = vars(obj).items()
        except TypeError:
            try:
                visit = obj.items()
            except AttributeError:
                return []
        for _, v in visit:
            direct_objects.extend(super()._resolve_from(obj, seen, v))
        return direct_objects


def as_path(s, dictkey=False):
    dict_cls = DictPath if dictkey else DirectPath
    if ">" in s:
        paths = tuple(as_path(p, dictkey=dictkey) for p in s.split(">"))
        return ComposedPath(paths)
    if isinstance(s, ObjectPath):
        return s
    if not isinstance(s, str):
        return s.as_path()
    if s == "*":
        return ChildrenRecursivePath()
    if isinstance(s, str):
        if s[-1] == "*":
            return NamedRecursivePath(as_path(s[:-1], dictkey=dictkey))
        if s[-1] == "+":
            return ComposedPath(
                (
                    as_path(s[:-1], dictkey=dictkey),
                    NamedRecursivePath(as_path(s[:-1], dictkey=dictkey)),
                )
            )

    return dict_cls(s)
