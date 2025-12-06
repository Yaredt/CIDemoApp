from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="lead-gen-agents",
    version="1.0.0",
    author="Your Organization",
    author_email="contact@yourorg.com",
    description="Multi-Agent Lead Generation System for Enterprise Technology Modernization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Yaredt/CIDemoApp",
    packages=find_packages(exclude=["tests", "tests.*", "docs", "deployment"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "black>=23.12.0",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
            "isort>=5.13.0",
            "pre-commit>=3.6.0",
        ],
        "test": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "faker>=22.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "lead-gen=orchestration.main:main",
            "lead-gen-setup=scripts.setup:main",
        ],
    },
)
