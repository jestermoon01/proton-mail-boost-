"""Regression checks without opening browsers or registering accounts."""

import contextlib
import io
import unittest
from unittest.mock import MagicMock, patch

from playwright.sync_api import TimeoutError

import proton_signup as signup


class SignupTests(unittest.TestCase):
    def exercise(self, answers, failure=None):
        browser = MagicMock()
        output = io.StringIO()
        with (
            patch.object(signup, "fill_signup", side_effect=failure),
            patch.object(signup, "advance_to_verification", return_value="Manual verification"),
            patch("builtins.input", side_effect=answers),
            contextlib.redirect_stdout(output),
        ):
            signup.run_sessions(browser)
        return browser, output.getvalue()

    def test_three_attempt_limit(self):
        browser, output = self.exercise(["", "", ""])
        self.assertEqual(browser.new_context.call_count, 3)
        self.assertEqual(browser.new_context.return_value.close.call_count, 3)
        self.assertIn("Filled 3 form(s)", output)

    def test_quit_stops_after_first(self):
        browser, _ = self.exercise(["q"])
        self.assertEqual(browser.new_context.call_count, 1)

    def test_timeout_keeps_credentials_available_and_stops_retries(self):
        browser, output = self.exercise([""], TimeoutError("Page timeout"))
        self.assertEqual(browser.new_context.call_count, 1)
        self.assertIn("Generated password:", output)
        self.assertIn("complete the open page manually", output)
        self.assertIn("Filled 0 form(s)", output)
        browser.new_context.return_value.close.assert_called_once()

    def test_missing_field_stops_retries(self):
        browser, output = self.exercise([""], RuntimeError("Missing field"))
        self.assertEqual(browser.new_context.call_count, 1)
        self.assertIn("Filled 0 form(s)", output)

    def test_cancel_closes_context(self):
        browser = MagicMock()
        with (
            patch.object(signup, "fill_signup"),
            patch.object(signup, "advance_to_verification", return_value="Manual verification"),
            patch("builtins.input", side_effect=EOFError),
            contextlib.redirect_stdout(io.StringIO()),
            self.assertRaises(EOFError),
        ):
            signup.run_sessions(browser)
        browser.new_context.return_value.close.assert_called_once()

    def test_only_plan_is_clicked_without_submitting(self):
        page = MagicMock()
        page.frames = []
        username, password = MagicMock(), MagicMock()
        with patch.object(signup, "find_field", side_effect=[username, password]):
            signup.fill_signup(page, "exampleuser", "examplepassword")
        page.get_by_text.assert_called_once_with("Free", exact=True)
        username.fill.assert_called_once_with("exampleuser")
        password.fill.assert_called_once_with("examplepassword")
        clicks = [call for call in page.mock_calls if call[0].endswith(".click")]
        self.assertEqual(len(clicks), 1)

    def test_identifies_visible_hcaptcha(self):
        page, iframe = MagicMock(), MagicMock()
        page.locator.return_value.all.return_value = [iframe]
        iframe.is_visible.return_value = True
        iframe.get_attribute.side_effect = ["https://newassets.hcaptcha.com/captcha/", ""]
        self.assertIn("hCaptcha", signup.verification_status(page))
        iframe.click.assert_not_called()

    def test_does_not_guess_provider_from_generic_verification_text(self):
        page = MagicMock()
        page.locator.return_value.all.return_value = []
        page.locator.return_value.inner_text.return_value = "Human verification"
        self.assertIn("not identified", signup.verification_status(page))

    def test_stops_after_submit_when_verification_appears(self):
        page = MagicMock()
        with patch.object(signup, "verification_status", return_value="hCaptcha visible"):
            self.assertEqual(signup.advance_to_verification(page), "hCaptcha visible")
        page.get_by_role.return_value.click.assert_called_once()
        self.assertEqual(page.get_by_role.call_count, 1)


if __name__ == "__main__":
    unittest.main()
