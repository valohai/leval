import re

import setuptools

with open("./leval/__init__.py", "r") as infp:
    version = re.search("__version__ = ['\"]([^'\"]+)['\"]", infp.read()).group(1)

dev_dependencies = [
    "black==20.8b1;python_version>='3.6'",
    "flake8-black==0.2.1;python_version>='3.6'",
    "flake8-bugbear==20.11.1;python_version>='3.6'",
    "flake8-docstrings==1.5.0;python_version>='3.6'",
    "flake8==3.8.4;python_version>='3.6'",
    "isort==5.6.4;python_version>='3.6'",
    "mypy>=0.812;python_version>='3.6'",
    "pytest-cov==2.10.1",
    "pytest==6.1.2",
]

if __name__ == "__main__":
    setuptools.setup(
        name="leval",
        description="Limited evaluator",
        version=version,
        url="https://github.com/valohai/leval",
        author="Valohai",
        author_email="info@valohai.com",
        maintainer="Aarni Koskela",
        maintainer_email="akx@iki.fi",
        license="MIT",
        include_package_data=True,
        install_requires=[],
        tests_require=dev_dependencies,
        extras_require={"dev": dev_dependencies},
        packages=setuptools.find_packages(".", include=("leval*",)),
    )
