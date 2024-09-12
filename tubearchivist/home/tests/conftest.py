"""test configs"""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def change_test_dir(request):
    """change directory to project folder"""
    os.chdir(request.config.rootdir / "tubearchivist")
