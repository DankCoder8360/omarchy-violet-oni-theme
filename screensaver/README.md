# Four synchronized ASCII scenes

Road of Ashes, Wind and Steel, Broken Crossing, and Spirit Lanterns assemble from moving RGB braille characters. Both monitors share the same scene, animation frames, seed, and clock. Each animation lasts 11 seconds at 24 FPS; the completed art remains for two seconds after all active players finish.

Each shuffled cycle contains all four scenes, with no repeat at the cycle boundary. Only files in `screensaver/scenes/` are active. Older text files remain archived outside that directory.

## Install or update

After installing and selecting Violet Oni:

```bash
bash ~/.config/omarchy/themes/violet-oni/screensaver/install.sh
omarchy launch screensaver force
```

The installer backs up an older Violet Oni helper before updating it. Unrelated existing helpers are refused. To disable reversibly, rename the installed Violet Oni helper:

```bash
mv ~/.local/bin/ttfx ~/.local/bin/violet-oni-ttfx.disabled
```

## Integration

The helper intercepts only Omarchy's native branding-file screensaver call while Violet Oni is selected and the controller is present. Other themes and ordinary ttfx calls pass through to /usr/bin/ttfx.

The Python standard-library controller renders a shared finite animation with the native ttfx engine, then plays the same cached frames on each terminal using a common monotonic clock. Artwork is centered on a 120 × 40 canvas. A session barrier waits for all living players and the viewing pause; exited players are removed, and unresponsive players expire after ten seconds. Late arrivals join the current animation.

Temporary shared state and the current frame cache live in `$XDG_RUNTIME_DIR/violet-oni-sync` (or `~/.cache/violet-oni-sync` when unavailable). No background daemon is installed. Controller processes use the name ttfx so Omarchy retains its native input, focus, and lock dismissal behavior. Signals terminate rendering children and unregister the player.

No packaged Omarchy files, idle timings, lock settings, or branding files are changed. Existing screenshots of older versions remain historical references. See [artwork prompts](PROMPTS.md).
