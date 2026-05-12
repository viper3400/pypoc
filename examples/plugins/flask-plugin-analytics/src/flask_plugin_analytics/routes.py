from __future__ import annotations

from flask import Blueprint, render_template

blueprint = Blueprint(
    "analytics",
    __name__,
    url_prefix="/analytics",
    template_folder="templates",
    static_folder="static",
    static_url_path="/analytics/static",
)


@blueprint.get("/")
def index() -> str:
    metrics = [
        {"label": "Active apps", "value": "2"},
        {"label": "Requests today", "value": "1,248"},
        {"label": "Error rate", "value": "0.04%"},
    ]
    return render_template("analytics/index.html", metrics=metrics)
