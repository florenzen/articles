#!/usr/bin/env python3
"""Check and fix metadata of the images in content/.

Commands (each takes one or more image files):

  check-svg-text  Fail if an SVG contains text elements. Text in SVGs is drawn
                  with fonts the visitor may not have, so it must be converted
                  to paths. Prints how to do that in Inkscape.
  check           Fail if a photo/raster image contains location (GPS) data,
                  or if any image lacks the copyright and licence entry.
  fix             Remove location data from raster images and add the missing
                  copyright and licence entries (all images).

Author and licence are read from [extra] in config.toml, the same values the
site footer uses. Raster images are read and written with exiftool.
"""

import argparse
import datetime
import json
import re
import shutil
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RASTER_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".tif", ".tiff"}

NS = {
    "svg": "http://www.w3.org/2000/svg",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "cc": "http://creativecommons.org/ns#",
    "dc": "http://purl.org/dc/elements/1.1/",
}

# Location tags besides the GPS ones (IPTC/XMP place names).
LOCATION_TAGS = [
    "XMP-iptcCore:Location",
    "XMP-photoshop:City",
    "XMP-photoshop:State",
    "XMP-photoshop:Country",
    "XMP-iptcExt:LocationCreated*",
    "XMP-iptcExt:LocationShown*",
    "IPTC:City",
    "IPTC:Sub-location",
    "IPTC:Province-State",
    "IPTC:Country-PrimaryLocationName",
]

INKSCAPE_HELP = """\
SVGs must not contain text: visitors who lack the font see a fallback font.
Convert the text to paths in Inkscape:

  1. Open the file in Inkscape.
  2. Edit > Select All in All Layers (Ctrl+Alt+A).
  3. Path > Object to Path (Shift+Ctrl+C). This also converts text inside groups.
  4. File > Save.

The text is no longer editable afterwards, so keep a copy with text elsewhere
(outside content/, so it is not published) if you want to change it later."""


def site_config():
    with open(ROOT / "config.toml", "rb") as f:
        extra = tomllib.load(f)["extra"]
    return extra["author"], extra["license"], extra["license_url"]


def rights_text(year, author, license_name):
    return f"© {year} {author}. Licensed under {license_name}."


def is_svg(path):
    return path.suffix.lower() == ".svg"


def is_raster(path):
    return path.suffix.lower() in RASTER_SUFFIXES


# --- SVG -------------------------------------------------------------------


def svg_text_elements(path):
    tree = ET.parse(path)
    found = []
    for tag in ("text", "flowRoot"):
        found += tree.getroot().findall(f".//svg:{tag}", NS)
    return found


def svg_license(path):
    """Return (rights, license_url) from the SVG's RDF metadata."""
    root = ET.parse(path).getroot()
    work = root.find(".//svg:metadata/rdf:RDF/cc:Work", NS)
    if work is None:
        return None, None
    rights = work.findtext("dc:rights/cc:Agent/dc:title", default="", namespaces=NS)
    lic = work.find("cc:license", NS)
    url = lic.get(f"{{{NS['rdf']}}}resource") if lic is not None else None
    return rights.strip() or None, url


def svg_metadata_block(rights, author, license_url, indent):
    """RDF metadata in the form Inkscape writes (Document Properties > Metadata)."""
    i = indent

    def agent(name):
        return f"<cc:Agent><dc:title>{name}</dc:title></cc:Agent>"

    return (
        f"{i}<metadata\n"
        f'{i}   xmlns:rdf="{NS["rdf"]}"\n'
        f'{i}   xmlns:cc="{NS["cc"]}"\n'
        f'{i}   xmlns:dc="{NS["dc"]}">\n'
        f"{i}  <rdf:RDF>\n"
        f'{i}    <cc:Work rdf:about="">\n'
        f"{i}      <dc:creator>{agent(author)}</dc:creator>\n"
        f"{i}      <dc:rights>{agent(rights)}</dc:rights>\n"
        f'{i}      <cc:license rdf:resource="{license_url}" />\n'
        f"{i}    </cc:Work>\n"
        f"{i}  </rdf:RDF>\n"
        f"{i}</metadata>\n"
    )


def fix_svg(path, year, author, license_name, license_url):
    rights, url = svg_license(path)
    if rights and url == license_url:
        return "ok"
    text = path.read_text(encoding="utf-8")
    if re.search(r"<metadata[\s>]", text):
        return (
            "has a <metadata> element already; add the entries by hand in Inkscape "
            "(File > Document Properties > Metadata): Rights "
            f'"{rights_text(year, author, license_name)}", License {license_name}'
        )
    # Insert right after the opening <svg ...> tag, keeping the file as it is.
    m = re.search(r"<svg\b[^>]*>\n?", text)
    if not m:
        return "no <svg> element found"
    block = svg_metadata_block(
        rights_text(year, author, license_name), author, license_url, "  "
    )
    path.write_text(text[: m.end()] + block + text[m.end() :], encoding="utf-8")
    return "added copyright and licence"


