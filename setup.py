from setuptools import setup, find_packages
setup(
name="github-repo-analyzer",
version="0.1.0",
packages=find_packages(),
install_requires=[
"requests>=2.26.0",
],
author="jeblister",
author_email="jeblister@waveup.dev",
description="A tool for analyzing GitHub repositories",
long_description=open("README.md").read(),
long_description_content_type="text/markdown",
url="https://github.com/waveuphq/github-repo-analyzer",
classifiers=[
"Programming Language :: Python :: 3",
"License :: OSI Approved :: MIT License",
"Operating System :: OS Independent",
],
python_requires='>=3.6',
)
