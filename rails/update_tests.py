#!/usr/bin/env python3
"""update_tests.py — bring an existing test_social.py up to the image-branch contract.

Two orchestration tests stub rails with `def fake(text)` and ran without an image. Both are fine to
keep testing, but they must now say what every caller says: the rail receives an `image=` kwarg, and
post() needs a resolved card. This edits them in place, idempotently.
"""
import pathlib
import sys

FAKE_OLD = '        def fake(text, link="", tags=None):'
FAKE_NEW = '        def fake(text, link="", tags=None, image=None):'
BOOM_OLD = '''        def boom(text):
            raise RuntimeError("rail on fire")
        def fine(text):
            return True, "ok"'''
BOOM_NEW = '''        def boom(text, **kw):
            raise RuntimeError("rail on fire")
        def fine(text, **kw):
            return True, "ok"'''
CARD = '''        import postimage
        card = postimage.Img(b"\\x89PNG\\r\\n\\x1a\\n" + b"\\x00" * 64, url="https://a.test/c.png")
'''
RESOLVE = '''             mock.patch.object(social, "_image", return_value=card):'''
NEW_TEST = '''
    def test_every_rail_refuses(self):
        """The rule from 2026-11-08: no image, no post."""
        import postimage
        with mock.patch.object(social, "_image", side_effect=postimage.NoImage("card 404")):
            res = social.post("body", rails=["bsky", "mastodon"])
        self.assertFalse(res["bsky"][0])
        self.assertIn("no image", res["bsky"][1])
'''


def patch(path: pathlib.Path) -> bool:
    s = path.read_text(encoding="utf-8")
    before = s
    s = s.replace(FAKE_OLD, FAKE_NEW)
    s = s.replace(BOOM_OLD, BOOM_NEW)
    s = s.replace('''        with mock.patch.object(social, "post_bsky", fake):
            social.post("body", link="https://a.test/x", rails=["bsky"])''',
                  CARD + '''        with mock.patch.object(social, "post_bsky", fake), \\
''' + RESOLVE + '''
            social.post("body", link="https://a.test/x", rails=["bsky"])''')
    s = s.replace('''        with mock.patch.object(social, "post_nostr", boom), \\
             mock.patch.object(social, "post_mastodon", fine):
            res = social.post("body", rails=["nostr", "mastodon"])''',
                  CARD + '''        with mock.patch.object(social, "post_nostr", boom), \\
             mock.patch.object(social, "post_mastodon", fine), \\
''' + RESOLVE + '''
            res = social.post("body", rails=["nostr", "mastodon"])''')
    s = s.replace(
        '        with mock.patch.object(social, "post_bsky", side_effect=AssertionError("must not post")):\n'
        '            res = social.post("hello", link="https://example.com", rails=["bsky"], dry=True)',
        '        import postimage\n'
        '        card = postimage.Img(b"\\x89PNG\\r\\n\\x1a\\n" + b"\\x00" * 64, url="https://a.test/c.png")\n'
        '        with mock.patch.object(social, "post_bsky", side_effect=AssertionError("must not post")), \\\n'
        '             mock.patch.object(social, "_image", return_value=card):\n'
        '            res = social.post("hello", link="https://example.com", rails=["bsky"], dry=True)')
    if "test_every_rail_refuses" not in s:
        s = s.rstrip() + "\n" + NEW_TEST
    if s != before:
        path.write_text(s, encoding="utf-8")
        return True
    return False


if __name__ == "__main__":
    changed = [str(p) for p in map(pathlib.Path, sys.argv[1:] or ["tests/test_social.py"]) if patch(p)]
    print("updated:", ", ".join(changed) or "nothing (already current)")
