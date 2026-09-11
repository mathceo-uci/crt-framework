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
  main.ptx                  # root file
  frontmatter.ptx
  introduction.ptx
  context.ptx
  dimensions-overview.ptx
  dimension-1.ptx           ✓
  dimension-2.ptx           ✓
  dimension-3.ptx           ✓
  dimension-4.ptx           ✓
  dimension-5.ptx           ✓
  dimension-6.ptx           ✓
  fundamental-goal.ptx      ✓
  three-contexts.ptx        ✓  (includes "Aligning the Three Contexts" as subsection)
  applying-dimensions.ptx   ✓  (includes "Examples" as subsection)
  possible-modifications.ptx ✓
external/                   # images live here (maps to output/web/external)
html-source/                # original Google Docs HTML (source of truth)
publication/publication.ptx # configured: generated="../generated-assets"
```

**Conversion is complete.** All sections have been converted from HTML and the build passes cleanly.

## PreTeXt conventions for this project

### Images
- Images are in `external/` at project root
- `main.ptx` `<docinfo>` has `<directories external="../external"/>` configured
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
  <!-- The "Components" wrapper subsection is commented out; each component is a
       direct <subsection> so components render at the same level as beliefs/activity. -->
  <subsection xml:id="dimN-[name]">
    <title>Component X: [Name]</title>
    <!-- one-liner description -->
    <paragraphs><title>Mentors' Actions</title>...</paragraphs>
    <paragraphs><title>Students' Perspectives</title>...</paragraphs>
    <!-- Note: Dim 1 Component 2 uses "Students' Interactions" not "Students' Perspectives" -->
  </subsection>
  <!-- Optional: activity, table, case study, suggested reading subsections -->
</section>
```

