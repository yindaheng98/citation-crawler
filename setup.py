#!/usr/bin/env python
# coding: utf-8

from setuptools import setup

with open("README.md", "r", encoding='utf8') as fh:
    long_description = fh.read()

package_dir = {
    'citation_crawler': 'citation_crawler',
    'citation_crawler.crawlers': 'citation_crawler/crawlers',
    'citation_crawler.summarizers': 'citation_crawler/summarizers',
    'citation_crawler.init': 'citation_crawler/init',
}

setup(
    name='citation_crawler',
    version='2.3.2',
    author='yindaheng98',
    author_email='yindaheng98@gmail.com',
    url='https://github.com/yindaheng98/citation-crawler',
    description=u'Asynchronous high-concurrency citation crawler, use with caution!',
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir=package_dir,
    packages=[key for key in package_dir],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'dblp-crawler>=2.1',
        'python-dateutil>=2.8.2',
        'neo4j>=5.15.0'
    ],
)
