"""Routing, full-cycle selection, barriers, and real engine frame validation."""
import importlib.util
import os
from pathlib import Path
import random
import re
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("controller", ROOT / "screensaver/controller.py")
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)


class Scenes(unittest.TestCase):
    def test_full_cycles_and_boundary(self):
        state = {}
        rng = random.Random(42)
        names = ["road", "wind", "bridge", "spirit"]
        previous = None
        for _ in range(100):
            cycle = []
            for _ in names:
                chosen = controller.next_scene(state, names, rng)
                self.assertNotEqual(previous, chosen)
                state["scene"] = chosen
                previous = chosen
                cycle.append(chosen)
            self.assertEqual(set(cycle), set(names))

    def test_barrier_holds_and_removes_closed_monitor(self):
        state = {"members": {"1": {"done": True, "heartbeat": 100},
                             "2": {"done": False, "heartbeat": 100}}}
        with patch.object(controller, "alive", return_value=True):
            self.assertFalse(controller.barrier(state, 100))
        with patch.object(controller, "alive", side_effect=lambda pid: pid == "1"):
            self.assertFalse(controller.barrier(state, 101))
            self.assertFalse(controller.barrier(state, 102))
            self.assertTrue(controller.barrier(state, 103))

    def test_four_unique_sources_and_real_movement(self):
        scenes = sorted((ROOT / "screensaver/scenes").glob("*.txt"))
        self.assertEqual(len(scenes), 4)
        self.assertEqual(len({p.read_bytes() for p in scenes}), 4)
        for scene in scenes:
            frames = controller.render(scene, 42)
            layouts = {re.sub(r"\x1b\[[0-9;]+m", "", "\n".join(f)) for f in frames}
            self.assertGreater(len(layouts), 50)
            self.assertEqual(len(frames[-1]), 40)


class Routing(unittest.TestCase):
    def test_native_and_passthrough(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / ".local/state/omarchy/current"
            scene_dir = state / "theme/screensaver/scenes"
            scene_dir.mkdir(parents=True)
            (scene_dir / "01-road-of-ashes.txt").write_text("art")
            ctrl = state / "theme/screensaver/controller.py"
            ctrl.write_text("controller")
            name = state / "theme.name"
            name.write_text("violet-oni\n")
            engine = root / "engine"
            engine.write_text('#!/bin/bash\nprintf "%s\\0" "$@"\n')
            engine.chmod(0o755)
            source = (ROOT / "screensaver/ttfx").read_text().replace("$HOME", str(root))
            source = source.replace("engine=/usr/bin/ttfx", f"engine={engine}")
            source = source.replace("/usr/bin/python3", str(engine))
            wrapper = root / "ttfx"
            wrapper.write_text(source)
            branding = str(root / ".config/omarchy/branding/screensaver.txt")
            native = ["-i", branding, "--frame-rate", "120", "--random-effect", "--no-restore-cursor"]
            def run(args):
                result = subprocess.run(["bash", str(wrapper), *args], check=True, capture_output=True)
                return result.stdout.decode().rstrip("\0").split("\0")
            self.assertEqual(run(native), [str(ctrl), str(scene_dir)])
            for args in (["--help"], ["-i"], native[:-1], native + ["--frame-rate"]):
                self.assertEqual(run(args), args)
            name.write_text("other\n")
            self.assertEqual(run(native), native)
            name.write_text("violet-oni\n")
            ctrl.unlink()
            self.assertEqual(run(native), native)


if __name__ == "__main__":
    unittest.main()
