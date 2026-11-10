"""Prepare up to three Proton signups and stop at human verification."""

import re
import secrets
import time

SIGNUP_URL = "https://account.proton.me/mail/signup"
MAX_ATTEMPTS = 3

FIRST_NAMES = (
    "adam", "amina", "anna", "aya", "daniel", "elena", "emma", "ethan",
    "hugo", "ines", "james", "julia", "leo", "lina", "lucas", "maya",
    "mila", "nora", "oliver", "omar", "sami", "sara", "sofia", "yasmine",
)
LAST_NAMES = (
    "adams", "bennett", "brooks", "carter", "clark", "collins", "davis",
    "ellis", "evans", "foster", "green", "hayes", "hill", "james", "lane",
    "morgan", "parker", "reed", "rivera", "ross", "scott", "stone",
    "walker", "young",
)
PASSPHRASE_WORDS = tuple("""
acorn amber anchor apple apricot arrow aspen atlas autumn azure bamboo basket
beacon berry birch blossom breeze brook cabin cactus candle canyon cedar cherry
chestnut cinnamon cliff cloud clover coast cobalt coral cotton creek crystal dawn
desert diamond drift dune eagle earth echo elm ember emerald falcon feather
fern field finch flame flint flower forest fountain frost garden garnet glacier
glade gold granite grape grove harbor hazel hearth heron hill honey horizon
indigo iris island ivory jade jasmine juniper kiwi lagoon lake lantern laurel
lavender leaf lemon lilac lily lime linen lotus maple marble meadow melon
mint moon moss mountain nectar oak ocean olive opal orange orchid otter
owl palm paper peach pearl pebble pine plum pond poppy quartz rain
raven reed reef river robin rose ruby sage sand satin scarlet shell
shore silver sky slate snow sparrow spring spruce star stone storm summit
sunset swift thyme tiger timber topaz trail tulip valley velvet violet walnut
wave wheat willow wind winter wren zephyr zinnia
""".split())


def make_details():
    """Use readable names and independently generated random passphrases."""
    username = (
        f"{secrets.choice(FIRST_NAMES)}.{secrets.choice(LAST_NAMES)}"
        f"{secrets.randbelow(9000) + 1000}"
    )
    words = [secrets.choice(PASSPHRASE_WORDS).capitalize() for _ in range(6)]
    digits = "".join(str(secrets.randbelow(10)) for _ in range(8))
    password = "-".join(words) + "-" + digits + "!"
    return username, password


