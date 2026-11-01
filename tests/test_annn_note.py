"""annn's tasknotes (`annn <id>.note`) go through `nb tw` when the plugin is installed
(tw-nb-interop M4), and keep the old ~/.task/notes behaviour when it isn't."""
from pathlib import Path


def tasknotes(env):
    return sorted((env.nb_dir / 'tasknotes').rglob('*.note.md'))


def test_pipe_creates_the_nb_tasknote(env):
    uuid = env.add_task('--', 'Fix the billing discrepancy')
    env.annn('1.note', input='called the vendor\n')
    [p] = tasknotes(env)
    assert p.name == f'fix-the-billing-discrepancy-{uuid[:8]}.note.md'
    text = p.read_text()
    assert text.startswith(f'---\ntype: task\ntw: {uuid}\n')
    assert text.rstrip().endswith('called the vendor')
    anns = env.annotations(uuid)
    assert f'nb: tasknotes:{p.name}' in anns
    assert 'note: called the vendor' in anns, 'summary skips frontmatter and the title heading'
    assert env.git_clean('tasknotes')


def test_inline_appends_to_a_note_in_a_project_folder(env):
    uuid = env.add_task('project:kitchen', '--', 'Grout the backsplash')
    env.annn('1.note', 'first', 'line')
    env.annn('1.note', 'second', 'line')
    [p] = tasknotes(env)
    assert p.parent.name == 'kitchen', 'found in its folder, not a new root file'
    body = p.read_text()
    assert body.index('first line') < body.index('second line')
    assert [a for a in env.annotations(uuid) if a.startswith('note: ')] == ['note: first line']
    assert env.git_clean('tasknotes')


def test_empty_pipe_saves_nothing(env):
    uuid = env.add_task('--', 'Nothing to say')
    r = env.annn('1.note', input='')
    assert 'Empty input' in r.stdout
    assert tasknotes(env) == []
    assert env.annotations(uuid) == []


def test_remove_deletes_the_note_and_both_annotations(env):
    uuid = env.add_task('--', 'Drop this note')
    env.annn('1.note', input='temporary\n')
    [p] = tasknotes(env)
    env.annn('-1.note', input='y\n')
    assert not p.exists()
    assert not [a for a in env.annotations(uuid) if a.startswith(('note: ', 'nb: '))]
    assert env.git_clean('tasknotes')


def test_remove_without_a_note_creates_nothing(env):
    env.add_task('--', 'Never had one')
    env.annn('-1.note', input='n\n')
    assert tasknotes(env) == []


def test_without_the_plugin_annn_keeps_its_own_files(plain):
    uuid = plain.add_task('--', 'Old style')
    plain.annn('1.note', input='plain text\n')
    p = plain.home / '.task' / 'notes' / f'old-style-{uuid[:8]}.note.md'
    assert p.read_text() == 'plain text\n'
    assert 'note: plain text' in plain.annotations(uuid)
    assert tasknotes(plain) == []


def test_interactive_edit_opens_the_nb_note_and_commits(env, tmp_path):
    """From a terminal (script gives annn a pty), nb opens $EDITOR on the note and commits."""
    editor = tmp_path / 'editor.sh'
    editor.write_text('#!/bin/sh\nprintf "typed in the editor\\n" >> "$1"\n')
    editor.chmod(0o755)
    uuid = env.add_task('--', 'Edit me interactively')
    env.env['EDITOR'] = str(editor)
    from tests.conftest import REPO
    env.run('script', '-qec', f'{REPO / "annn"} 1.note', '/dev/null')
    [p] = tasknotes(env)
    assert p.read_text().rstrip().endswith('typed in the editor')
    assert 'note: typed in the editor' in env.annotations(uuid)
    assert env.git_clean('tasknotes')


def test_without_the_plugin_a_heading_is_still_the_summary(plain):
    uuid = plain.add_task('--', 'Headed')
    plain.annn('1.note', input='# Supplemental documents\nmore\n')
    assert 'note: # Supplemental documents' in plain.annotations(uuid)
