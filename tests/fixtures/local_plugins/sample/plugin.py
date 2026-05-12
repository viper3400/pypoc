from __future__ import annotations

from flask import Blueprint

blueprint = Blueprint("local_sample", __name__, url_prefix="/local-sample")


@blueprint.get("/")
def index() -> str:
    return "local sample"


PLUGIN = {
    "id": "local-sample",
    "name": "Local Sample",
    "description": "Local scan fixture plugin",
    "version": "0.1.0",
    "blueprint": blueprint,
    "menu_entry": {
        "label": "Local Sample",
        "icon": "scan",
        "path": "/local-sample/",
    },
}
