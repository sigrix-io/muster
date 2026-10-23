# Muster

A format for playbooks. A playbook is a process a business runs by hand, sold as the files a
person works through: the steps, the copy to send, the checklists and the tools that work
offline. One file, `playbook.json`, says what those files are and how they fit: the order a
person works through them, what each one is for, which ones are the same content in another
form, and the placeholders the buyer fills in.

This repository holds the format: its [JSON Schema](schemas/0.1/playbook.schema.json), a
[table of cases](schemas/0.1/playbook.cases.json) every implementation runs, and this README,
which says what the schema cannot. [Sigrix](https://sigrix.io) checks every playbook it is
given against the format, and serves the schema at its address.

## A playbook

A playbook is a folder, with `playbook.json` at its top beside the files it names:

```
moving-quote-follow-up/
├── playbook.json
├── README.md            guide
├── CHECKLIST.md         checklist
├── checklist.html       the same checklist, as a page that works offline
├── follow-up-steps.md   steps
├── reply-templates.md   copy
├── pricing-notes.md     reference
├── LICENSE.txt          license
└── CHANGELOG.md         changelog
```

It travels as a `.zip`, with `playbook.json` at the top of the zip or inside the one folder that
holds everything, as zipping a folder leaves it. Every entry is a plain file: no links to other
files, and no passwords.

## `playbook.json`

```json
{
  "format_version": "0.1",
  "name": "moving-quote-follow-up",
  "title": "Moving Quote Follow-Up",
  "order": [
    "README.md", "CHECKLIST.md", "checklist.html", "follow-up-steps.md",
    "reply-templates.md", "pricing-notes.md", "LICENSE.txt", "CHANGELOG.md"
  ],
  "files": [
    {"path": "README.md", "role": "guide"},
    {"path": "CHECKLIST.md", "role": "checklist"},
    {"path": "checklist.html", "role": "checklist", "same_as": "CHECKLIST.md", "self_contained": true},
    {"path": "follow-up-steps.md", "role": "steps"},
    {"path": "reply-templates.md", "role": "copy"},
    {"path": "pricing-notes.md", "role": "reference"},
    {"path": "LICENSE.txt", "role": "license"},
    {"path": "CHANGELOG.md", "role": "changelog"}
  ],
  "slots": {
    "setup": [
      {"placeholder": "[BUSINESS NAME]", "label": "Your business's name, as customers know it"},
      {"placeholder": "[PHONE]", "label": "The number customers call you on"},
      {"placeholder": "[CITY]", "label": "The city you work from"},
      {"placeholder": "[WEBSITE]", "label": "Your website's address"}
    ],
    "message": [
      {"placeholder": "[name]", "label": "The customer's first name"},
      {"placeholder": "[phone]", "label": "The number the customer left"},
      {"placeholder": "[from]", "label": "Where the move starts"},
      {"placeholder": "[to]", "label": "Where the move ends"},
      {"placeholder": "[date]", "label": "The day they want to move"},
      {"placeholder": "[crew]", "label": "The crew lead's first name"}
    ]
  },
  "examples_are_fictional": true
}
```

That is format 0.1, and the first valid case in the case table. Each member's `description` in
the schema says what it holds; in short:

| Member | Holds |
| --- | --- |
| `format_version` | `"0.1"`: the format, as `MAJOR.MINOR` |
| `name` | the playbook's name: lowercase letters, digits and single hyphens, at most 80 characters |
| `title` | the name a person sees, on one line, at most 200 characters |
| `order` | every file's path, once each, in the order a person works through them |
| `files` | each file, 1 to 100 of them, with its `path` and its `role` |
| `slots` | the placeholders the files use, in two lists that may be empty: `setup` and `message` |
| `examples_are_fictional` | whether every name, number and address in the files' examples is made up |

Every member is required.

### Files

A `path` is relative to the folder, with `/` between folders, and at most 200 characters. Each
part starts with a letter, a digit or `_`, and goes on in letters, digits, spaces and
`. _ ( ) + -`. A file is `.md`, `.txt`, `.csv` or `.html`, in any case.

Each file has one `role`:

| Role | The file is |
| --- | --- |
| `guide` | the guide to the playbook |
| `steps` | the steps to follow |
| `checklist` | a checklist to work through |
| `copy` | the copy to use: messages and replies, ready to fill in |
| `reference` | reference material |
| `tool` | a tool to work in |
| `license` | the license that says how the buyer may use the files |
| `changelog` | what changed in each version |

`same_as` names another file whose content this one presents in another form, such as a
`checklist.html` beside `CHECKLIST.md`.

`self_contained` is an `.html` file's promise that it loads nothing from the network. Every
`.html` file makes it, as `true`, and no other file carries it.

### Placeholders

A placeholder is a token in square brackets that the buyer replaces with their own words: a
letter, then up to 39 letters, digits, spaces, `_` or `-`. Case is part of it: `[PHONE]` and
`[phone]` are two placeholders. Each has a `label`, one line saying what it stands for, and is
declared in one of two lists:

- `setup`: filled in once, for the buyer's business, such as `[BUSINESS NAME]`.
- `message`: filled in each time the files are used, such as the `[name]` of the person a
  reply goes to.

## What the schema cannot say

JSON Schema checks one document. A playbook is also its files, and a writer keeps these rules
too. A checker refuses a playbook that breaks any of them.

The document:

- `order` names every file in `files` once, and nothing else.
- No two files share a path. Paths are compared ignoring case, since macOS and Windows hold
  `README.md` and `readme.md` as one file.
- `same_as` names another file in `files`: not the file itself, and not one that is itself the
  same as another. The file has that file's `role`.
- A placeholder is declared once, in `setup` or in `message`.

The files:

- Every file `files` names is in the folder, and the folder holds nothing else beside
  `playbook.json`. What an operating system adds to a folder is ignored: `__MACOSX/`,
  `.DS_Store`, `Thumbs.db`, `desktop.ini` and names starting `._`.
- Every file is UTF-8 text.
- Every placeholder a file uses is declared, written the same way, and every declared one is
  used. Markdown's own brackets are not placeholders: a link (`[text](address)`,
  `[text][label]`, or a `[label]` that a link definition in the file names), an image, an
  escaped `\[`, and a task mark (`[x]`). Nor is anything in an `.html` file's stylesheets,
  scripts or comments, where `[hidden]` is a selector.
