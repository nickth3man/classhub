from setuptools import setup, find_packages
import os

# Read the contents of the requirements file
with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as f:
    requirements = f.read().splitlines()
    # Remove comments and empty lines
    requirements = [line for line in requirements if line and not line.startswith('#')]

setup(
    name="academic_organizer",
    version="0.1.0",
    description="A comprehensive desktop application for students to organize educational materials, track assignments, and manage courses",
    author="Academic Organizer Team",
    author_email="info@academicorganizer.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=requirements,
    python_requires=">=3.8, <3.11",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Education",
        "Topic :: Office/Business :: Scheduling",
    ],
    entry_points={
        "console_scripts": [
            "academic-organizer=academic_organizer.core.main:main",
        ],
    },
)