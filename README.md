- Project: https://github.com/linuxcaffe/tw-ann-hook
- Issues:  https://github.com/linuxcaffe/tw-ann-hook/issues

# annn

A compact annotation manager for Taskwarrior — create, list, edit, and remove
annotations from your terminal, with an optional hook for auto-prompting on
task completion or deletion.

---

## TL;DR

- Create and edit annotations in your editor, not inline
- Pipe annotations directly: `echo "quick note" | annn 42`
- List annotations with numbered indexes
- Remove annotations with confirmation
- Compact dot-syntax: `annn 42.1` to edit, `annn -42.1` to remove
- Label syntax: `annn 42.status` to edit/create the `status:` annotation
- Templates: `~/.task/templates/<label>.md` pre-populates the editor
- Tasknotes: `annn 42.note` opens a persistent file in `~/.task/notes/`
- Optional hook: auto-prompt for annotation when completing or deleting `+ann` tasks
- Works standalone or as a tw wrapper: `tw 42 ann.1`
- Designed for Taskwarrior 2.6.2

---

## Why this exists

Taskwarrior's built-in `annotate` command works, but it's limited to a single
inline string. There's no way to edit an existing annotation, no way to pick
one by index, and writing anything longer than a sentence on the command line
is painful.

`annn` makes annotations a first-class workflow — open your editor, write what
you need, and get back to work. The companion hook ensures you never forget to
document why a task was completed or deleted.

---

## Three components

### 1. `annn` — CLI annotation manager

A standalone bash script for creating, listing, editing, and removing
annotations by index. Supports both interactive (editor) and non-interactive
(pipe) input.

### 2. `on-exit_annn.py` — Auto-annotation hook

A Taskwarrior on-exit hook that watches for tasks tagged `+ann`. When one is
completed or deleted, it opens your editor for a final annotation — a closing
note, a reason for deletion, or whatever context you want to preserve.

### 3. tw wrapper integration

When installed via awesome-taskwarrior, `annn` registers as a tw wrapper,
enabling `tw 42 ann.1` syntax. tw dispatches to `annn` automatically — no
changes to tw required.

Each component works independently. Use one, two, or all three.

---

## CLI usage

```
annn <id>                  New annotation (opens $EDITOR, prompts for label)
annn <id>.                 List annotations with index numbers
annn <id>.<N>              Edit annotation N by index
annn <id>.<label>          Edit/create annotation by label
annn -<id>.<N>             Remove annotation N (with confirmation)
annn -<id>.<label>         Remove annotation by label (with confirmation)
echo "text" | annn <id>    Annotate from pipe (no editor)
echo "text" | annn <id>.<label>  Pipe with label prefix

annn <id>.note             Open/create the task's note file in $EDITOR
annn <id>.note text...     Append inline text to the note (no editor)
echo "text" | annn <id>.note     Append piped text to the note
annn -<id>.note            Remove the note annotation and file (with confirmation)
```

Space-separated form also works: `annn 42 .1` is the same as `annn 42.1`.

When opening the editor, `annn` shows the task context with annotation count:

```
[annn] Task 42: assemble realed expenses (3 annotations)
```

The editor opens a descriptively named temp file so you always know what
you're annotating:

```
/tmp/annn_42_assemble-realed-expenses.Xk9f3m.md
```

---

## CLI examples

Add a new annotation to task 42:

```bash
annn 42
# [annn] Task 42: assemble realed expenses (2 annotations)
# Editor opens — write your annotation, save, quit
# [annn] Annotation added to task 42
```

Pipe a quick note without opening the editor:

```bash
echo "called vendor, waiting for callback" | annn 42
# [annn] Annotation added to task 42
```

Pipe command output:

```bash
git log --oneline -1 | annn 42
date "+Started %Y-%m-%d %H:%M" | annn 42
```

List annotations on task 42:

```bash
annn 42.
# Task 42: assemble realed expenses
# ---
#   .1   [2026-02-17 12:52]
#        first annotation text
#
#   .2   [2026-02-17 13:10]
#        second annotation text
```

Edit the first annotation:

