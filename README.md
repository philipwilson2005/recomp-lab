# Recomp Lab

Your fitness dashboard, refreshed from Garmin every morning with no uploads.

A GitHub Action runs daily at 7:30am Central. It pulls the last 7 days from Garmin Connect (scale readings, steps, calories burned, resting heart rate, sleep, HRV, food log, workouts), rebuilds the dashboard, password-protects it, and publishes it to a private-feeling link you can pin to your phone's home screen.

**Privacy.** Everything saved in the repo (`data/history.enc`, `data/tokens.enc`) is encrypted with a key only you have. The published page is encrypted with your password. Your Garmin password is never saved anywhere; it's used once on your own computer to create a login token. The repo can therefore be public (free), and nobody browsing it can read your data.

---

## Setup (about 20 minutes, once)

### 1. Install two things
- **Python 3.12**: python.org/downloads. On the first installer screen, tick **Add python.exe to PATH**.
- **GitHub Desktop**: desktop.github.com. Sign in (or create a free GitHub account).

### 2. Run the one-time setup on your computer
1. Unzip this folder somewhere, e.g. `Documents\recomp-lab`.
2. Open the folder in File Explorer, click the address bar, type `cmd`, press Enter.
3. Run:
   ```
   py -m pip install -r requirements.txt
   py setup_local.py
   ```
4. Enter your Garmin email, password, and the MFA code if Garmin asks for one.
5. It prints a **DATA_KEY**. Copy it somewhere safe (a password manager). It's also saved in `.env.local`.
6. Open `site\index.html` in your browser to check the dashboard looks right.

### 3. Put it on GitHub
1. In GitHub Desktop: **File → Add local repository** → pick the `recomp-lab` folder → **create a repository** if asked.
2. Click **Publish repository**. Untick **Keep this code private** (everything is encrypted; GitHub Pages on private repos needs a paid plan).
3. Check the file list before publishing: `seed_history.json` and `.env.local` must **not** be there. (`.gitignore` already excludes them.)

### 4. Add two secrets
On github.com, open the repo → **Settings → Secrets and variables → Actions → New repository secret**:
| Name | Value |
|---|---|
| `DATA_KEY` | the key from step 2 |
| `PAGE_PASSWORD` | a password you'll type to open the dashboard |

### 5. Turn on the page
**Settings → Pages → Build and deployment → Source: GitHub Actions.**

### 6. First run
**Actions → Refresh dashboard → Run workflow** (set days to `30` the first time to fill the gap since your last export). It takes about 2 minutes. Your link is shown in **Settings → Pages**, like `https://YOUR-NAME.github.io/recomp-lab/`.

On your phone: open the link, enter the password, tick **Remember me**, then **Share → Add to Home Screen**.

---

## Day to day
Nothing. Weigh in, wear the watch, log food in MyFitnessPal (synced to Garmin), and the page updates every morning.

Two habits make it much better:
- **Start gym sessions on the watch as Strength, not Cardio**, and log sets. The Strength section then tracks each lift's estimated one-rep max.
- **Name at-home lifting sessions** with "lift", "push" or "pull" if you record them as another type, so they count toward the 2-a-week target.

## If something breaks
- **GitHub emails you that the run failed.** Garmin's API is unofficial and occasionally changes its login. Update the library in `requirements.txt` to the latest `garminconnect` version, or re-run `py setup_local.py` to create a fresh login token, then commit `data/tokens.enc` in GitHub Desktop.
- **Food intake doesn't show up.** Garmin doesn't document its nutrition feed. The run log prints only the field names it received (never values); send that line to Claude to adjust `recomp/fetch.py`.
- **Want to go further back:** Actions → Run workflow → days `90`.

## Files
| Path | What it does |
|---|---|
| `run.py` | Daily job: fetch → save encrypted → build page |
| `recomp/fetch.py` | Garmin calls (python-garminconnect) |
| `recomp/build.py` | Turns history into the page's data |
| `recomp/store.py` | Encryption for everything saved in the repo |
| `template/index.html` | The dashboard |
| `setup_local.py` | One-time login + key creation |
| `.github/workflows/refresh.yml` | The daily schedule |

## Credits
Built on [python-garminconnect](https://github.com/cyberjunky/python-garminconnect) (MIT) and [StatiCrypt](https://github.com/robinmoisson/staticrypt) (MIT). Ideas from [garmin-grafana](https://github.com/arpanghosh8453/garmin-grafana) (sleep regularity, strength tracking), [running_page](https://github.com/yihong0618/running_page) (scheduled GitHub Action + Pages), and [openScale](https://github.com/oliexdev/openScale) (tape-measure body fat).
