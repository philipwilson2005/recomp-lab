"""One-time setup. Run on your own computer:  py setup_local.py

1. Logs into Garmin (asks for your MFA code if you use one).
2. Creates DATA_KEY, the key that encrypts everything stored in the repo.
3. Writes data/tokens.enc (your Garmin session, encrypted) and data/history.enc
   (your history so far, seeded from seed_history.json, encrypted).
4. Builds site/index.html so you can open it and check it before pushing.

Your password is only sent to Garmin; it is never saved.
"""
import getpass, json, os
from cryptography.fernet import Fernet
from garminconnect import Garmin

os.makedirs("data", exist_ok=True)
key = None
if os.path.exists(".env.local"):
    key = open(".env.local").read().strip().split("=", 1)[1]
if not key:
    key = Fernet.generate_key().decode()
    open(".env.local", "w").write(f"DATA_KEY={key}\n")
os.environ["DATA_KEY"] = key

from recomp import store, build  # noqa: E402

if not os.path.exists(".staticrypt.json"):  # fixed salt so "remember me" survives daily rebuilds
    json.dump({"salt": os.urandom(16).hex()}, open(".staticrypt.json", "w"))

email = input("Garmin email: ").strip()
password = getpass.getpass("Garmin password (not saved): ")
g = Garmin(email, password, prompt_mfa=lambda: input("Garmin MFA code: ").strip())
g.login()
store.save_text("data/tokens.enc", g.client.dumps())
print("Garmin login OK - tokens saved (encrypted).")

if not os.path.exists("data/history.enc"):
    seed = json.load(open("seed_history.json")) if os.path.exists("seed_history.json") else {"days": {}, "workouts": {}}
    store.save_json("data/history.enc", seed)
    print(f"History seeded with {len(seed['days'])} days.")

hist = store.load_json("data/history.enc", {"days": {}, "workouts": {}})
os.makedirs("site", exist_ok=True)
build.build(hist, "template/index.html", "site/index.html")
print("\nOpen site/index.html to check the dashboard.")
print("\n=== Add these two GitHub secrets (Settings > Secrets and variables > Actions) ===")
print(f"DATA_KEY       = {key}")
print("PAGE_PASSWORD  = (make up a password you'll type to open the dashboard)")
print("\nKeep DATA_KEY somewhere safe (it's also in .env.local). Without it the saved history can't be decrypted.")
