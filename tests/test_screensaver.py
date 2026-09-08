"""Exercise routing without launching a desktop or changing user configuration."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class ScreensaverRouting(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="violet-oni-routing-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = os.environ.copy()
        self.env["XDG_STATE_HOME"] = str(self.root / ".state")
        self.engine = self.root / "engine"
        self.engine.write_text("#!/bin/bash\nprintf '%s\\0' \"$@\"\n")
        self.engine.chmod(0o755)
        source = (Path(__file__).parents[1] / "screensaver/ttfx").read_text()
        # Redirect filesystem references in a temporary copy; never reassign HOME.
        source = source.replace("engine=/usr/bin/ttfx", f'engine="{self.engine}"')
        source = source.replace("$HOME", str(self.root))
        self.wrapper = self.root / "ttfx"
        self.wrapper.write_text(source)
        self.state = self.root / ".local/state/omarchy/current"
        self.scene_dir = self.state / "theme/screensaver"
        self.scene_dir.mkdir(parents=True)
        self.scenes = []
        for name in ("scene-03-road-of-ashes.txt", "scene-04-last-light-valley.txt",
                     "scene-05-ruined-shrine-road.txt", "scene-06-moonlit-mountain-pass.txt"):
            scene = self.scene_dir / name
            scene.write_text(name + "\n")
            self.scenes.append(scene)
        (self.scene_dir / "scene.txt").write_text("legacy\n")
        (self.state / "theme.name").write_text("violet-oni\n")
        self.branding = str(self.root / ".config/omarchy/branding/screensaver.txt")
        self.native = ["-i", self.branding, "--frame-rate", "120", "--canvas-width", "0",
                       "--reuse-canvas", "--random-effect", "--no-eol", "--no-restore-cursor"]

    def run_args(self, args):
        result = subprocess.run(["bash", str(self.wrapper), *args], check=True,
                                capture_output=True, env=self.env)
        return result.stdout.decode().rstrip("\0").split("\0")

    def test_native_invocation_gets_shuffled_scene_and_moderate_effect(self):
        selected = []
        for _ in range(12):
            args = self.run_args(self.native)
            selected.append(args[args.index("-i") + 1])
            self.assertIn(selected[-1], {str(scene) for scene in self.scenes})
            self.assertEqual(args[args.index("--frame-rate") + 1], "24")
            self.assertNotIn("--random-effect", args)
            self.assertIn("colorshift", args)
            self.assertEqual(args[args.index("--gradient-frames") + 1], "8")
            self.assertIn("087cf2", args)
            self.assertIn("00d9ff", args)
            self.assertIn("ff2bd6", args)
            self.assertIn("00e676", args)
        self.assertTrue(all(a != b for a, b in zip(selected, selected[1:])))
        self.assertEqual(set(selected), {str(scene) for scene in self.scenes})
        self.assertIn("--reuse-canvas", args)
        self.assertIn("--no-restore-cursor", args)

    def test_other_theme_is_untouched(self):
        (self.state / "theme.name").write_text("osaka-jade\n")
        self.assertEqual(self.run_args(self.native), self.native)

    def test_missing_scene_is_untouched(self):
        for scene in self.scenes:
            scene.unlink()
        (self.scene_dir / "scene.txt").unlink()
        self.assertEqual(self.run_args(self.native), self.native)

    def test_ordinary_calls_are_untouched(self):
        for args in (["--help"], ["--version"], ["-i", "my-art.txt", "--random-effect"],
                     self.native[:-1], ["-i"], self.native + ["--frame-rate"]):
            with self.subTest(args=args):
                self.assertEqual(self.run_args(args), args)


if __name__ == "__main__":
    unittest.main()
