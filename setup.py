"""Setup script for cz_nia."""
from setuptools import find_packages, setup

import cz_nia


setup(name='cz_nia',
      version=cz_nia.__version__,
      author='Tomas Pazderka',
      author_email='tomas.pazderka@nic.cz',
      url='https://github.com/tpazderka/python-cz-nia',
      description='Python application for communication with Czech NIA.',
      long_description=open('README.md').read(),
      long_description_content_type='text/markdown',
      python_requires='~=3.5',
      packages=find_packages(),
      install_requires=['zeep', 'xmlsec'],
      extras_require={'quality': ['isort', 'flake8', 'pydocstyle']})
