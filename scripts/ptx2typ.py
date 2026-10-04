"""Convert the PreTeXt source directly to Typst.

Writes body.typ (the document body) and meta.json (title page data) to
output/typst, copies the styling template scripts/main.typ next to them,
then compiles output/typst/main.pdf.  Usage, from the project folder:

    python3 scripts/ptx2typ.py      (macOS/Linux)
    py scripts\\ptx2typ.py           (Windows)

Needs Python 3.8+, lxml (pip install lxml), and typst on the PATH.

Only the PreTeXt elements this project uses are supported; anything else
stops the conversion with its file and line, so nothing is silently dropped.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePath

try:
    from lxml import etree
except ImportError:
    sys.exit("ptx2typ: the lxml package is required (pip install lxml)")

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "source" / "main.ptx"
OUT = ROOT / "output" / "typst"
TEMPLATE = Path(__file__).resolve().parent / "main.typ"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"

HEADING_LEVEL = {"section": 1, "subsection": 2, "subsubsection": 3, "paragraphs": 4}
CHAR_ELEMENTS = {"mdash": "—", "ndash": "–", "ellipsis": "…"}


class ConversionError(Exception):
    pass


def fail(el, msg):
    src = el.base or "?"
    raise ConversionError(f"{os.path.basename(src)}:{el.sourceline}: {msg} <{el.tag}>")


# --- loading -----------------------------------------------------------------

def load_customizations():
    """Read <custom name=...> values from the file publication.ptx points to."""
    pub = etree.parse(str(ROOT / "publication" / "publication.ptx"))
    rel = pub.find("source").get("customizations")
    if not rel:
        return {}
    path = (MAIN.parent / rel).resolve()
    tree = etree.parse(str(path))
    return {c.get("name"): c for c in tree.iter("custom")}


def load_source():
    parser = etree.XMLParser(remove_comments=True, remove_pis=True)
    tree = etree.parse(str(MAIN), parser)
    tree.xinclude()
    return tree.getroot()


# --- text escaping -----------------------------------------------------------

def escape(text):
    """Escape Typst markup characters in plain text."""
    text = re.sub(r"([\\#$*_`<>@\[\]~])", r"\\\1", text)
    # Straight apostrophes become smart quotes in Typst (and primes after
    # digits), so use the typographic apostrophe directly.
    return text.replace("'", "’").replace('"', "”")


def protect_line_start(text):
    """Keep text at the start of a line from being read as list/heading markup."""
    text = text.lstrip()
    if re.match(r"[-+=/]\s", text) or text.startswith("="):
        return "\\" + text
    m = re.match(r"(\d+)\.", text)
    if m:
        return m.group(1) + "\\." + text[m.end():]
    return text


def indent(text, by):
    pad = " " * by
    return "\n".join(pad + line if line else line for line in text.split("\n"))


def item(marker, body):
    """A list/term item; a body that itself starts with a list goes on its own line."""
    if re.match(r"[-+/] ", body):
        return marker + "\n" + indent(body, 2)
    return f"{marker} " + indent(body, 2).lstrip()


# --- math --------------------------------------------------------------------

LATEX_MATH = {r"\times": " times ", r"\#": "\\#"}


def math(el):
    tex = el.text or ""
    if len(el):
        fail(el, "markup inside math is not supported")
    out = []
    for tok in re.split(r"(\\[A-Za-z]+|\\.)", tex):
        if tok.startswith("\\"):
            if tok not in LATEX_MATH:
                fail(el, f"unsupported LaTeX command {tok!r} in math")
            out.append(LATEX_MATH[tok])
        else:
            # Typst reads adjacent letters as one multi-letter name; LaTeX means a
            # product.  A bare "/" would be a stacked fraction in Typst.
            tok = re.sub(r"(?<=[A-Za-z])(?=[A-Za-z])", " ", tok)
            out.append(tok.replace("/", "\\/"))
    return f"${''.join(out).strip()}$"


# --- converter ---------------------------------------------------------------

class Converter:
    def __init__(self, custom, external):
        self.custom = custom
        self.external = external
        self.quote_depth = 0

    # inline content ----------------------------------------------------------

    def inline(self, el):
        """Convert an element's mixed text/inline content (not its tail)."""
        out = [escape(el.text or "")]
        for child in el:
            out.append(self.inline_el(child))
            out.append(escape(child.tail or ""))
        return "".join(out)

    def inline_el(self, el):
        tag = el.tag
        if tag in CHAR_ELEMENTS:
            return CHAR_ELEMENTS[tag]
        if tag == "q":
            self.quote_depth += 1
            body = self.inline(el)
            self.quote_depth -= 1
            return f"“{body}”" if self.quote_depth == 0 else f"‘{body}’"
        if tag == "em":
            return f"#emph[{self.inline(el)}]"
        if tag in ("term", "alert"):
            return f"#strong[{self.inline(el)}]"
        if tag == "m":
            return math(el)
        if tag == "url":
            href = el.get("href")
            label = self.inline(el) if (el.text or len(el)) else escape(href)
            return f'#link("{href}")[{label}]'
        if tag == "custom":
            ref = el.get("ref")
            if ref not in self.custom:
                fail(el, f"unknown customization {ref!r}")
            return self.inline(self.custom[ref])
        fail(el, "unsupported inline element")

    def clean(self, text):
        return re.sub(r"\s+", " ", text).strip()

    def title(self, el):
        t = el.find("title")
        return self.clean(self.inline(t)) if t is not None else None

    # blocks ------------------------------------------------------------------

    def blocks(self, el, skip=("title",)):
        """Convert block children of a division or container."""
        out = []
        for child in el:
            if child.tag in skip:
                continue
            out.extend(self.block(child))
            if (child.tail or "").strip():
                fail(child, "stray text after block element")
        return out

    def block(self, el):
        tag = el.tag
        if tag in HEADING_LEVEL:
            return self.division(el)
        if tag in ("introduction", "conclusion"):
            return self.blocks(el)
        if tag == "p":
            return self.paragraph(el)
        if tag in ("ul", "ol"):
            return [self.list(el)]
        if tag == "dl":
            return [self.dlist(el)]
        if tag == "figure":
            return [self.figure(el)]
        if tag == "tabular":
            return [self.tabular(el)]
        fail(el, "unsupported block element")

    def division(self, el):
        level = HEADING_LEVEL[el.tag]
        title = self.title(el)
        if title is None:
            fail(el, "division without a title")
        label = f" <{el.get(XML_ID)}>" if el.get(XML_ID) else ""
        return [f"{'=' * level} {title}{label}"] + self.blocks(el)

    def paragraph(self, el):
        """A <p> may hold lists; split it into text runs and block parts."""
        parts, run = [], [escape(el.text or "")]

        def flush():
            text = self.clean("".join(run))
            if text:
                parts.append(protect_line_start(text))
            run.clear()

        for child in el:
            if child.tag in ("ul", "ol", "dl"):
                flush()
                parts.extend(self.block(child))
            else:
                run.append(self.inline_el(child))
            run.append(escape(child.tail or ""))
        flush()
        return parts

    def item_body(self, li):
        """Body of an <li>: inline text, or block children (with optional title)."""
        if any(c.tag in ("p", "ul", "ol", "dl", "figure", "tabular") for c in li):
            if (li.text or "").strip():
                fail(li, "mixed text and blocks in list item")
            return "\n\n".join(self.blocks(li))
        return protect_line_start(self.clean(self.inline(li)))

    def list(self, el):
        marker = "-" if el.tag == "ul" else "+"
        items = []
        for li in el:
            if li.tag != "li":
                fail(li, "expected <li>")
            title = self.title(li)
            body = self.item_body(li)
            if title:
                if not re.search(r"[.!?:]$", title):
                    title += "."
                body = f"#strong[{title}]\n\n{body}" if body else f"#strong[{title}]"
            items.append(item(marker, body))
        sep = "\n\n" if any("\n" in i for i in items) else "\n"
        return sep.join(items)

    def dlist(self, el):
        items = []
        for li in el:
            title = self.title(li)
            if title is None:
                fail(li, "<dl> item without a title")
            body = self.item_body(li)
            items.append(item(f"/ {title}:", body))
        return "\n\n".join(items)

    def figure(self, el):
        img = el.find("image")
        cap = el.find("caption")
        if img is None or cap is None:
            fail(el, "figure needs an image and a caption")
        for child in el:
            if child.tag not in ("image", "caption"):
                fail(child, "unsupported figure content")
        args = [f'"{self.external}/{img.get("source")}"']
        if img.get("width"):
            args.append(f"width: {img.get('width')}")
        short = img.find("shortdescription")
        if short is not None:
            alt = self.clean(short.xpath("string()")).replace('"', '\\"')
            args.append(f'alt: "{alt}"')
        label = f" <{el.get(XML_ID)}>" if el.get(XML_ID) else ""
        caption = self.clean(self.inline(cap))
        return f"#figure(\n  image({', '.join(args)}),\n  caption: [{caption}],\n){label}"

    def tabular(self, el):
        cols = [c.get("width") for c in el.findall("col")]
        rows = el.findall("row")
        ncols = max(len(r.findall("cell")) for r in rows)
        columns = f"({', '.join(cols)})" if cols and all(cols) else str(ncols)
        align = {"left": "left", "center": "center", "right": "right"}[el.get("halign", "left")]

        def cell(c):
            if c.find("p") is not None:
                return "[" + "\n\n".join(self.blocks(c)) + "]"
            return "[" + self.clean(self.inline(c)) + "]"

        lines = [f"columns: {columns},", f"align: {align},"]
        for r in rows:
            cells = ", ".join(cell(c) for c in r.findall("cell"))
            if r.get("header") == "yes":
                lines.append(f"table.header({cells}),")
            else:
                lines.append(f"{cells},")
        table = "table(\n" + indent("\n".join(lines), 2) + "\n)"
        return f"#align(center, block(breakable: false, {table}))"


