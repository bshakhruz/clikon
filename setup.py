from setuptools import setup, find_packages

setup(
    name="clicon",
    version="0.1",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "clicon=clicon.app:main",  # runs main() in app.py
        ],
    },
)