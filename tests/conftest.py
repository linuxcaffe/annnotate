"""Throwaway HOME with nb, the nb-plugins tw.nb-plugin and Taskwarrior, for annn's tasknote
tests. Nothing touches the real ~/.nb or ~/.task. NB_PLUGIN may point at the plugin under test
(default: the sibling checkout ~/dev/nb-plugins)."""
import json
import os
import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PLUGIN = Path(os.environ.get('NB_PLUGIN', REPO.parent / 'nb-plugins' / 'tw.nb-plugin'))
ANSI = re.compile(r'\x1b\[[0-9;?]*[A-Za-z]|\x1b\([A-Za-z0-9]')


class Env:
    def __init__(self, root):
        self.home = root / 'home'
        self.nb_dir = self.home / '.nb'
        self.task_dir = root / 'task'
        self.env = {'PATH': os.environ['PATH'], 'HOME': str(self.home), 'NB_DIR': str(self.nb_dir),
                    'NBRC_PATH': str(self.home / '.nbrc'), 'TASKRC': str(self.home / '.taskrc'),
                    'EDITOR': 'true', 'LANG': os.environ.get('LANG', 'C.UTF-8')}

    def run(self, *args, input=None, check=True):
        r = subprocess.run(list(args), capture_output=True, text=True, env=self.env, timeout=60,
                           input=input if input is not None else '')
        r.stdout, r.stderr = ANSI.sub('', r.stdout), ANSI.sub('', r.stderr)
        if check and r.returncode:
            raise AssertionError(f'{args} -> {r.returncode}\n{r.stdout}\n{r.stderr}')
        return r

    def annn(self, *args, input=None, check=True):
        return self.run(str(REPO / 'annn'), *args, input=input, check=check)

    def task(self, *args, check=True):
        return self.run('task', 'rc.hooks=off', *args, check=check)

    def add_task(self, *words):
        out = self.task('rc.verbose=new-uuid', 'add', *words).stdout
        return re.search(r'Created task ([0-9a-f-]{36})', out).group(1)

    def annotations(self, uuid):
        t = json.loads(self.task('rc.json.array=on', uuid, 'export').stdout)[0]
        return [a['description'] for a in t.get('annotations', [])]

    def git_clean(self, nb):
        return self.run('git', '-C', str(self.nb_dir / nb), 'status', '--porcelain').stdout == ''


def _base(tmp_path):
    e = Env(tmp_path)
    e.home.mkdir()
    e.task_dir.mkdir()
    (e.home / '.taskrc').write_text(f'data.location={e.task_dir}\nconfirmation=off\n')
    e.run('git', 'config', '--global', 'user.name', 'Pat Smith')
    e.run('git', 'config', '--global', 'user.email', 'pat@example.com')
    e.run('nb', 'notebooks', '--names')
    e.run('nb', 'notebooks', 'add', 'tasknotes')
    return e


@pytest.fixture
def env(tmp_path):
    e = _base(tmp_path)
    (e.nb_dir / '.plugins').mkdir(exist_ok=True)
    (e.nb_dir / '.plugins' / 'tw.nb-plugin').symlink_to(PLUGIN)
    return e


@pytest.fixture
def plain(tmp_path):
    """No tw.nb-plugin: annn keeps its own ~/.task/notes files."""
    return _base(tmp_path)
