"""
Victor Prime AGI - Setup Configuration
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="victor_prime_agi",
    version="1.0.0",
    author="Brandon Emery",
    author_email="",
    description="Victor Prime Synthesis Core AGI - A highly modular and extensible AGI framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MASSIVEMAGNETICS/victor_llm",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "victor-core=victor_core.main:main",
            "victor-agi=VICTOR_AGI_LLM:main",
        ],
    },
    include_package_data=True,
    package_data={
        "victor_core": ["**/*.yaml", "**/*.json"],
        "victor": ["**/*.yaml"],
    },
)
