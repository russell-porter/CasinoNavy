from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in casino_navy/__init__.py
from casino_navy import __version__ as version

setup(
	name="casino_navy",
	version=version,
	description="A custom App for Casino Navy",
	author="Lewin Villar",
	author_email="lewin.villar@tzcode.tech",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
