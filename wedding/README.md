# Wedding photobooth

Live camera preview → countdown → 4 photos with a delay between each → printed as a photobooth strip.

```sh
pip install -r requirements.txt          # from the repo root
python -m wedding.photobooth --title "Sam & Alex" --subtitle "June 20, 2027"
python -m wedding.photobooth --no-print --windowed   # test without the printer
```

Press **SPACE/ENTER** to start a session, **Q/ESC** to quit. A USB "big red button" that sends a key press works as the trigger.

The booth uses the first camera that gives a real picture. It prints `Using camera N` at startup; to force a particular camera, pass `--camera N`. On a Mac, an iPhone nearby can show up as camera 0 (Continuity Camera) and send only black frames, so the booth skips it.

Each session's raw shots and the final `strip.png` are saved to `wedding/output/<timestamp>/` (git-ignored).

Useful flags: `--delay 3` (seconds between shots), `--countdown 5` (before the first shot),
`--style dither|lines|combo`, `--aspect 4:3`, `--footer "Thanks for coming!"`. See `--help` for all of them.
