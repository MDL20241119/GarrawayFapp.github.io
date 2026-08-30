from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
required = [
    ROOT / "index.html",
    ROOT / "events" / "index.html",
    ROOT / "contact" / "index.html",
    ROOT / ".nojekyll",
    ROOT / "data" / "instagram.json",
    ROOT / "data" / "facebook-events.json",
    ROOT / "assets" / "floor-map.svg",
]

errors: list[str] = []
for path in required:
    if not path.exists() or path.stat().st_size == 0:
        errors.append(f"Missing or empty: {path.relative_to(ROOT)}")

if not errors:
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    events_page = (ROOT / "events" / "index.html").read_text(encoding="utf-8")
    contact_page = (ROOT / "contact" / "index.html").read_text(encoding="utf-8")

    checks = {
        "Garraway F brand": "Garraway F",
        "Living Lab message": "SOCIAL IMPLEMENTATION LIVING LAB",
        "Instagram panel": "Instagram",
        "Facebook panel": "Facebook",
        "Events route": "/GarrawayFapp.github.io/events",
        "Contact route": "/GarrawayFapp.github.io/contact",
    }
    for label, needle in checks.items():
        if needle not in home:
            errors.append(f"Missing {label}")

    if "次の出会いを" not in events_page:
        errors.append("Events page content is missing")
    if "相談から" not in contact_page:
        errors.append("Contact page content is missing")

    instagram = json.loads((ROOT / "data" / "instagram.json").read_text(encoding="utf-8"))
    posts = instagram.get("posts", []) if isinstance(instagram, dict) else []
    if len(posts) < 4:
        errors.append(f"Instagram JSON must contain at least 4 posts, found {len(posts)}")

    facebook = json.loads((ROOT / "data" / "facebook-events.json").read_text(encoding="utf-8"))
    events = facebook.get("events", []) if isinstance(facebook, dict) else []
    if len(events) < 1:
        errors.append("Facebook event JSON must contain at least 1 event")

if errors:
    print("SITE VALIDATION FAILED")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("SITE VALIDATION PASSED")
print("- Home, Events, Contact: OK")
print("- Instagram and Facebook data: OK")
print("- Floor map and GitHub Pages assets: OK")
