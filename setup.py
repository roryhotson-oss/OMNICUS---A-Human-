#!/usr/bin/env python3
"""
OMNICUS Setup Script
Alternative setup for pip install
"""

from setuptools import setup, find_packages

setup(
    name="omnicus",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "aiohttp>=3.9.0",
        "websockets>=12.0",
        "httpx>=0.26.0",
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "python-telegram-bot>=21.0",
        "python-binance>=1.0.19",
        "ccxt>=4.2.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "requests>=2.31.0",
        "sqlalchemy>=2.0.0",
        "aiosqlite>=0.19.0",
        "twilio>=8.0.0",
        "openai>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "omnicus=main:main",
        ],
    },
)
