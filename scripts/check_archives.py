"""Verify that binary distributions can be fetched and contain the declared executable."""

import hashlib
import ipaddress
import socket
import stat
import tarfile
import tempfile
import zipfile
from pathlib import PurePosixPath
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

# Keep this in sync with the Host binary installer.
MAX_BYTES = 1024 * 1024 * 1024


def check_public_url(url):
    address = urlsplit(url)
    if (
        address.scheme != "https"
        or not address.hostname
        or address.username is not None
    ):
        raise ValueError("archive URL must be public HTTPS")
    hosts = socket.getaddrinfo(
        address.hostname, address.port or 443, type=socket.SOCK_STREAM
    )
    for *_, host in hosts:
        ip = ipaddress.ip_address(host[0])
        if not ip.is_global or ip.is_multicast:
            raise ValueError("archive URL must resolve to public addresses")


class PublicRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, url):
        check_public_url(url)
        return super().redirect_request(request, fp, code, message, headers, url)


OPENER = build_opener(PublicRedirects)


def archive_contains(archive, is_zip, command):
    if is_zip:
        with zipfile.ZipFile(archive) as entries:
            return any(
                not entry.is_dir()
                and not stat.S_ISLNK(entry.external_attr >> 16)
                and PurePosixPath(entry.filename) == command
                for entry in entries.infolist()
            )
    with tarfile.open(fileobj=archive, mode="r|gz") as entries:
        return any(
            entry.isfile() and PurePosixPath(entry.name) == command for entry in entries
        )


def check_archive(target):
    url = target["archive"]
    check_public_url(url)
    command = PurePosixPath(target["cmd"])
    if (
        not command.parts
        or command.is_absolute()
        or ".." in command.parts
        or ":" in command.parts[0]
        or "\\" in target["cmd"]
        or "\0" in target["cmd"]
    ):
        raise ValueError("archive executable must be a relative file path")

    request = Request(url, headers={"User-Agent": "Orbit-ACP-Registry/1.0"})
    with (
        OPENER.open(request, timeout=30) as response,
        tempfile.TemporaryFile() as archive,
    ):
        digest = hashlib.sha256()
        size = 0
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_BYTES:
                raise ValueError("archive exceeds Orbit's 1 GiB limit")
            archive.write(chunk)
            digest.update(chunk)

        expected = target.get("sha256")
        if expected and digest.hexdigest() != expected.lower():
            raise ValueError("archive SHA-256 does not match the manifest")

        archive.seek(0)
        if not archive_contains(
            archive, url.split("?", 1)[0].endswith(".zip"), command
        ):
            raise ValueError(f"archive does not contain executable {target['cmd']}")
        return size
