#!/usr/bin/env python3
"""Generate README.md and site/data.json from data/awesome-fastapi.json.

data/awesome-fastapi.json is the single source of truth for this list.
To add, remove, or edit an entry, edit that file and re-run this script
(or just push -- CI regenerates and checks for drift).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "awesome-fastapi.json"
README_PATH = ROOT / "README.md"
SITE_DATA_PATH = ROOT / "site" / "data.json"


def render_item(item, indent):
    lines = []
    if item.get("url"):
        text = f"[{item['name']}]({item['url']})"
        if item.get("desc"):
            sep = " " if item.get("no_dash") else " - "
            text += f"{sep}{item['desc']}"
    else:
        text = f"{item['name']}:"
    lines.append(f"{indent}- {text}")
    for child in item.get("children", []):
        lines.extend(render_item(child, indent + "  "))
    return lines


def render_items(items, indent=""):
    lines = []
    for item in items:
        lines.extend(render_item(item, indent))
    return lines


def render_subsection(sub, level):
    lines = [f"{'#' * level} {sub['title']}", ""]
    if sub.get("note"):
        lines.append(sub["note"])
        lines.append("")
    if "subsections" in sub:
        for i, nested in enumerate(sub["subsections"]):
            lines.extend(render_subsection(nested, level + 1))
            if i < len(sub["subsections"]) - 1:
                lines.append("")
    elif "groups" in sub:
        for i, group in enumerate(sub["groups"]):
            lines.append(group["label"])
            lines.append("")
            lines.extend(render_items(group["items"]))
            if i < len(sub["groups"]) - 1:
                lines.append("")
    else:
        lines.extend(render_items(sub.get("items", [])))
    return lines


def slugify_toc_entries(data):
    lines = []
    for section in data["sections"]:
        lines.append(f"- [{section['title']}](#{section['id']})")
        for sub in section.get("subsections", []):
            lines.append(f"  - [{sub['title']}](#{sub['id']})")
    lines.append("- [Sponsors](#sponsors)")
    return lines


def render_readme(data):
    lines = []
    lines.append("<!--lint disable double-link-->")
    lines.append("")
    badge = data["badge"]
    lines.append(
        f"# {data['title']} | [![{badge['alt']}]({badge['img']})]({badge['url']})"
    )
    lines.append("")
    lines.append(f"> {data['tagline']}")
    lines.append("")
    lines.append(data["intro"])
    lines.append("")
    lines.append("## Contents")
    lines.append("")
    lines.extend(slugify_toc_entries(data))
    lines.append("")

    for section in data["sections"]:
        lines.append(f"## {section['title']}")
        lines.append("")
        subs = section.get("subsections", [])
        for i, sub in enumerate(subs):
            lines.extend(render_subsection(sub, 3))
            lines.append("")

    lines.append("## Sponsors")
    lines.append("")
    lines.append(data["sponsors"]["text"])
    lines.append("")
    for s in data["sponsors"]["items"]:
        lines.append(
            f'<a href="{s["url"]}" target="_blank" title="{s["title"]}">'
            f'<img src="{s["img"]}"></a>'
        )
    lines.append("")

    return "\n".join(lines)


def flatten_for_site(data):
    entries = []

    def walk(items, breadcrumb, section_id):
        for item in items:
            if item.get("url"):
                entries.append(
                    {
                        "name": item["name"],
                        "url": item["url"],
                        "desc": item.get("desc", ""),
                        "category": breadcrumb,
                        "sectionId": section_id,
                    }
                )
            for child in item.get("children", []):
                child_breadcrumb = breadcrumb + " › " + item["name"]
                if child.get("url"):
                    entries.append(
                        {
                            "name": child["name"],
                            "url": child["url"],
                            "desc": child.get("desc", ""),
                            "category": child_breadcrumb,
                            "sectionId": section_id,
                        }
                    )

    def walk_subsection(sub, breadcrumb, section_id):
        crumb = breadcrumb + " › " + sub["title"]
        if "subsections" in sub:
            for nested in sub["subsections"]:
                walk_subsection(nested, crumb, section_id)
        elif "groups" in sub:
            for group in sub["groups"]:
                walk(group["items"], crumb, section_id)
        else:
            walk(sub.get("items", []), crumb, section_id)

    sections_meta = []
    for section in data["sections"]:
        sections_meta.append({"id": section["id"], "title": section["title"]})
        for sub in section.get("subsections", []):
            walk_subsection(sub, section["title"], section["id"])

    return {"sections": sections_meta, "entries": entries}


def main():
    data = json.loads(DATA_PATH.read_text())
    readme = render_readme(data)
    site_data = flatten_for_site(data)

    check_only = "--check" in sys.argv

    if check_only:
        ok = True
        if README_PATH.read_text() != readme:
            print("README.md is out of sync with data/awesome-fastapi.json", file=sys.stderr)
            ok = False
        existing_site = (
            json.loads(SITE_DATA_PATH.read_text()) if SITE_DATA_PATH.exists() else None
        )
        if existing_site != site_data:
            print("site/data.json is out of sync with data/awesome-fastapi.json", file=sys.stderr)
            ok = False
        sys.exit(0 if ok else 1)

    README_PATH.write_text(readme)
    SITE_DATA_PATH.write_text(json.dumps(site_data, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {README_PATH} and {SITE_DATA_PATH}")


if __name__ == "__main__":
    main()
