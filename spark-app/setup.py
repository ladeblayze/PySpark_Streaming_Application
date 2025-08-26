from setuptools import setup, find_packages

setup(
    name="spark-streaming-processor",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "pyspark>=3.5.0",
    ],
    extras_require={
        "test": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "streaming-processor=streaming_app:main",
        ],
    },
)