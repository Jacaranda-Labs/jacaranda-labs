"""Tests for the Mechanism Audit social rails.

Nothing here touches the network: the point is that a missing secret is a skip (not a crash) and
that the two pieces of hand-rolled crypto — the OAuth 1.0a signature and the bech32 nsec decode —
produce the shapes the platforms expect.
"""
import base64
import hashlib
import importlib
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import social  # noqa: E402


class ArmedTest(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)
        for k in list(os.environ):
            if k.startswith("MA_"):
                del os.environ[k]

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def test_nothing_set_is_nothing_armed(self):
        self.assertEqual(social.armed(), [])

    def test_each_rail_needs_its_whole_set(self):
        os.environ["MA_BSKY_ID"] = "x"
        self.assertNotIn("bsky", social.armed())          # password still missing
        os.environ["MA_BSKY_PASS"] = "y"
        self.assertIn("bsky", social.armed())

    def test_tumblr_needs_five_values(self):
        for k, v in (("MA_TUMBLR_CK", "a"), ("MA_TUMBLR_CS", "b"), ("MA_TUMBLR_TOKEN", "c")):
            os.environ[k] = v
        self.assertFalse(social.tumblr_armed())           # no token secret, no blog
        os.environ["MA_TUMBLR_TOKEN_SECRET"] = "d"
        os.environ["MA_TUMBLR_BLOG"] = "mechanism-audit.tumblr.com"
        self.assertTrue(social.tumblr_armed())

    def test_unarmed_rail_skips_instead_of_raising(self):
        ok, why = social.post_bsky("hello")
        self.assertFalse(ok)
        self.assertIn("skip", why)
        ok, why = social.post_tumblr("hello")
        self.assertFalse(ok)
        self.assertIn("skip", why)

    def test_dry_run_reports_without_calling_out(self):
        import postimage
        card = postimage.Img(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64, url="https://a.test/c.png")
        with mock.patch.object(social, "post_bsky", side_effect=AssertionError("must not post")), \
             mock.patch.object(social, "_image", return_value=card):
            res = social.post("hello", link="https://example.com", rails=["bsky"], dry=True)
        self.assertTrue(res["bsky"][0])

    def test_link_is_appended_once(self):
        seen = {}
        def fake(text, link="", tags=None, image=None):
            seen["text"] = text
            return True, "ok"
        import postimage
        card = postimage.Img(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64, url="https://a.test/c.png")
        with mock.patch.object(social, "post_bsky", fake), \
             mock.patch.object(social, "_image", return_value=card):
            social.post("body", link="https://a.test/x", rails=["bsky"])
            self.assertTrue(seen["text"].endswith("https://a.test/x"))
            social.post("body https://a.test/x", link="https://a.test/x", rails=["bsky"])
            self.assertEqual(seen["text"].count("https://a.test/x"), 1)

    def test_one_failing_rail_does_not_stop_the_others(self):
        def boom(text, **kw):
            raise RuntimeError("rail on fire")
        def fine(text, **kw):
            return True, "ok"
        import postimage
        card = postimage.Img(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64, url="https://a.test/c.png")
        with mock.patch.object(social, "post_nostr", boom), \
             mock.patch.object(social, "post_mastodon", fine), \
             mock.patch.object(social, "_image", return_value=card):
            res = social.post("body", rails=["nostr", "mastodon"])
        self.assertFalse(res["nostr"][0])
        self.assertTrue(res["mastodon"][0])


class CryptoTest(unittest.TestCase):
    def test_oauth1_signature_matches_the_reference_construction(self):
        """Recompute the same signature by hand and compare — a wrong signature is a silent 401."""
        sig_header = social._oauth1(
            "POST", "https://api.tumblr.com/v2/blog/x.tumblr.com/post",
            {"type": "text", "body": "hi"}, "ck", "cs", "tok", "tsec")
        self.assertTrue(sig_header.startswith("OAuth "))
        self.assertIn('oauth_signature_method="HMAC-SHA1"', sig_header)
        parts = dict(p.strip().split("=", 1) for p in sig_header[6:].split(","))
        nonce = parts["oauth_nonce"].strip('"')
        ts = parts["oauth_timestamp"].strip('"')
        params = {"type": "text", "body": "hi", "oauth_consumer_key": "ck",
                  "oauth_nonce": nonce, "oauth_signature_method": "HMAC-SHA1",
                  "oauth_timestamp": ts, "oauth_token": "tok", "oauth_version": "1.0"}
        enc = lambda s: __import__("urllib.parse", fromlist=["quote"]).quote(str(s), safe="~-._")
        qs = "&".join(f"{k}={v}" for k, v in sorted((enc(k), enc(v)) for k, v in params.items()))
        base = "&".join(["POST", enc("https://api.tumblr.com/v2/blog/x.tumblr.com/post"), enc(qs)])
        import hmac
        want = base64.b64encode(hmac.new(b"cs&tsec", base.encode(), hashlib.sha1).digest()).decode()
        self.assertEqual(parts["oauth_signature"].strip('"'),
                         __import__("urllib.parse", fromlist=["quote"]).quote(want, safe="~-._"))

    def test_nsec_bech32_decodes_to_32_bytes(self):
        sk = social._bech32_decode("nsec1zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zygs4rm7hz")
        self.assertEqual(len(sk), 32)

    def test_hex_nsec_is_accepted_too(self):
        os.environ["MA_NOSTR_NSEC"] = "11" * 32
        try:
            self.assertEqual(social._sk(), bytes.fromhex("11" * 32))
        finally:
            del os.environ["MA_NOSTR_NSEC"]

    def test_facets_point_at_the_link_bytes(self):
        text = "look at https://a.test/x now"
        f = social._facets(text, "https://a.test/x")
        self.assertEqual(len(f), 1)
        i = f[0]["index"]
        self.assertEqual(text.encode()[i["byteStart"]:i["byteEnd"]].decode(), "https://a.test/x")