- An `.html` file works offline. Its markup loads nothing from outside the file: no
  stylesheet, font, image, frame, form action or `url()`. A `data:` address is inside the file,
  and a link the reader follows is not a load.
- An `.html` file that runs a script (a `<script>`, an `on…=` handler or a `javascript:`
  address) carries a Content-Security-Policy in its `<head>`, before any script, that blocks
  every request. This line does:

  ```html
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; form-action 'none'">
  ```

  Another policy does too if `default-src` and `form-action` are `'none'` and no directive
  allows a host, a scheme other than `data:` and `blob:`, `'self'`, `*`, `'strict-dynamic'` or a
  reporting address. A policy after a script, in the `<body>`, inside a `<template>` or a
  `<noscript>`, or Report-Only, is none, because a browser applies none of them to the scripts.
  A script kept in a `data:` address is refused, since nobody can read it.

The buyer's browser holds the file to its policy. A policy cannot stop a script sending the page
somewhere else, so a store that sells a playbook reads its scripts.

## Versions

`format_version` is `MAJOR.MINOR`, and a reader treats it this way:

- It refuses a major version it does not know.
- It ignores a member it does not know. A minor version only adds members, so a reader that
  knows 0.1 reads a 0.2 document as the 0.1 document inside it. A change a reader cannot ignore
  moves the major.

So the schema is a reader's view: its objects are open, and `format_version` admits any `0.x`.
Do not generate a writer's types from it. A writer writes the members its version defines.

Each version is a directory under `schemas/`, and a new version is a new directory beside the
old ones, never an edit in place: `schemas/0.1/` is the format a 0.1 document names.

## The schema's address

The schema's `$id` is `https://sigrix.io/schemas/muster/0.1/playbook.schema.json`. It is
permanent: it is never reused for anything else, and it resolves, because Sigrix copies
`schemas/0.1/` and serves the schema there. The document at it may be corrected; a change here
is then a change there too, and the pull request making one says so.

## The case table

[`schemas/0.1/playbook.cases.json`](schemas/0.1/playbook.cases.json) holds the cases every
implementation agrees on. `valid` lists documents that validate. Each entry in `invalid` names a
valid case as its `base` and one RFC 6902 `add`, `replace` or `remove` as its `change`, so it
fails for that change and nothing else.

[`tests/test_playbook_schema.py`](tests/test_playbook_schema.py) runs the table against the
schema with `jsonschema`, and checks the table itself: every member appears in a valid case, and
every required member has a case without it, wherever its object sits. An implementation with a
checker of its own runs the same table against that checker, so the two cannot quietly disagree
about what the format allows; Sigrix's does. A change to the schema comes with the cases that
show it.

## Where it fits

Muster is one of the open-source projects [Sigrix](https://sigrix.io) publishes. Its neighbours:

- **[Sigrix](https://sigrix.io)**, which checks every playbook uploaded to it against Muster, with a checker of its own
  held to the case table above, and serves the schema at its address.
- **[Gatehouse](https://github.com/sigrix-io/gatehouse)**, the browser client whose playbook block draws what a playbook
  holds, its files in order and the placeholders a buyer fills in, from its `playbook.json`.

Every project Sigrix publishes, and a map of how they connect: [sigrix.io/open-source](https://sigrix.io/open-source).

## Working on it

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check . && python -m ruff format --check .
python -m pytest
```

## License

The format, its schema and its cases are under the Apache License 2.0: see [LICENSE](LICENSE)
and [NOTICE](NOTICE). A playbook written in the format is its author's, under the license its
`license` file gives.
