#!/usr/bin/env python3
"""Synchronized playback of native ttfx frames; no daemon or extra packages."""
import ctypes
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import re
import shutil
import signal
import subprocess
import sys
import time

FPS = 24
DURATION = 11.0
HOLD = 2.0
COLORS = ['087cf2', '00d9ff', '7c3aed', 'ff2bd6', 'ff3b30', '00e676', '087cf2']
CONTROL = re.compile(r'\x1b(?:\[[0-?]*[ -/]*[A-ln-zA-Z]|[78])')
child = None


def next_scene(state, names, rng):
    if not state.get('bag'):
        state['bag'] = list(names)
        rng.shuffle(state['bag'])
        if len(names) > 1 and state['bag'][0] == state.get('scene'):
            state['bag'][0], state['bag'][1] = state['bag'][1], state['bag'][0]
    return state['bag'].pop(0)


def alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except ProcessLookupError:
        return False


def barrier(state, now):
    state['members'] = {p: m for p, m in state['members'].items()
                        if alive(p) and now - m['heartbeat'] < 10}
    if state['members'] and all(m['done'] for m in state['members'].values()):
        if state.get('hold_until') is None:
            state['hold_until'] = now + HOLD
        return now >= state['hold_until']
    return False


def render(scene, seed):
    global child
    command = ['/usr/bin/ttfx', '-i', str(scene), '--seed', str(seed),
               '--frame-rate', '0', '--canvas-width', '120', '--canvas-height', '40',
               '--ignore-terminal-dimensions', '--anchor-text', 'c', '--reuse-canvas',
               '--no-eol', '--no-restore-cursor', 'scattered', '--movement-speed', '0.5',
               '--movement-easing', 'in_out_sine', '--final-gradient-stops', *COLORS,
               '--final-gradient-steps', '8', '--final-gradient-frames', '2',
               '--final-gradient-direction', 'diagonal']
    child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        output, error = child.communicate(timeout=15)
        if child.returncode:
            raise RuntimeError(error.decode())
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()
        child = None
    frames = [CONTROL.sub('', f).splitlines() for f in output.decode().split('\x1b8')[1:]]
    frames = [f for f in frames if f]
    if not frames:
        raise RuntimeError('ttfx returned no animation frames')
    return frames


def display(lines):
    size = shutil.get_terminal_size((120, 40))
    top = max(0, (size.lines - 40) // 2)
    left = max(0, (size.columns - 120) // 2)
    return ''.join(f'\x1b[{top + i + 1};{left + 1}H{line}\x1b[0m'
                   for i, line in enumerate(lines[:size.lines]))


def stop(*_):
    raise SystemExit(0)


def main():
    # Omarchy monitors and kills processes named ttfx on each terminal.
    ctypes.CDLL(None).prctl(15, b'ttfx', 0, 0, 0)
    for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT, signal.SIGQUIT):
        signal.signal(sig, stop)
    scene_dir = Path(sys.argv[1])
    scenes = {p.name: p for p in sorted(scene_dir.glob('*.txt')) if p.is_file() and p.stat().st_size}
    if not scenes:
        raise RuntimeError('No readable screensaver scenes')
    signature = hashlib.sha256(b''.join(p.read_bytes() for p in scenes.values())).hexdigest()
    root = Path(os.environ.get('XDG_RUNTIME_DIR', str(Path.home() / '.cache'))) / 'violet-oni-sync'
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    # The native launcher can briefly spawn twice before Python sets its name.
    # Keep exactly one player per terminal for the entire session.
    terminal = os.ttyname(sys.stdout.fileno()) if sys.stdout.isatty() else str(os.getpid())
    terminal_lock = (root / ('terminal-' + hashlib.sha256(terminal.encode()).hexdigest() + '.lock')).open('a')
    try:
        fcntl.flock(terminal_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        terminal_lock.close()
        return
    state_path = root / 'session.json'
    pid = str(os.getpid())
    generation = None
    last_frame = None
    frames = []
    rng = random.SystemRandom()
    sys.stdout.write('\x1b[?25l\x1b[2J')
    try:
        while True:
            with (root / 'session.lock').open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                now = time.monotonic()
                try:
                    state = json.loads(state_path.read_text())
                except (FileNotFoundError, ValueError):
                    state = {}
                living = {p: m for p, m in state.get('members', {}).items()
                          if alive(p) and now - m['heartbeat'] < 10}
                if not living or state.get('signature') != signature:
                    state = {'members': {}, 'signature': signature, 'generation': 0, 'history': []}
                else:
                    state['members'] = living
                state['members'][pid] = {'heartbeat': now,
                                        'done': generation == state['generation'] and last_frame == len(frames) - 1}
                advance = barrier(state, now) if state.get('scene') else True
                if advance:
                    state['scene'] = next_scene(state, list(scenes), rng)
                    state['seed'] = rng.randrange(2**31)
                    rendered = render(scenes[state['scene']], state['seed'])
                    (root / 'frames.json').write_text(json.dumps(rendered))
                    state['generation'] += 1
                    state['start'] = time.monotonic() + 0.8
                    state['hold_until'] = None
                    for member in state['members'].values():
                        member['done'] = False
                        member['heartbeat'] = time.monotonic()
                    state['history'] = (state['history'] + [state['scene']])[-12:]
                if generation != state['generation']:
                    frames = json.loads((root / 'frames.json').read_text())
                    generation = state['generation']
                    last_frame = None
                state_path.write_text(json.dumps(state))
                start = state['start']
            elapsed = time.monotonic() - start
            if elapsed >= 0:
                index = min(len(frames) - 1, int(elapsed / DURATION * (len(frames) - 1)))
                if index != last_frame:
                    sys.stdout.write(display(frames[index]))
                    sys.stdout.flush()
                    last_frame = index
            time.sleep(1 / FPS)
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=1)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        with (root / 'session.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                state = json.loads(state_path.read_text())
                state.get('members', {}).pop(pid, None)
                state_path.write_text(json.dumps(state))
            except (FileNotFoundError, ValueError):
                pass
        sys.stdout.write('\x1b[0m\x1b[?25h')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