class ExitCodeTest(unittest.TestCase):
    def test_verify_exits_non_zero_when_a_credential_is_dead(self):
        """The daily job is only useful if a dead credential fails the run."""
        with mock.patch.object(social, "verify", return_value={"bsky": "FAIL 401"}):
            with mock.patch.object(sys, "argv", ["social.py", "verify"]):
                self.assertEqual(social.main(), 1)

    def test_verify_exits_zero_when_everything_answers(self):
        with mock.patch.object(social, "verify", return_value={"bsky": "@x (did:plc:y)"}):
            with mock.patch.object(sys, "argv", ["social.py", "verify"]):
                self.assertEqual(social.main(), 0)


if __name__ == "__main__":
    unittest.main()


class BufferTest(unittest.TestCase):
    """The Buffer rail: one GraphQL call, a board that must be right, and an image a pin cannot live
    without. All mocked — nothing here spends a real pin."""

    def setUp(self):
        self._env = dict(os.environ)
        for k in list(os.environ):
            if k.startswith("MA_"):
                del os.environ[k]

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)
        social._ORG.clear()

    def test_not_armed_without_a_token(self):
        self.assertNotIn("pinterest", social.armed())
        ok, why = social.post_buffer("hi")
        self.assertFalse(ok)
        self.assertIn("skip", why)

    def test_armed_with_a_token(self):
        os.environ["MA_BUFFER_TOKEN"] = "t"
        self.assertIn("pinterest", social.armed())

    def test_pin_payload_names_the_board_and_carries_an_image(self):
        os.environ["MA_BUFFER_TOKEN"] = "t"
        os.environ["MA_PINTEREST_BOARD"] = "999"
        seen = {}
        def fake(query, variables=None):
            seen["query"] = query
            seen["vars"] = variables
            if "organizations" in query:
                return {"data": {"account": {"id": "a", "organizations": [{"id": "org1"}]}}}
            if "channels(input" in query:
                return {"data": {"channels": [{"id": "ch1", "service": "pinterest", "name": "mechanismaudit"}]}}
            return {"data": {"createPost": {"post": {"id": "p1", "status": "sent"}}}}
        with mock.patch.object(social, "_buffer", fake):
            ok, detail = social.post_buffer("body", link="https://a.test", image="https://a.test/i.png", title="T")
        self.assertTrue(ok, detail)
        inp = seen["vars"]["input"]
        self.assertEqual(inp["mode"], "shareNow")
        self.assertEqual(inp["channelId"], "ch1")
        self.assertEqual(inp["metadata"]["pinterest"]["boardServiceId"], "999")
        self.assertEqual(inp["assets"][0]["image"]["url"], "https://a.test/i.png")

    def test_board_is_discovered_when_not_configured(self):
        os.environ["MA_BUFFER_TOKEN"] = "t"
        calls = []
        def fake(query, variables=None):
            calls.append(query)
            if "organizations" in query:
                return {"data": {"account": {"id": "a", "organizations": [{"id": "org1"}]}}}
            if "channels(input" in query:
                return {"data": {"channels": [{"id": "ch1", "service": "pinterest", "name": "x"}]}}
            if "PinterestMetadata" in query:
                return {"data": {"channel": {"metadata": {"boards": [{"serviceId": "278801101871362052"}]}}}}
            return {"data": {"createPost": {"post": {"id": "p", "status": "sent"}}}}
        with mock.patch.object(social, "_buffer", fake):
            ok, _ = social.post_buffer("body", image="https://a.test/i.png")
        self.assertTrue(ok)
        self.assertTrue(any("boards" in c for c in calls))

    def test_no_pinterest_channel_is_a_clear_failure(self):
        os.environ["MA_BUFFER_TOKEN"] = "t"
        def fake(query, variables=None):
            if "organizations" in query:
                return {"data": {"account": {"organizations": [{"id": "org1"}]}}}
            return {"data": {"channels": []}}
        with mock.patch.object(social, "_buffer", fake):
            ok, why = social.post_buffer("body")
        self.assertFalse(ok)
        self.assertIn("no pinterest channel", why)

    def test_every_rail_refuses(self):
        """The rule from 2026-11-08: no image, no post."""
        import postimage
        with mock.patch.object(social, "_image", side_effect=postimage.NoImage("card 404")):
            res = social.post("body", rails=["bsky", "mastodon"])
        self.assertFalse(res["bsky"][0])
        self.assertIn("no image", res["bsky"][1])
