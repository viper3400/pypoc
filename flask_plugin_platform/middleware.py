from __future__ import annotations

from collections.abc import Callable, Iterable

StartResponse = Callable[[str, list[tuple[str, str]], tuple[object, ...] | None], object]
WsgiApp = Callable[[dict[str, object], StartResponse], Iterable[bytes]]


class PrefixMiddleware:
    def __init__(self, app: WsgiApp, url_prefix: str) -> None:
        self._app = app
        self._url_prefix = "" if url_prefix == "/" else url_prefix

    def __call__(self, environ: dict[str, object], start_response: StartResponse) -> Iterable[bytes]:
        script_name = str(environ.get("SCRIPT_NAME", ""))
        path_info = str(environ.get("PATH_INFO", ""))

        environ["SCRIPT_NAME"] = f"{script_name}{self._url_prefix}"

        if self._url_prefix and path_info.startswith(self._url_prefix):
            stripped = path_info[len(self._url_prefix) :]
            environ["PATH_INFO"] = stripped or "/"

        return self._app(environ, start_response)
