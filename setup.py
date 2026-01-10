from setuptools import setup, find_packages

setup(
    name="axcent",
    version="0.1.0",
    description="The easiest way to build AI agents in Python",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="Mohin Uddin Shipon",
    author_email="sshiponudin22@gmail.com",
    url="https://github.com/ssshiponu/axcent",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "gemini": ["google-genai>=1.57.0"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
