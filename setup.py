"""
Audio2Text - Transcripción de Audio en Tiempo Real
Setup configuration for package distribution
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = (this_directory / "requirements.txt").read_text(encoding='utf-8').splitlines()

setup(
    name="audio2text-cenf",
    version="0.9.2",
    author="CENF",
    author_email="soporte@cenfarg.com.ar",
    description="Aplicación de transcripción de audio en tiempo real usando IA",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CENFARG/Audio2Text",
    project_urls={
        "Bug Tracker": "https://github.com/CENFARG/Audio2Text/issues",
        "Documentation": "https://github.com/CENFARG/Audio2Text/blob/main/docs/",
        "Source Code": "https://github.com/CENFARG/Audio2Text",
    },
    packages=find_packages(exclude=["tests", "tests.*", "scripts", "_build_artifacts", "_old_versions_archive"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: Microsoft :: Windows",
        "Natural Language :: Spanish",
        "Natural Language :: English",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "audio2text=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.html", "*.ico", "*.png"],
    },
    keywords="transcription audio speech-to-text whisper groq ai real-time",
    zip_safe=False,
)
