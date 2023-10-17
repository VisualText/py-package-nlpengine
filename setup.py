from setuptools import setup, find_packages
import glob
import os

setup(
    name='NLPPlus',
    version='1.0',
    packages=find_packages(),
    package_data={
      'NLPPlus': ['x64/*.dll'],
      'NLPPlus': [f'analyzers/{file}' for file in glob.glob('analyzers/**', recursive=True) if os.path.isfile(file)],
      'NLPPlus': [f'data/{file}' for file in glob.glob('data/**', recursive=True) if os.path.isfile(file)],
    },
    include_package_data=True,
    description='Python package for NLP++',
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/VisualText/py-package-nlpengine",
    author="David De Hilster",
    maintainer="Vladyslav Romasenko",
    maintainer_email="pinyz8221@gmail.com"
)
