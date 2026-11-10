# Protoboost

Prepare up to three supervised Proton Mail signup forms per run. The helper opens a visible Microsoft Edge browser immediately, selects Free, generates a proposed username and password, and fills the form. It clicks the signup button once, dismisses recognized free-plan upsell dialogs, and pauses when verification appears. You complete all verification yourself.

## Setup and run (Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-proton.txt
.\.venv\Scripts\python.exe protoboost.py
```

After setup you can also run `.\run-protoboost.ps1` from PowerShell. The launcher uses the project virtual environment even when your terminal has a different Python selected.

Microsoft Edge must be installed. Only `requirements-proton.txt` is needed. This repository contains the Proton helper only; account records, screenshots, browser state, and legacy Gmail files are excluded.

Generated details are displayed in the terminal and are not saved to a file. Save them in your password manager before closing a session. Proposed usernames may be unavailable; edit the form manually if needed. Filling a form does not establish that an account exists.

Usernames use a first name, surname, and four random digits (for example, `lina.morgan5287`). Passwords use six independently selected words, eight random digits, and a symbol. They are generated separately from the username using Python's `secrets` module.

The helper reports the visible CAPTCHA provider when identifiable, otherwise it reports that the provider is unknown. It stops at verification without interacting with challenges. Unknown dialogs and validation errors are left for manual review.

Finish registration in the browser before pressing Enter in the terminal: Enter closes that browser session and opens the next, up to three attempts. Type `q` to close and stop. If the page layout changes or verification prevents filling the form, the helper stops rather than retrying signup automatically.

`proton_mail.py` also launches the same helper.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests mock browser actions and never register accounts. Live provider pages may change; CAPTCHA detection reports only what is identifiable from visible page elements.

No proxy rotation, fingerprint modifications, CAPTCHA solving, or verification bypass is included. Signup submission is automatic; verification remains manual.
