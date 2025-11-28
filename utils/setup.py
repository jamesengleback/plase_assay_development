from setuptools import setup, find_packages 

setup(name='utils',
      packages=find_packages(),
      entry_points={
          'console_scripts': ['plate_utils=utils.cli:cli']
          },
      version='0.0.1',
      )
