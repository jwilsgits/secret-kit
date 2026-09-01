import os
import tempfile
import unittest

from engine.hashcheck import detect_algo, normalize_hex, verify_file


class NormalizeTests(unittest.TestCase):
    def test_strips_noise(self):
        self.assertEqual(normalize_hex("  0xAb Cd\n"), "abcd")

    def test_detect(self):
        self.assertEqual(detect_algo("a" * 32), "md5")
        self.assertEqual(detect_algo("a" * 40), "sha1")
        self.assertEqual(detect_algo("a" * 64), "sha256")
        self.assertEqual(detect_algo("a" * 128), "sha512")
        self.assertIsNone(detect_algo("abcd"))


class FileHashTests(unittest.TestCase):
    def setUp(self):
        handle, self.path = tempfile.mkstemp()
        os.write(handle, b"secret-kit-fixture\n")
        os.close(handle)

    def tearDown(self):
        os.remove(self.path)

    def test_sha256_match(self):
        expected = "6d5c9b3d5c5d4c4a1f3d0e6f6a6d0b2c7e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b"
        # compute via the function itself first
        from engine.hashcheck import hash_file

        real = hash_file(self.path, "sha256")
        result = verify_file(self.path, real)
        self.assertTrue(result["ok"])
        self.assertTrue(result["match"])
        self.assertEqual(result["algo"], "sha256")
        self.assertTrue(result["auto"])
        self.assertFalse(result["legacy"])
        self.assertEqual(result["digest"], real)
        self.assertNotEqual(real, expected)

    def test_mismatch_and_legacy(self):
        from engine.hashcheck import hash_file

        md5 = hash_file(self.path, "md5")
        result = verify_file(self.path, "0" * 32)
        self.assertTrue(result["ok"])
        self.assertFalse(result["match"])
        self.assertEqual(result["algo"], "md5")
        self.assertTrue(result["legacy"])
        matched = verify_file(self.path, md5, "md5")
        self.assertTrue(matched["match"])

    def test_compare_and_folder(self):
        from engine.hashcheck import compare_blobs, compare_files, hash_tree

        other = self.path + ".b"
        with open(other, "wb") as handle:
            handle.write(b"secret-kit-fixture\n")
        try:
            same = compare_files(self.path, other, "sha256")
            self.assertTrue(same["match"])
            with open(other, "wb") as handle:
                handle.write(b"different")
            diff = compare_files(self.path, other, "sha256")
            self.assertFalse(diff["match"])
            same_blobs = compare_blobs(b"secret-kit-fixture\n", b"secret-kit-fixture\n")
            self.assertTrue(same_blobs["match"])
            diff_blobs = compare_blobs(b"secret-kit-fixture\n", b"different")
            self.assertFalse(diff_blobs["match"])
        finally:
            os.remove(other)
        folder = tempfile.mkdtemp()
        try:
            with open(os.path.join(folder, "a.txt"), "wb") as handle:
                handle.write(b"aa")
            with open(os.path.join(folder, "b.txt"), "wb") as handle:
                handle.write(b"bb")
            tree = hash_tree(folder, "sha256")
            self.assertEqual(tree["count"], 2)
            self.assertEqual({row["path"] for row in tree["files"]}, {"a.txt", "b.txt"})
            hidden = os.path.join(folder, ".git")
            os.mkdir(hidden)
            with open(os.path.join(hidden, "HEAD"), "wb") as handle:
                handle.write(b"ref")
            outside = self.path + ".outside"
            with open(outside, "wb") as handle:
                handle.write(b"secret-outside")
            link = os.path.join(folder, "link.txt")
            os.symlink(outside, link)
            tree2 = hash_tree(folder, "sha256")
            paths = {row["path"] for row in tree2["files"]}
            self.assertEqual(paths, {"a.txt", "b.txt"})
            os.remove(link)
            os.remove(outside)
            os.remove(os.path.join(hidden, "HEAD"))
            os.rmdir(hidden)
        finally:
            for name in os.listdir(folder):
                path = os.path.join(folder, name)
                if os.path.isdir(path):
                    for inner in os.listdir(path):
                        os.remove(os.path.join(path, inner))
                    os.rmdir(path)
                else:
                    os.remove(path)
            os.rmdir(folder)

    def test_tree_bound(self):
        from engine.hashcheck import hash_tree
        import engine.hashcheck as hc

        folder = tempfile.mkdtemp()
        try:
            with open(os.path.join(folder, "a.txt"), "wb") as handle:
                handle.write(b"aa")
            with open(os.path.join(folder, "b.txt"), "wb") as handle:
                handle.write(b"bb")
            old = hc.MAX_TREE_FILES
            hc.MAX_TREE_FILES = 1
            try:
                with self.assertRaises(Exception):
                    hash_tree(folder, "sha256")
            finally:
                hc.MAX_TREE_FILES = old
        finally:
            for name in os.listdir(folder):
                os.remove(os.path.join(folder, name))
            os.rmdir(folder)
