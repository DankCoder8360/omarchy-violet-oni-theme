# Animated ASCII screensaver

This optional helper uses Omarchy's installed `ttfx` engine and native screensaver launcher. It shuffles four supplied text-art scenes, suppressing immediate repeats. Each pass takes approximately 11 seconds with a moderate reveal and a rich electric-blue → cyan → violet → magenta → red → green color wave at 24 frames per second.

Install the theme first, then opt into the helper:

```bash
bash ~/.config/omarchy/themes/violet-oni/screensaver/install.sh
omarchy launch screensaver force
```

The helper is installed as `~/.local/bin/ttfx`. That directory must resolve before `/usr/bin` in the desktop's PATH. It intercepts only the native screensaver's exact branding-file invocation while `violet-oni` is selected and at least one `scene-*.txt` file is present in the active theme. Other calls and other themes execute the original `/usr/bin/ttfx` with their arguments unchanged.

The four bundled scenes are `scene-03-road-of-ashes.txt`, `scene-04-last-light-valley.txt`, `scene-05-ruined-shrine-road.txt`, and `scene-06-moonlit-mountain-pass.txt`. The last selected path is stored under `${XDG_STATE_HOME:-~/.local/state}/omarchy/violet-oni-screensaver/last-scene` so simultaneous monitor launches can coordinate without changing the theme files.

Theme installation alone never executes this installer. No packaged Omarchy files, idle timings, lock settings, or existing branding text are modified. Omarchy continues to launch one terminal per monitor and to control screensaver dismissal and the lock deadline.

To disable the helper reversibly:

```bash
mv ~/.local/bin/ttfx ~/.local/bin/violet-oni-ttfx.disabled
```

Only use this command if `~/.local/bin/ttfx` is the helper installed above. Running screensavers finish using the already-started engine; the next launch uses Omarchy's original random effects.
