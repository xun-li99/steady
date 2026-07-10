"""Steady — Zero-touch self-healing agent maintenance.
Agent crashes? Auto-restart. Context full? Auto-handoff-restart.
Human sees: reliability. Agent gets: continuity.
"""

from setuptools import setup, find_packages

setup(
    name="steady-agent",
    version="0.1.0",
    description="Zero-touch self-healing agent maintenance",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Steady",
    url="https://github.com/steady/steady",
    packages=find_packages(),
    py_modules=["agent_daemon", "diary", "connectome", "steady_cli"],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "steady=steady_cli:main",
        ],
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: System :: Monitoring",
    ],
)
