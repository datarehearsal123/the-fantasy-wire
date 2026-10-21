# The Fantasy Wire — Version 1

A public, static fantasy hockey newsroom for the 14-team Hit the Road Hockey league.

## What's working
- Responsive homepage, league standings, browsable fantasy rosters, sample editorial commentary.
- Player names matched from the user's Fantrax All Players CSV, not a manually fabricated database.
- A GitHub Actions workflow attempts a nightly standings update. If the Fantrax response is missing, malformed, or has unexpected team IDs, the script exits without overwriting the last good snapshot.

## What's NOT automated yet
- Daily fantasy player points, weekly matchup scores, final result verification, trades, power rankings and AI-written nightly articles.
- Roster updates: the included roster data is from a one-time CSV export. Do not represent it as current after transactions.
- The sample editorial items are tied to the initial standings snapshot and should be replaced by verified generated articles before enabling automatic story publishing.

## Launch (GitHub Pages)
1. Create a **public** GitHub repository, e.g. `the-fantasy-wire`.
2. Upload all files from this package, including `.github/workflows/nightly.yml` (uploading a zip alone will NOT deploy the site).
3. In GitHub repo **Settings → Pages**, select **Deploy from a branch**, branch `main`, folder `/ (root)`, then Save.
4. After GitHub deploys, visit `https://YOUR-USERNAME.github.io/the-fantasy-wire/`.
5. In **Actions**, manually run **Nightly Fantrax standings refresh** once to test. If it fails, inspect the workflow logs. A failed run leaves existing standings intact.
6. In **Settings → Actions → General**, ensure workflow permissions allow **Read and write permissions** for the commit step (repository or organization policies may override).

## Nightly schedule and time zones
The workflow uses 10:00 UTC daily. That is 2 a.m. during Pacific Standard Time and 3 a.m. during Pacific Daylight Time. GitHub scheduled jobs may run late or be skipped. For a reliable exact local-time job, move the schedule to a managed scheduler with time-zone support.

## Production automation roadmap
1. Verify Fantrax's matchup and player daily-score endpoints and access rules using test responses.
2. Persist daily snapshots and compare successive results, recording a unique league/week/date key.
3. Detect whether daily scoring is final, handle corrections and late games, and retry incomplete pulls.
4. Generate stories only from verified structured facts, with optional AI API integration stored in GitHub Secrets (never in frontend JS or committed files).
5. Run validation, duplicate checks, and publish only if all checks pass. Send a failure alert instead of publishing guessed results.
6. Refresh player name mapping and team rosters automatically; remove dependence on manual CSV exports.

## Privacy and licensing
The public site publishes team names and player data from the league export. Make sure league members are comfortable with public display of their fantasy team names. No passwords or API keys are needed for this initial version.
