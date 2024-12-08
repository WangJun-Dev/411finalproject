from setuptools import setup, find_packages

setup(
    name="stock-trading",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'flask',
        'requests',
        'python-dotenv',
        'pytest',
        'pytest-mock'
    ],
)