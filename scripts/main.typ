// Math CEO Connections Framework — Typst edition.
// Body text (body.typ) and meta.json are generated from source/*.ptx.
// Build:  python3 scripts/ptx2typ.py  — copies this file to output/typst and
// compiles it there.  Edit this copy, not the one in output/typst.
#let meta = json("meta.json")

// Palette
#let accent = rgb("#1F6F8B")      // deep teal
#let accent-soft = rgb("#E6F1F5")
#let warm = rgb("#F2A541")        // highlight
#let ink = rgb("#1F2933")
#let muted = rgb("#6B7785")
#let hairline = rgb("#D9E0E6")

#let sans = ("Avenir Next", "Helvetica Neue", "Arial")

// Plain text of a heading body
#let plain(c) = {
  if type(c) == str { c }
  else if c.func() == smartquote { if c.double { "”" } else { "’" } }
  else if c.has("text") { c.text }
  else if c.has("children") { c.children.map(plain).join() }
  else if c.has("body") { plain(c.body) }
  else if c == [ ] { " " }
  else { "" }
}

// Section name for the running header: last level-1 heading up to this page
#let current-section() = {
  let pg = here().page()
  let hs = query(heading.where(level: 1)).filter(h => h.location().page() <= pg)
  if hs.len() > 0 { hs.last().body } else { none }
}

// Authors; an affiliation shared by all of them is shown once
#let names = meta.authors.map(a => a.name)
#let affiliations = meta.authors.map(a => a.affiliation).filter(a => a != "").dedup()
#let shared-affiliation = meta.authors.all(a => a.affiliation == meta.authors.first().affiliation)

#set document(title: meta.title, author: names)
#set page(
  paper: "us-letter",
  margin: (x: 1in, top: 1in, bottom: 0.9in),
  header: context {
    if counter(page).get().first() > 2 {
      set text(8pt, fill: muted, tracking: 0.04em)
      grid(
        columns: (1fr, auto),
        upper(meta.title), current-section(),
      )
      v(-0.4em)
      line(length: 100%, stroke: 0.5pt + hairline)
    }
  },
  footer: context {
    if counter(page).get().first() > 2 {
      set text(8.5pt, fill: muted)
      align(right, counter(page).display())
    }
  },
)
#set text(font: sans, size: 10.5pt, fill: ink, lang: "en")
#set par(justify: false, leading: 0.72em, spacing: 1.15em)
#show math.equation: set text(font: "New Computer Modern Math")

// Lists
#set list(marker: text(fill: accent, "•"), indent: 0.3em, body-indent: 0.6em, spacing: 0.8em)
#set enum(numbering: n => text(fill: accent, weight: "semibold", str(n) + "."), spacing: 0.8em)

// Term lists (overview "The main goal", "Dimension 1", ...)
#show terms.item: it => block(above: 1em, below: 0.6em)[
  #text(fill: accent, weight: "semibold", it.term)
  #pad(left: 0.9em, top: -0.2em, it.description)
]

// Headings
#show heading: set text(font: sans, fill: ink, hyphenate: false)
#show heading: set par(justify: false)

#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  let m = plain(it.body).match(regex("^(Dimension \d+):\s*(.*)$"))
  v(0.6in)
  if m != none {
    text(10pt, fill: accent, weight: "bold", tracking: 0.12em, upper(m.captures.at(0)))
    v(0.1em)
    text(26pt, weight: "bold", m.captures.at(1))
  } else {
    text(26pt, weight: "bold", it.body)
  }
  v(0.2em)
  box(width: 3em, height: 4pt, fill: warm, radius: 2pt)
  v(1.2em)
}

#show heading.where(level: 2): it => block(above: 2em, below: 0.9em, sticky: true)[
  #text(15pt, weight: "bold", fill: accent, it.body)
]

#show heading.where(level: 3): it => block(above: 1.6em, below: 0.7em, sticky: true)[
  #text(12pt, weight: "bold", it.body)
]