# --- Raster images (exiftool) ----------------------------------------------


def exiftool(*args):
    if not shutil.which("exiftool"):
        sys.exit(
            "exiftool is not installed "
            "(Debian/Ubuntu: apt install libimage-exiftool-perl)"
        )
    return subprocess.run(
        ["exiftool", *args], check=True, capture_output=True, text=True
    ).stdout


def raster_tags(path):
    out = exiftool(
        "-json", "-a", "-G1", "-n",
        "-gps:all", "-xmp-exif:gps*", *[f"-{t}" for t in LOCATION_TAGS],
        "-EXIF:Copyright", "-XMP-dc:Rights", "-XMP-cc:License",
        "-DateTimeOriginal", "-CreateDate",
        str(path),
    )  # fmt: skip
    tags = json.loads(out)[0]
    tags.pop("SourceFile", None)
    return tags


def location_tags(tags):
    place_names = {
        "City",
        "State",
        "Country",
        "Sub-location",
        "Province-State",
        "Country-PrimaryLocationName",
    }
    keys = []
    for key in tags:
        group, _, name = key.partition(":")
        is_gps = group == "GPS" or name.startswith("GPS")
        if is_gps or name.startswith("Location") or name in place_names:
            keys.append(key)
    return keys


def raster_year(tags):
    for key in ("ExifIFD:DateTimeOriginal", "ExifIFD:CreateDate", "XMP-xmp:CreateDate"):
        value = str(tags.get(key, ""))
        if re.match(r"\d{4}", value):
            return value[:4]
    return None


def fix_raster(path, year, author, license_name, license_url):
    tags = raster_tags(path)
    args = []
    done = []
    if location_tags(tags):
        args += ["-gps:all=", "-xmp-exif:gps*="] + [f"-{t}=" for t in LOCATION_TAGS]
        done.append("removed location data")
    if not (tags.get("IFD0:Copyright") or tags.get("XMP-dc:Rights")):
        rights = rights_text(raster_year(tags) or year, author, license_name)
        args += [
            f"-EXIF:Copyright={rights}",
            f"-EXIF:Artist={author}",
            f"-XMP-dc:Rights={rights}",
            f"-XMP-dc:Creator={author}",
        ]
        done.append("added copyright")
    if tags.get("XMP-cc:License") != license_url:
        args += [
            f"-XMP-cc:License={license_url}",
            f"-XMP-xmpRights:WebStatement={license_url}",
            "-XMP-xmpRights:Marked=True",
        ]
        done.append("added licence")
    if not args:
        return "ok"
    exiftool("-overwrite_original", "-P", "-q", *args, str(path))
    return ", ".join(done)


# --- Commands --------------------------------------------------------------


def cmd_check_svg_text(files):
    bad = [p for p in files if is_svg(p) and svg_text_elements(p)]
    for p in bad:
        print(f"{p}: contains {len(svg_text_elements(p))} text element(s)")
    if bad:
        print()
        print(INKSCAPE_HELP)
    return 1 if bad else 0


def cmd_check(files):
    _, license_name, license_url = site_config()
    problems = []
    for p in files:
        if is_svg(p):
            rights, url = svg_license(p)
        elif is_raster(p):
            tags = raster_tags(p)
            loc = location_tags(tags)
            if loc:
                problems.append(f"{p}: contains location data ({', '.join(loc)})")
            rights = tags.get("IFD0:Copyright") or tags.get("XMP-dc:Rights")
            url = tags.get("XMP-cc:License")
        else:
            continue
        if not rights:
            problems.append(f"{p}: no copyright entry")
        if url != license_url:
            problems.append(f"{p}: licence is not {license_name} ({url or 'missing'})")
    for line in problems:
        print(line)
    if problems:
        print()
        print("Fix with: python3 scripts/image-metadata.py fix FILE...")
    return 1 if problems else 0


def cmd_fix(files, year):
    author, license_name, license_url = site_config()
    status = 0
    for p in files:
        if is_svg(p):
            result = fix_svg(p, year, author, license_name, license_url)
        elif is_raster(p):
            result = fix_raster(p, year, author, license_name, license_url)
        else:
            continue
        print(f"{p}: {result}")
        if result.startswith(("has a", "no <svg>")):
            status = 1
    return status


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("command", choices=["check-svg-text", "check", "fix"])
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument(
        "--year",
        default=str(datetime.date.today().year),
        help="copyright year for images without a recorded creation date "
        "(default: current year)",
    )
    args = parser.parse_args()
    if args.command == "check-svg-text":
        return cmd_check_svg_text(args.files)
    if args.command == "check":
        return cmd_check(args.files)
    return cmd_fix(args.files, args.year)


if __name__ == "__main__":
    sys.exit(main())