def find_field(page, selector, timeout=15):
    """Locate visible inputs in the page or a normally accessible child frame."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for frame in page.frames:
            matches = frame.locator(selector)
            for index in range(matches.count()):
                candidate = matches.nth(index)
                if candidate.is_visible():
                    return candidate
        page.wait_for_timeout(250)
    raise RuntimeError("Signup field unavailable. Complete the page manually.")


def fill_signup(page, username, password):
    # Selecting the plan is distinct from submitting the registration form.
    page.get_by_text("Free", exact=True).first.click(timeout=15000)
    find_field(page, 'input[id="username"], input[name="username"]').fill(username)
    find_field(page, 'input[id="password"], input[name="password"]').fill(password)
    # Some signup layouts expose a confirmation field on this screen.
    for frame in page.frames:
        confirmation = frame.locator(
            'input[id="repeat-password"], input[name="repeat-password"], '
            'input[id="password-confirm"], input[name="confirmPassword"]'
        )
        for index in range(confirmation.count()):
            field = confirmation.nth(index)
            if field.is_visible():
                field.fill(password)


def verification_status(page):
    """Report only visible verification UI; never interact with challenges."""
    for iframe in page.locator("iframe").all():
        if not iframe.is_visible():
            continue
        description = " ".join(
            iframe.get_attribute(attribute) or "" for attribute in ("src", "title")
        ).lower()
        for marker, label in (
            ("hcaptcha", "hCaptcha"),
            ("recaptcha", "Google reCAPTCHA"),
            ("funcaptcha", "Arkose/FunCaptcha"),
            ("arkoselabs", "Arkose/FunCaptcha"),
            ("challenges.cloudflare.com", "Cloudflare verification"),
        ):
            if marker in description:
                return label + " visible; stopped for manual verification."
        if "captcha" in description:
            return "CAPTCHA visible; provider not identified from the page."
    text = page.locator("body").inner_text(timeout=5000).lower()
    if any(marker in text for marker in (
        "captcha", "human verification", "verify you are human", "verify you're human",
        "vérification humaine", "confirmez que vous êtes humain",
    )):
        return "Human verification visible; CAPTCHA provider not identified."
    return None


def advance_to_verification(page, timeout=45):
    """Submit Free signup once and dismiss only explicit free-plan upsells."""
    submit = re.compile(
        r"^(?:Start using Proton Mail|Create account|Create your account|"
        r"Commencer à utiliser Proton Mail|Créer (?:un|votre) compte)$", re.I
    )
    page.get_by_role("button", name=submit).click(timeout=15000)
    deadline = time.monotonic() + timeout
    dismissed = 0
    while time.monotonic() < deadline:
        status = verification_status(page)
        if status:
            return status
        # Restrict dismissal to dialogs and explicitly free/decline choices.
        dialogs = page.get_by_role("dialog")
        for dialog in dialogs.all():
            if not dialog.is_visible() or dismissed >= 3:
                continue
            decline = dialog.get_by_role("button", name=re.compile(
                r"^(?:Continue with [Ff]ree|Stay on [Ff]ree|Keep [Ff]ree|"
                r"No,? thanks|Not now|Maybe later|Continuer avec Free|"
                r"Continuer gratuitement|Non,? merci|Plus tard)$", re.I
            ))
            if decline.count() == 1 and decline.is_visible():
                decline.click()
                dismissed += 1
        page.wait_for_timeout(500)
    return "Stopped: no identifiable verification appeared. Inspect the browser manually."


def run_sessions(browser):
    from playwright.sync_api import Error

    filled = 0
    for index in range(1, MAX_ATTEMPTS + 1):
        context = browser.new_context()
        try:
            page = context.new_page()
            print(f"Opening signup {index}/{MAX_ATTEMPTS}...")
            username, password = make_details()
            print(f"Proposed address (not yet registered): {username}@proton.me")
            print(f"Generated password: {password}")
            print("Save these details before continuing. They are not saved to a file.")
            try:
                page.goto(SIGNUP_URL, wait_until="domcontentloaded", timeout=60000)
                fill_signup(page, username, password)
            except (Error, RuntimeError):
                print("Could not finish autofill. You can complete the open page manually.")
                input("Press Enter after finishing manually to close the browser session: ")
                break
            filled += 1
            try:
                print(advance_to_verification(page))
            except (Error, RuntimeError):
                print("Could not advance automatically. Inspect the browser manually.")
            print("Complete any verification yourself in the browser.")
            print("Availability and account creation have not been checked.")
            action = input(
                "When finished, Enter closes this session and continues; q closes and stops: "
            ).strip().lower()
            while action not in ("", "q"):
                action = input("Enter to continue, or q to stop: ").strip().lower()
            if action == "q":
                break
        finally:
            context.close()
    print(f"Filled {filled} form(s). Account creation was not verified.")


def run():
    try:
        from playwright.sync_api import Error, sync_playwright
    except ImportError:
        print("Install the Proton dependency: python -m pip install -r requirements-proton.txt")
        return
    try:
        with sync_playwright() as playwright:
            # Use the installed, visible Edge browser without stealth modifications.
            browser = playwright.chromium.launch(channel="msedge", headless=False)
            try:
                run_sessions(browser)
            finally:
                browser.close()
    except (KeyboardInterrupt, EOFError):
        print("\nStopped.")
    except (Error, RuntimeError) as error:
        print(f"Signup helper stopped: {error}")


if __name__ == "__main__":
    run()
