#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2021 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""The setup script"""

import pathlib

from setuptools import find_packages, setup

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="haul",
    version="0.1.0",
    description="An command line tool for rapid contract and service development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fetchai/cli",
    author="Fetch.AI Limited",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords="cosmos, gaia, fetchhub, fetchai",
    package_dir={"haul": "haul"},
    packages=find_packages(include=["haul*"]),
    python_requires=">=3.6, <4",
    install_requires=[
        "ecdsa",
        "bech32",
        "requests",
        "google-api-python-client",
        "protobuf",
        "python-mbedtls==2.2.0",
        "grpcio",
        "click",
        "types-certifi",
        "bip-utils",
        "blspy",
    ],
    extras_require={
        "dev": [
            "docker==5.0.0",
            "check-manifest",
            "tox==3.24.1",
            "flake8==3.9.2",
            "black==22.3",
            "mypy==0.910",
            "mkdocs==1.3",
            "mkdocs-material==8.2.11",
            "bandit==1.7.0",
            "safety==1.10.3",
            "isort==5.9.3",
            "darglint==1.8.0",
            "vulture==2.3",
            "pylint==2.9.6",
            "liccheck==0.6.2",
            "flake8-copyright==0.2.2",
            # Using Tensorflow v2.4.0 was causing conflicts because it requires grpcio==1.32.0
            "grpcio-tools<=1.32.0",
        ],
        "test": ["coverage", "pytest"],
    },
    project_urls={
        "Bug Reports": "https://github.com/fetchai/cli/issues",
        "Source": "https://github.com/fetchai/cli",
    },
)
