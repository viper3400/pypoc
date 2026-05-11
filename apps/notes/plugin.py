from __future__ import annotations

from apps.notes.routes import blueprint

PLUGIN = {
    "id": "notes",
    "name": "Notes",
    "description": "Simple notes application",
    "version": "0.1.0",
    "blueprint": blueprint,
    "menu_entry": {
        "label": "Notes",
        "icon": "sticky-note",
        "path": "/notes/",
    },
}
