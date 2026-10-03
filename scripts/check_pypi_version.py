"""Refuse publication unless PyPI proves the requested version is absent."""

import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, build_opener


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        return None


def _open_without_redirects(url, timeout):
    return build_opener(_NoRedirect()).open(url, timeout=timeout)


def require_unpublished(version, open_url=_open_without_redirects):
    url = "https://pypi.org/pypi/swfte-sdk/{}/json".format(quote(version, safe=""))
    try:
        with open_url(url, timeout=15) as response:
            status = response.getcode()
    except HTTPError as error:
        status = error.code
        error.close()
    except (URLError, TimeoutError, OSError) as error:
        raise RuntimeError("PyPI availability could not be verified; publication is blocked") from error
    if status != 404:
        if status == 200:
            raise RuntimeError("swfte-sdk {} already exists on PyPI; bump the version".format(version))
        raise RuntimeError("PyPI returned HTTP {}; publication is blocked".format(status))


if __name__ == "__main__":
    require_unpublished(sys.argv[1])
    print("PYPI_VERSION_ABSENT_404")
