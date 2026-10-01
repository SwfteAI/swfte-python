"""Authenticated SDK transport: redirects never resend credentials or bodies."""

from typing import Any, Callable

import requests

from .exceptions import APIError


def _send(sender: Callable[..., requests.Response], *args: Any, **kwargs: Any) -> requests.Response:
    # Requests retains POST bodies on 307/308, even across origins. Dropping
    # Authorization on that redirect does not protect prompts, files or audio.
    kwargs["allow_redirects"] = False
    response = sender(*args, **kwargs)
    if 300 <= response.status_code < 400:
        try:
            body = response.json()
        except ValueError:
            body = response.text
        response.close()
        raise APIError("Redirect refused: HTTP {}".format(response.status_code),
                       status_code=response.status_code, body=body)
    return response


def request(*args: Any, **kwargs: Any) -> requests.Response:
    return _send(requests.request, *args, **kwargs)


def get(*args: Any, **kwargs: Any) -> requests.Response:
    return _send(requests.get, *args, **kwargs)


def post(*args: Any, **kwargs: Any) -> requests.Response:
    return _send(requests.post, *args, **kwargs)


def put(*args: Any, **kwargs: Any) -> requests.Response:
    return _send(requests.put, *args, **kwargs)


def patch(*args: Any, **kwargs: Any) -> requests.Response:
    return _send(requests.patch, *args, **kwargs)


def delete(*args: Any, **kwargs: Any) -> requests.Response:
    return _send(requests.delete, *args, **kwargs)
