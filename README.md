# citation-crawler

Asynchronous high-concurrency dblp crawler, use with caution!

异步高并发引文数据爬虫，慎用

Only support Semantic Scholar currently.

目前支持从Semantic Scholar上爬references和citations

Crawl papers from dblp and connect them into an undirected graph. Each edge is a paper, each node is an author.

爬引文数据并将其组织为无向图。图的节点是文章，边是引用关系

## Install

```sh
pip install citation-crawler
```

## Usage

### Config environment variables

* `CITATION_CRAWLER_MAX_CACHE_DAYS_AUTHORS`: 
  * save cache for a paper authors page (to get authors of a published paper) for how many days
  * default: `-1` (cache forever, since authors of a paper are not likely to change)
* `CITATION_CRAWLER_MAX_CACHE_DAYS_REFERENCES`: 
  * save cache for a reference page (to get references of a published paper) for how many days
  * default: `-1` (cache forever, since references of a paper are not likely to change)
* `CITATION_CRAWLER_MAX_CACHE_DAYS_CITATIONS`
  * save cache for a citation page (to get citations of a published paper) for how many days
  * default: `7` (citations of a paper may change frequently)
* `CITATION_CRAWLER_MAX_CACHE_DAYS_PAPER`
  * save cache for a paper detail page (to get details of a paper) for how many days
  * default: `-1` (cache forever, since detailed information of a published paper are not likely to change)
* `HTTP_PROXY`
  * Set it `http://your_user:your_password@your_proxy_url:your_proxy_port` if you want to use proxy