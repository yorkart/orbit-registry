import hashlib
import io
import tarfile
import unittest
import zipfile
from unittest.mock import patch
from urllib.error import HTTPError

from check_archives import OPENER, check_archive


def tar_bytes():
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode="w:gz") as entries:
        entry = tarfile.TarInfo("./bin/traecli")
        entry.size = 3
        entries.addfile(entry, io.BytesIO(b"ACP"))
    return archive.getvalue()


def zip_bytes():
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, mode="w") as entries:
        entries.writestr("bin/traecli", b"ACP")
    return archive.getvalue()


class ArchiveChecks(unittest.TestCase):
    def setUp(self):
        dns = patch(
            "check_archives.socket.getaddrinfo",
            return_value=[(None, None, None, "", ("8.8.8.8", 443))],
        )
        dns.start()
        self.addCleanup(dns.stop)

    def test_verifies_tar_and_zip_with_the_expected_digest(self):
        for filename, data in (
            ("adapter.tar.gz", tar_bytes()),
            ("adapter.zip", zip_bytes()),
        ):
            with (
                self.subTest(filename=filename),
                patch.object(OPENER, "open", return_value=io.BytesIO(data)),
            ):
                check_archive(
                    {
                        "archive": f"https://example.com/{filename}",
                        "cmd": "./bin/traecli",
                        "sha256": hashlib.sha256(data).hexdigest(),
                    }
                )

    def test_rejects_missing_download(self):
        url = "https://example.com/adapter.tar.gz"
        with patch.object(
            OPENER, "open", side_effect=HTTPError(url, 404, "Not Found", None, None)
        ):
            with self.assertRaisesRegex(HTTPError, "404"):
                check_archive({"archive": url, "cmd": "./bin/traecli"})

    def test_rejects_wrong_digest_or_missing_executable(self):
        target = {
            "archive": "https://example.com/adapter.tar.gz",
            "cmd": "./bin/traecli",
        }
        with patch.object(OPENER, "open", return_value=io.BytesIO(tar_bytes())):
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                check_archive({**target, "sha256": "0" * 64})
        with patch.object(OPENER, "open", return_value=io.BytesIO(tar_bytes())):
            with self.assertRaisesRegex(ValueError, "does not contain executable"):
                check_archive({**target, "cmd": "./bin/missing"})

    def test_stops_at_the_archive_size_limit(self):
        target = {
            "archive": "https://example.com/adapter.tar.gz",
            "cmd": "./bin/traecli",
        }
        with patch("check_archives.MAX_BYTES", 2):
            with patch.object(OPENER, "open", return_value=io.BytesIO(tar_bytes())):
                with self.assertRaisesRegex(ValueError, "archive exceeds"):
                    check_archive(target)

    def test_rejects_download_targets_on_private_networks(self):
        with (
            patch(
                "check_archives.socket.getaddrinfo",
                return_value=[(None, None, None, "", ("127.0.0.1", 443))],
            ),
            patch.object(OPENER, "open") as download,
        ):
            with self.assertRaisesRegex(ValueError, "public addresses"):
                check_archive(
                    {
                        "archive": "https://example.com/adapter.tar.gz",
                        "cmd": "./bin/traecli",
                    }
                )
        download.assert_not_called()
