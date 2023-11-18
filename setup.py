#!/usr/bin/env python
# coding: utf-8

from setuptools import setup

with open("README.md", "r", encoding='utf8') as fh:
    long_description = fh.read()

package_dir = {
    'citation_crawler': 'citation_crawler',
    'citation_crawler.crawlers': 'citation_crawler/crawlers',
    'citation_crawler.summarizers': 'citation_crawler/summarizers',
}

setup(
    name='citation_crawler',
    version='1.0.0',
    author='yindaheng98',
    author_email='yindaheng98@gmail.com',
    url='https://github.com/yindaheng98/citation-crawler',
    description=u'异步高并发citation爬虫，慎用',
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
        'dblp-crawler>=1.6.7',
    ],
)
