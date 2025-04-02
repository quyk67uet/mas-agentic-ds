from setuptools import setup, find_packages

setup(
    name="ielts-assessment",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "streamlit",
        "langchain",
        "langchain-openai",
        "python-dotenv",
        "pandas",
    ],
    python_requires=">=3.8",
) 