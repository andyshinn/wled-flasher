import os
from tempfile import NamedTemporaryFile

from github import Github, GitReleaseAsset

from wledflasher.common import open_downloadable_binary

github = Github(os.getenv("GITHUB_TOKEN", None))


def get_releases():
    repo = github.get_repo("Aircoookie/WLED")
    return repo.get_releases()


def download_firmware(asset: GitReleaseAsset):
    data = open_downloadable_binary(asset.browser_download_url)

    file = NamedTemporaryFile(mode="wb", delete=False)
    file.write(data.read())

    return file
