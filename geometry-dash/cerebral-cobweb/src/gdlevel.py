"""Read/write GDShare .gmd files and Geometry Dash level strings.

The .gmd is kept byte-identical except for the level string (k4) and the
object count (k48). Original layout objects are carried over as their exact
original text; new objects are appended after them.
"""
import base64
import gzip
import re
import zlib


def decode_level_string(s: str) -> str:
    s = s.strip()
    raw = base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
    try:
        return gzip.decompress(raw).decode("utf-8")
    except OSError:
        return zlib.decompress(raw, 15 + 32).decode("utf-8")


def encode_level_string(level: str) -> str:
    # GD writes gzip + url-safe base64 (with padding).
    raw = gzip.compress(level.encode("utf-8"), compresslevel=9, mtime=0)
    return base64.urlsafe_b64encode(raw).decode("ascii")


def split_level(level: str):
    """Return (header, [raw object strings]) keeping exact original text."""
    parts = level.split(";")
    header = parts[0]
    objs = [p for p in parts[1:] if p != ""]
    return header, objs


def parse_obj(raw: str) -> dict:
    kv = raw.split(",")
    return {kv[i]: kv[i + 1] for i in range(0, len(kv) - 1, 2)}


def parse_header(header: str) -> list:
    """Header is k,v,k,v... (values may contain '|' and '_')."""
    kv = header.split(",")
    return [[kv[i], kv[i + 1]] for i in range(0, len(kv) - 1, 2)]


def build_header(pairs: list) -> str:
    return ",".join(f"{k},{v}" for k, v in pairs)


def parse_colors(kS38: str) -> list:
    """Return list of color dicts (ordered keys) from the kS38 string."""
    out = []
    for c in kS38.split("|"):
        if not c:
            continue
        p = c.split("_")
        out.append([[p[i], p[i + 1]] for i in range(0, len(p) - 1, 2)])
    return out


def build_colors(cols: list) -> str:
    return "".join("_".join(f"{k}_{v}" for k, v in c) + "|" for c in cols)


class GmdFile:
    def __init__(self, path):
        self.path = path
        self.xml = open(path, encoding="utf-8").read()
        m = re.search(r"<k>k4</k><s>(.*?)</s>", self.xml, re.S)
        if not m:
            raise ValueError("no k4 level string in " + path)
        self._k4_span = m.span(1)
        self.level = decode_level_string(m.group(1))

    def write(self, path, new_level: str, object_count: int):
        enc = encode_level_string(new_level)
        m = re.search(r"<k>k4</k><s>(.*?)</s>", self.xml, re.S)  # locate at write time
        a, b = m.span(1)
        xml = self.xml[:a] + enc + self.xml[b:]
        xml, n = re.subn(r"(<k>k48</k><i>)(\d+)(</i>)",
                         lambda m: f"{m.group(1)}{object_count}{m.group(3)}", xml, count=1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml)
        return path