```bash
annn 42.1
# [annn] Task 42: assemble realed expenses (2 annotations)
# Editor opens with current text — edit, save, quit
# [annn] Annotation .1 updated on task 42
```

Remove the second annotation:

```bash
annn -42.2
# Task 42: assemble realed expenses
# ---
#   .2   [2026-02-17 13:10]
#        second annotation text
#
# Remove this annotation? [y/N]: y
# [annn] Annotation .2 removed from task 42
```

---

## Labels

An annotation label is a leading `word: ` prefix — a single word followed by
a colon and space at the start of the annotation text:

```
status: blocked waiting for vendor callback
link: https://ticket.example.com/TKT-42
reason: duplicate of task 17
```

Labels are entirely optional. Any annotation can have one, none are required,
and they can be added by `annn` or by any other means. The label is just part
of the annotation text — no UDAs or extra configuration needed.

**`note:` is special** — it activates the tasknotes feature (see below).

### Addressing by label

```bash
annn 42.status           # edit the "status:" annotation (create if absent)
annn 42.status text...   # set inline: saves as "status: text..."
echo "url" | annn 42.link  # pipe: saves as "link: url"
annn -42.status          # remove the "status:" annotation
```

If no `status:` annotation exists, `annn` opens the editor pre-populated with
`status: ` so the label is already in place.

If multiple annotations share the same label, `annn` lists them and prompts
for a selection before editing or removing.

### Label prompt on new annotations

When creating a new annotation interactively (`annn 42`), `annn` offers an
optional label prompt before opening the editor:

```
[annn] Task 42: Fix billing discrepancy (1 annotation)
[annn] Label (optional, e.g. status, link — Enter to skip):
```

Press Enter to skip; type a label name to pre-populate the editor with
`label: `. Typing `note` at this prompt opens the tasknotes editor instead.

### List display

Labels are highlighted in the annotation list:

```bash
annn 42.
# Task 42: Fix billing discrepancy
# ---
#   .1   [2026-02-17 12:52]
#        status: blocked waiting for vendor callback
#
#   .2   [2026-02-17 13:10]
#        link: https://ticket.example.com/TKT-42
#
#   .3   [2026-02-17 14:00]
#        general note without a label
```

---

## Templates

If `~/.task/templates/<label>.md` exists, `annn` pre-populates the editor with
that file's content when creating a new labeled annotation interactively.

```bash
# ~/.task/templates/status.md
status:

Next actions:
-
```

```bash
annn 42.status    # editor opens with status.md content
annn 42.link      # no template → editor opens with "link: "
```

Templates are freeform — include the `label: ` prefix or not, add structure,
checklists, whatever serves the workflow. The `note:` template lives at
`~/.task/templates/note.md` and is applied when creating a new tasknote.

Pipe and inline paths are unaffected by templates (no editor is opened).

---

## Tasknotes

The `note:` label is special. Instead of storing content inline in the
Taskwarrior annotation, `annn 42.note` opens a persistent Markdown file:

```
~/.task/notes/<task-slug>-<uuid8>.note.md
```

After the editor closes, `annn` writes a summary annotation to the task:

```
note: <first line of the note file>
```

This keeps the task list readable while the full note is always a
`annn 42.note` away.

### Tasknote examples

```bash
annn 42.note
# [annn] Task 42: Fix billing discrepancy (1 annotation)
# Editor opens ~/.task/notes/fix-billing-discrepancy-a3f9c2b1.note.md
# [annn] Note created: ~/.task/notes/fix-billing-discrepancy-a3f9c2b1.note.md

annn 42.note
# (file already exists — editor opens it directly)
# [annn] Note updated: ~/.task/notes/fix-billing-discrepancy-a3f9c2b1.note.md

echo "see ticket TKT-99" | annn 42.note
# Appends to the note file, updates annotation
# [annn] Note updated for task 42

annn 42.note Followed up with vendor
# Appends inline text to note, updates annotation, no editor

annn -42.note
# Task 42: Fix billing discrepancy
# ---
# Note file: ~/.task/notes/fix-billing-discrepancy-a3f9c2b1.note.md
#   Followed up with vendor
#
# Remove note annotation and file? [y/N]: y
# [annn] Note annotation removed from task 42
# [annn] Note file deleted: ~/.task/notes/fix-billing-discrepancy-a3f9c2b1.note.md
```

