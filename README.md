# Morning Paper podcast

An **unlisted** podcast feed for *Morning Paper*, hosted as static files on GitHub Pages.

The show is not submitted to any podcast directory. It is reachable only by anyone
who knows the feed URL, so keep the URL private-ish.

- Site: <https://dnikolsk.github.io/morning-paper-podcast/>
- Feed: <https://dnikolsk.github.io/morning-paper-podcast/feed.xml>

## Subscribe in Apple Podcasts

1. Open **Apple Podcasts**.
2. Go to **Library**.
3. Tap/click the **...** (more) button, or on Mac use **File** in the menu bar.
4. Choose **Follow a Show by URL...**
5. Paste this URL and confirm:

   ```
   https://dnikolsk.github.io/morning-paper-podcast/feed.xml
   ```

The show appears in your Library and new episodes download like any other podcast.
The feed also works in any other podcast app that accepts a raw RSS URL.

## Publishing an episode

Episodes are plain MP3 files in `episodes/`, named `YYYY-MM-DD.mp3`, and listed as
`<item>` entries in `feed.xml` (newest first).

Use the helper script from the repo root (Python 3, standard library only):

```bash
python3 scripts/publish_episode.py \
  --mp3 /path/to/recording.mp3 \
  --title "Morning Paper - 13 Sep 2026" \
  --date 2026-09-13 \
  --summary "Optional short description of the episode."
```

The script:

- copies the MP3 to `episodes/YYYY-MM-DD.mp3`
- inserts a new `<item>` at the top of `feed.xml` (or updates the existing item for
  that date) with the correct `enclosure` URL, length, GUID and `pubDate`
- refreshes the channel's `lastBuildDate`

Then commit and push:

```bash
git add episodes/ feed.xml
git commit -m "Publish episode 2026-09-13"
git push
```

GitHub Pages redeploys within a minute or two and podcast apps pick up the new
episode on their next refresh.

## Repository layout

```
feed.xml                   Podcast RSS 2.0 feed (iTunes namespace)
index.html                 Minimal landing page pointing at the feed
episodes/                  MP3 files, one per episode (YYYY-MM-DD.mp3)
scripts/publish_episode.py CLI to add an episode and update the feed
```

## Hosting

GitHub Pages serves the `main` branch from the repository root. No build step,
no secrets, no third-party hosting.
