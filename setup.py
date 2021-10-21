from setuptools import setup

setup(
    name='pypoller',
    version='0.1.6',
    python_requires='>=3.7',
    install_requires=['pymodbus'],
    scripts=['pypoller.py'],
)
