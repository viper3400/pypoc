from __future__ import annotations

from flask_plugin_analytics.routes import blueprint

PLUGIN = {
    "id": "analytics",
    "name": "Analytics",
    "description": "Operational analytics dashboard",
    "version": "0.1.0",
    "blueprint": blueprint,
    "menu_entry": {
        "label": "Analytics",
        "icon": "chart-line",
        "path": "/analytics/",
    },
}
