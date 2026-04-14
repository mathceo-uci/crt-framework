# CRT Framework — PreTeXt Project

## What this is
A PreTeXt article converting a Google Docs HTML file into structured PreTeXt XML.
Source HTML: `html-source/V4 - The Math CEO Connections Framework: Six Dimensions of CRT.html`
This is a Culturally Responsive Teaching framework for UCI Math CEO (after-school math program, LatinX youth, UC Irvine).

## Build commands
```
pretext build web     # build HTML output
pretext view web      # preview in browser
```

## File structure
```
source/
  main.ptx                  # root file — add xi:include here for each new section
  frontmatter.ptx
  introduction.ptx
  context.ptx
  dimensions-overview.ptx
  dimension-1.ptx           ✓ done
  dimension-2.ptx           ✓ done
  dimension-3.ptx           ✓ done
  dimension-4.ptx           (next)
  dimension-5.ptx
  dimension-6.ptx
  ... (remaining sections)
assets/                     # images live here
html-source/                # original Google Docs HTML (source to convert from)
publication/publication.ptx # configured: external="../assets", generated="../generated-assets"
```

## Remaining sections to convert (from HTML)
Starting at approximately entry 536 in the parsed HTML:
- Dimension 4: Access and Relevance
- Dimension 5: Inclusion through Cultural Diversity
- Dimension 6: Social Justice Reflection
- The Fundamental Goal: Personal Development & Growth
- The Three Contexts (Program Structure, Pedagogical Practices, Curriculum)
- Aligning the Three Contexts
- Applying the Dimensions
- Examples
- Possible Modifications to the Six Dimensions

## PreTeXt conventions for this project

### Images
- Images are in `assets/` at project root
- `publication.ptx` has `external="../assets"` configured
- Reference images by filename only: `<image source="filename.png"/>`

### Special characters
- Em-dash (−): use `<mdash/>`
- En-dash (range, e.g. 6–8): use `<ndash/>`
- Ampersand (&): use `&amp;`
- Ellipsis (…): use `<ellipsis/>`
- Quotes: use `<q>...</q>` (not " ")

### Headings
- Use `<paragraphs><title>...</title>` for bold/minor named groupings (NOT `<term>`)
- `<term>` is only for actual mathematical/technical terms being defined
- `<alert>...</alert>` for bold inline text that is NOT a heading

### Student perspectives
- Always wrap student quotes in `<q>...</q>` tags for consistency

### Planning items
- Mark with `(Planning)` prefix in list items

### Skipping content
- Skip repeated decorative "THE 6 DIMENSIONS" sidebar entries in the HTML
  (these appear as entries like "THE", "6 DIMENSIONS", "1:", "Students at the Center", etc.)

### Dimension section template
Each dimension follows this structure:
```xml
<section xml:id="dimension-N">
  <title>Dimension N: [Title]</title>
  <introduction>
    <!-- 2-3 intro paragraphs -->
  </introduction>
  <subsection xml:id="dimN-beliefs">
    <title>Mentors' Beliefs and Attitudes</title>
    <!-- belief list + reflection question -->
  </subsection>
  <subsection xml:id="dimN-components">
    <title>Components</title>
    <subsubsection xml:id="dimN-[name]">
      <title>Component X: [Name]</title>
      <!-- one-liner description -->
      <paragraphs><title>Mentors' Actions</title>...</paragraphs>
      <paragraphs><title>Students' Perspectives</title>...</paragraphs>
      <!-- Note: Dim 1 Component 2 uses "Students' Interactions" not "Students' Perspectives" -->
    </subsubsection>
  </subsection>
  <!-- Optional: activity, table, case study, suggested reading subsections -->
</section>
```

### Parsing the HTML
Use this Python snippet to extract text entries from the HTML:
```python
python3 -c "
from html.parser import HTMLParser
class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.entries = []
        self.in_body = False
        self.current_tag = ''
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        if tag == 'body': self.in_body = True
    def handle_data(self, data):
        if self.in_body and data.strip():
            self.entries.append((self.current_tag, data.strip()))
parser = TextExtractor()
with open('html-source/V4 - The Math CEO Connections Framework: Six Dimensions of CRT.html', encoding='utf-8') as f:
    parser.feed(f.read())
for i, (tag, text) in enumerate(parser.entries[START:END], start=START):
    print(f'{i:3}. [{tag}] {text[:120]}')
"
```
Dimension 4 starts around entry 536.
