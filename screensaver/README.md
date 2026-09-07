# Animated ASCII screensaver

This optional helper uses Omarchy's installed `ttfx` engine and native screensaver launcher. It displays the supplied text-art scene with a slow blue → violet → muted red → blue color wave, at 12 frames per second and approximately 53 seconds per gradient cycle.

Install the theme first, then opt into the helper:

```bash
bash ~/.config/omarchy/themes/violet-oni/screensaver/install.sh
omarchy launch screensaver force
```

The helper is installed as `~/.local/bin/ttfx`. That directory must resolve before `/usr/bin` in the desktop's PATH. It intercepts only the native screensaver's exact branding-file invocation while `violet-oni` is selected and `screensaver/scene.txt` is present in the active theme. Other calls and other themes execute the original `/usr/bin/ttfx` with their arguments unchanged.

Theme installation alone never executes this installer. No packaged Omarchy files, idle timings, lock settings, or existing branding text are modified. Omarchy continues to launch one terminal per monitor and to control screensaver dismissal and the lock deadline.

To disable the helper reversibly:

```bash
mv ~/.local/bin/ttfx ~/.local/bin/violet-oni-ttfx.disabled
```

Only use this command if `~/.local/bin/ttfx` is the helper installed above. Running screensavers finish using the already-started engine; the next launch uses Omarchy's original random effects.