# --- front matter --------------------------------------------------------------

def front_matter(article, conv):
    fm = article.find("frontmatter")
    text = lambda e: conv.clean(e.xpath("string()")) if e is not None else ""

    def check(el, allowed):
        for child in el:
            if child.tag not in allowed:
                fail(child, "unsupported front matter element")

    check(fm, ("bibinfo", "titlepage", "abstract"))
    bib = fm.find("bibinfo")
    check(bib, ("author", "date"))
    authors = []
    for author in bib.findall("author"):
        check(author, ("personname", "institution"))
        authors.append({
            "name": text(author.find("personname")),
            "affiliation": text(author.find("institution")),
        })
    return {
        "title": text(article.find("title")),
        "subtitle": text(article.find("subtitle")),
        "authors": authors,
        "date": text(bib.find("date")),
        "abstract": text(fm.find("abstract")),
    }


def write_utf8(path, text):
    # Explicit encoding and newlines: Windows defaults to cp1252 and CRLF
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main():
    root = load_source()
    article = root.find("article")
    external_dir = MAIN.parent / root.find("docinfo/directories").get("external")
    # Typst paths need forward slashes ("\" is an escape in Typst strings)
    external = PurePath(os.path.relpath(external_dir.resolve(), OUT)).as_posix()
    conv = Converter(load_customizations(), external)

    meta = front_matter(article, conv)
    meta["external"] = external
    body = conv.blocks(article, skip=("title", "subtitle", "frontmatter"))

    OUT.mkdir(parents=True, exist_ok=True)
    write_utf8(OUT / "meta.json", json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    write_utf8(OUT / "body.typ",
        "// Generated by scripts/ptx2typ.py from source/*.ptx — do not edit.\n\n"
        + "\n\n".join(body) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}/body.typ ({len(body)} blocks) and meta.json")

    if not TEMPLATE.exists():
        sys.exit(f"ptx2typ: no template at {TEMPLATE.relative_to(ROOT)}; not compiling")
    # main.typ reads meta.json and body.typ by relative path, so it runs from OUT
    template = OUT / "main.typ"
    shutil.copyfile(TEMPLATE, template)
    typst = shutil.which("typst")
    if typst is None:
        sys.exit("ptx2typ: typst not found on PATH; not compiling")
    # --root lets main.typ and body.typ reach images in external/
    if subprocess.run([typst, "compile", "--root", str(ROOT), str(template)]).returncode:
        sys.exit("ptx2typ: typst compile failed")
    print(f"wrote {OUT.relative_to(ROOT)}/main.pdf")


if __name__ == "__main__":
    # Messages may quote source text; don't crash on a non-UTF-8 console
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors="replace")
    try:
        main()
    except ConversionError as e:
        sys.exit(f"ptx2typ: {e}")
