from setuptools import setup, find_packages

setup(
    name="pinetree-agent-sdk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "web3>=6.0.0",
        "eth-account>=0.8.0"
    ],
    description="Headless SDK for Pine Tree Predict Agentic Liquidity",
    author="Pine Tree Predict",
)