The note filename is derived deterministically from the task description and
UUID — it's always findable from the task ID, even without `annn`.

---

## tw wrapper usage

When installed via awesome-taskwarrior, all `annn` commands are available
through tw:

```bash
tw 42 ann            # new annotation
tw 42 ann.           # list annotations
tw 42 ann.1          # edit annotation 1
tw 42 -ann.1         # remove annotation 1
tw 42 ann.status     # edit/create "status:" annotation
tw 42 -ann.status    # remove "status:" annotation
tw 42 ann.note       # open/create tasknote
tw 42 -ann.note      # remove tasknote and file
echo "note" | tw 42 ann         # pipe input
echo "url" | tw 42 ann.link     # pipe with label
echo "detail" | tw 42 ann.note  # append to tasknote
```

tw detects the `ann` keyword, translates the arguments, and dispatches to
`annn`. The wrapper registration happens automatically during installation.

---

## Hook usage

Tag any task with `+ann` to enable auto-annotation:

```bash
task add "Resolve billing dispute" +ann due:friday
```

When you complete or delete it, the hook opens your editor:

```bash
task 42 done
# [annn] Task 42: Resolve billing dispute
# [annn] Event: completed
# [annn] Opening editor for annotation...
#
# (editor opens — write your closing note, save, quit)
#
# [annn] Annotation saved.
```

The annotation is saved to the task after the editor closes. Empty saves
are skipped. The hook uses `rc.hooks=off` when saving to avoid re-triggering
itself.

The editor opens on your terminal (`/dev/tty`), since Taskwarrior gives hooks
pipes. In a client without a terminal (tw-web, vit: `TW_NOINTERACT=1`) the task
is completed or deleted as usual, and the hook leaves the editor step in the
client's spool (`TW_SPOOL_DIR`): the client offers to run it in a terminal
afterwards. See awesome-taskwarrior's
[CONVENTIONS.md](https://github.com/linuxcaffe/awesome-taskwarrior/blob/main/CONVENTIONS.md).

---

## Configuration

The hook reads `annn.rc` for settings:

```ini
# Tag that triggers auto-annotation (default: ann)
annn.tag=ann

# Trigger on task completion (default: yes)
annn.on_complete=yes

# Trigger on task deletion (default: yes)
annn.on_delete=yes

# Editor override (leave empty for $EDITOR, defaults to vim)
annn.editor=
```

---

## Installation

### CLI only

Copy `annn` somewhere on your `$PATH`:

```bash
cp annn ~/.local/bin/
chmod +x ~/.local/bin/annn
```

Create the notes and templates directories:

```bash
mkdir -p ~/.task/notes ~/.task/templates
```

### Hook

```bash
cp on-exit_annn.py ~/.task/hooks/
chmod +x ~/.task/hooks/on-exit_annn.py
cp annn.rc ~/.task/config/
echo 'include ~/.task/config/annn.rc' >> ~/.taskrc
```

### Via awesome-taskwarrior (recommended)

```bash
tw --install annn
```

This installs all components and registers the tw wrapper automatically.

**Requirements:**
- Taskwarrior 2.6.2
- Bash 4.0+ (CLI)
- Python 3.6+ (hook)
- A terminal editor (`$EDITOR` or vim)

---

## Debugging

Enable debug logging for the hook:

```bash
export DEBUG_ANNN=1
task 42 done
cat ~/.task/logs/debug/annn_debug.log
```

---

## Project status

Working and stable for daily use.

The annotation API in Taskwarrior 2.6.2 has some inherent limitations
(denotation matches by text content, not by index), but `annn` handles
these edge cases gracefully.

---

## Metadata

- Version: 0.7.1
- License: MIT
- Language: Bash (CLI), Python (hook)
- Interface: CLI + `$EDITOR`
- Platforms: Linux
