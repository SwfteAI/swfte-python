"""Credential-safe exception boundaries; ordinary successful values stay intact."""

import functools
import inspect
import json
import re
from enum import Enum
from urllib.parse import quote, quote_plus


def redact_diagnostic(value, credential):
    """Detach exception diagnostics, including requests' request/response fields."""
    literals = {credential, json.dumps(credential, ensure_ascii=False)[1:-1],
                json.dumps(credential)[1:-1], quote(credential, safe=""), quote_plus(credential)}
    literals.update(quote(item, safe="") for item in list(literals))
    patterns = []
    for literal in sorted(filter(None, literals), key=len, reverse=True):
        escaped = re.escape(literal)
        escaped = re.sub(r"%([0-9A-Fa-f]{2})", lambda match: "%" + "".join(
            "[{}{}]".format(char.lower(), char.upper()) if char.lower() in "abcdef" else char
            for char in match.group(1)), escaped)
        patterns.append(re.compile(escaped))

    # A short credential can be part of the usual marker itself.
    marker = "*" if any(literal and literal in "[REDACTED]" for literal in literals) else "[REDACTED]"

    def text(item):
        for pattern in patterns:
            item = pattern.sub(marker, item)
        return item

    seen = {}

    def copy(item, depth=0):
        if isinstance(item, str):
            return text(item)
        if isinstance(item, bytes):
            result = item
            for literal in literals:
                if literal:
                    result = result.replace(literal.encode("utf-8"), marker.encode("utf-8"))
            return result
        if isinstance(item, Enum):
            return item if not isinstance(item.value, str) or text(item.value) == item.value else text(item.value)
        if item is None or isinstance(item, (int, float, bool)):
            return item
        if callable(item):
            return "[callable omitted]"
        if id(item) in seen:
            return seen[id(item)]
        if depth > 32 or len(seen) >= 5000:
            return "[diagnostic omitted]"
        if isinstance(item, dict):
            result = {}
            seen[id(item)] = result
            for key, child in item.items():
                result[copy(key, depth + 1)] = copy(child, depth + 1)
            return result
        if isinstance(item, (list, tuple, set, frozenset)):
            result = []
            seen[id(item)] = result
            result.extend(copy(child, depth + 1) for child in item)
            if isinstance(item, tuple):
                return tuple(result)
            if isinstance(item, (set, frozenset)):
                return type(item)(result)
            return result
        if isinstance(item, BaseException):
            try:
                result = type(item).__new__(type(item))
            except Exception:
                result = RuntimeError()
            seen[id(item)] = result
            BaseException.__init__(result, *copy(item.args, depth + 1))
            for key, child in vars(item).items():
                setattr(result, text(key), copy(child, depth + 1))
            cause = item.__cause__
            if cause is None and not item.__suppress_context__:
                cause = item.__context__
            result.__cause__ = copy(cause, depth + 1)
            result.__context__ = None
            result.__traceback__ = None
            result.__suppress_context__ = True
            return result
        try:
            state = vars(item)
            result = object.__new__(type(item))
        except (TypeError, AttributeError):
            return "[diagnostic omitted]"
        seen[id(item)] = result
        for key, child in state.items():
            setattr(result, text(key), copy(child, depth + 1))
        return result

    return copy(value)


def credential_safe(cls):
    """Explicitly protect a resource's raised errors, retaining its public API.

    Raise outside the except block: the original error must not become an
    implicit context carrying unsanitized headers or response text.
    """
    def protect(method):
        def key_of(instance):
            owner = getattr(instance, "_client", getattr(instance, "client", instance))
            credential = getattr(owner, "api_key", "")
            return credential if isinstance(credential, str) else ""

        if inspect.isgeneratorfunction(method):
            @functools.wraps(method)
            def stream(instance, *args, **kwargs):
                credential = key_of(instance)

                def iterate():
                    safe = None
                    try:
                        yield from method(instance, *args, **kwargs)
                    except Exception as error:
                        safe = redact_diagnostic(error, credential)
                    if safe is not None:
                        raise safe from safe.__cause__
                return iterate()
            return stream

        @functools.wraps(method)
        def call(instance, *args, **kwargs):
            credential = key_of(instance)
            safe = None
            try:
                return method(instance, *args, **kwargs)
            except Exception as error:
                safe = redact_diagnostic(error, credential)
            raise safe from safe.__cause__
        return call

    for name, method in list(vars(cls).items()):
        if inspect.isfunction(method) and not name.startswith("__"):
            setattr(cls, name, protect(method))
    return cls
