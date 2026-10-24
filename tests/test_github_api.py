import pytest

from github_api import parse_repo_url


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://github.com/AliMoR10/MLH-Hackathon", ("AliMoR10", "MLH-Hackathon")),
        ("https://github.com/AliMoR10/MLH-Hackathon.git", ("AliMoR10", "MLH-Hackathon")),
        ("github.com/owner/repo/tree/main/src", ("owner", "repo")),
        ("  https://github.com/owner/repo?tab=readme  ", ("owner", "repo")),
    ],
)
def test_parse_repo_url(url, expected):
    assert parse_repo_url(url) == expected


@pytest.mark.parametrize("url", ["", "hello", "https://gitlab.com/owner/repo"])
def test_parse_repo_url_rejects_bad_links(url):
    with pytest.raises(ValueError):
        parse_repo_url(url)
