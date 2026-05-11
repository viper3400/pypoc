from __future__ import annotations

from flask import Blueprint, render_template

blueprint = Blueprint(
    "notes",
    __name__,
    url_prefix="/notes",
    template_folder="templates",
    static_folder="static",
    static_url_path="/notes/static",
)


@blueprint.get("/")
def index() -> str:
    notes = [
        {"title": "Design", "body": "Keep host and apps separated."},
        {"title": "Deployment", "body": "Use an allowlist to deploy selected apps."},
    ]
    return render_template("notes/index.html", notes=notes)