// PreTeXt <paragraphs> titles ("Mentors' Actions.") as small labels
#show heading.where(level: 4): it => block(above: 1.5em, below: 0.7em, sticky: true)[
  #show regex("\\.$"): none
  #text(8.5pt, weight: "bold", fill: muted, tracking: 0.1em, upper(it.body))
]

// Links
#show link: it => text(fill: accent, underline(stroke: 0.5pt + accent.lighten(50%), offset: 2pt, it))

// Figures and tables
#show figure.caption: it => text(9pt, fill: muted)[
  #if it.supplement != none [
    #text(weight: "bold", fill: accent)[#it.supplement #context it.counter.display(it.numbering)]
    #h(0.4em)
  ]
  #it.body
]
#show figure: set block(above: 1.6em, below: 1.6em)

#set table(
  stroke: (x, y) => (bottom: 0.5pt + hairline),
  fill: (x, y) => if y == 0 { accent } else if calc.even(y) { accent-soft.lighten(40%) },
  inset: (x: 9pt, y: 7pt),
)
#show table.cell: set align(left)
#show table.cell: set par(spacing: 0.5em)
#show table.cell.where(y: 0): set text(fill: white, weight: "bold")
#show table: set text(9.5pt)
// Tables without a header row: no header coloring
#show table: it => {
  if it.fill == none or it.children.any(c => c.func() == table.header) { it } else {
    let f = it.fields()
    let cells = f.remove("children")
    f.insert("fill", none)
    show table.cell.where(y: 0): set text(fill: ink, weight: "regular")
    table(..f, ..cells)
  }
}

// Title page
#page(margin: 0pt, header: none, footer: none)[
  #set par(justify: false)
  #block(width: 100%, height: 52%, fill: accent, inset: (x: 1in, top: 1.6in))[
    #set text(fill: white)
    #text(10pt, weight: "bold", tracking: 0.15em, upper(affiliations.join(" · ")))
    #v(0.8em)
    #text(34pt, weight: "bold", meta.title)
    #v(0.4em)
    #box(width: 3em, height: 5pt, fill: warm, radius: 2pt)
    #v(0.6em)
    #text(15pt, fill: white.darken(8%), meta.subtitle)
  ]
  #pad(x: 1in, top: 0.5in)[
    #grid(
      columns: (1fr, 2.6in),
      gutter: 0.5in,
      [
        #text(8.5pt, weight: "bold", fill: muted, tracking: 0.1em, "ABOUT")
        #v(0.2em)
        #text(11.5pt, meta.abstract)
        #v(1.5em)
        #text(8.5pt, weight: "bold", fill: muted, tracking: 0.1em,
          if names.len() == 1 { "AUTHOR" } else { "AUTHORS" })
        #v(0.2em)
        #for a in meta.authors [
          #text(11pt, weight: "semibold", a.name) \
          #if not shared-affiliation and a.affiliation != "" [
            #text(9.5pt, fill: muted, a.affiliation) \
          ]
        ]
        #v(0.6em)
        #text(9.5pt, fill: muted)[
          #if shared-affiliation and affiliations.len() > 0 [#affiliations.first() \ ]
          #meta.date
        ]
      ],
      image(meta.external + "/Diagram-Six-DimensionsCRT.png", width: 100%),
    )
  ]
]

// Contents
#page(header: none, footer: none)[
  #text(26pt, weight: "bold", "Contents")
  #v(0.2em)
  #box(width: 3em, height: 4pt, fill: warm, radius: 2pt)
  #v(1.2em)
  #set outline.entry(fill: none)
  #show outline.entry.where(level: 1): it => block(above: 1.1em, text(weight: "semibold", it))
  #show outline.entry.where(level: 2): set text(9.5pt, fill: muted)
  #outline(title: none, depth: 2, indent: 1.2em)
]

#counter(page).update(3)
#include "body.typ"
