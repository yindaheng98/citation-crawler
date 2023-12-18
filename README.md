# citation-crawler

Asynchronous high-concurrency citation crawler, use with caution!

异步高并发引文数据爬虫，慎用

Only support Semantic Scholar currently.

目前支持从Semantic Scholar上爬references和citations

Crawl papers based on BFS(Breath First Search) from the citation network and connect them into an undirected graph. Each edge is a paper, each node is an author.

基于广度优先搜索爬引文数据并将其组织为无向图。图的节点是文章，边是引用关系

Neo4J output compatible with [dblp-crawler](https://github.com/yindaheng98/dblp-crawler)

Neo4J形式的输出和[dblp-crawler](https://github.com/yindaheng98/dblp-crawler)兼容，可以自动识别相同paper不产生重复节点，并可以匹配数据库中已记录的作者，从而为新加入数据库的paper连接作者

![](asserts/graph.png)

## Install

```sh
pip install citation-crawler
```

## Usage

```sh
python -m citation_crawler -h
usage: __main__.py [-h] [-y YEAR] [-l LIMIT] -k KEYWORD [-p PID] [-a AID] {networkx,neo4j} ...

positional arguments:
  {networkx,neo4j}      sub-command help
    networkx            Write results to a json file.
    neo4j               Write result to neo4j database

optional arguments:
  -h, --help            show this help message and exit
  -y YEAR, --year YEAR  Only crawl the paper after the specified year.
  -l LIMIT, --limit LIMIT
                        Limitation of BFS depth.
  -k KEYWORD, --keyword KEYWORD
                        Specify keyword rules.
  -p PID, --pid PID     Specified a list of paperId to start crawling.
  -a AID, --aid AID     Specified a list of authorId to start crawling.
```

```sh
python -m citation_crawler networkx -h
usage: __main__.py networkx [-h] --dest DEST

optional arguments:
  -h, --help   show this help message and exit
  --dest DEST  Path to write results.
```

```sh
python -m citation_crawler neo4j -h   
usage: __main__.py neo4j [-h] [--auth AUTH] --uri URI

optional arguments:
  -h, --help           show this help message and exit
  --username USERNAME  Auth username to neo4j database.
  --password PASSWORD  Auth password to neo4j database.
  --uri URI            URI to neo4j database.
```

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
* `CITATION_CRAWLER_MAX_CACHE_DAYS_INIT_AUTHOR`
  * save cache for an author page (to init papers from specified author by `-a`) for how many days
  * default: `7` (author may publish frequently)
* `HTTP_PROXY`
  * Set it `http://your_user:your_password@your_proxy_url:your_proxy_port` if you want to use proxy
* `HTTP_TIMEOUT`
  * Timeout for each http request, in seconds
* `HTTP_CONCORRENT`
  * Concurrent HTTP requests
  * default: `8`

### Write to a JSON file

e.g. write to `summary.json`:

```sh
python -m citation_crawler -k video -k edge -p 27d5dc70280c8628f181a7f8881912025f808256 -a 1681457 networkx --dest summary.json
```

#### JSON format

```json
{
  "nodes": {
    "<paperId of a paper in Semantic Scholar>": {
      "paperId": "<paperId of this paper in Semantic Scholar>",
      "dblp_key": "<dblp id of this paper>",
      "title": "<title of this paper>",
      "year": "int <publish year of this paper>",
      "doi": "<doi of this paper>",
      "authors": [
        {
          "authorId": "<authorId of this person in Semantic Scholar>",
          "name": "<name of this person>",
          "dblp_name": [
            "<disambiguation name of this person in dblp>",
            "<disambiguation name of this person in dblp>",
            "<disambiguation name of this person in dblp>",
            "......"
          ]
        },
        { ...... },
        { ...... },
        ......
      ]
    },
    "<paperId of a paper in Semantic Scholar>": { ...... },
    "<paperId of a paper in Semantic Scholar>": { ...... },
    ......
  },
  "edges": [
    [
        "<paperId of a paper in Semantic Scholar>",
        "<paperId of a reference in the above paper>"
    ],
    [ ...... ],
    [ ...... ],
    ......
  ]
```

### Write to a Neo4J database

```sh
docker pull neo4j
docker run --rm -it -p 7474:7474 -p 7687:7687 -v $(pwd)save/neo4j:/data -e NEO4J_AUTH=none neo4j
```

e.g. write to `neo4j://localhost:7687`:

```sh
python -m dblp_crawler -k video -k edge -p 27d5dc70280c8628f181a7f8881912025f808256 -a 1681457 neo4j --uri neo4j://localhost:7687
```

### Get initial paper list or author list from a Neo4J database

```sh
python -m dblp_crawler -k video -k edge -a "importlib.import_module('citation_crawler.init').papers_in_neo4j('neo4j://localhost:7687')" neo4j --uri neo4j://localhost:7687
```

```sh
python -m dblp_crawler -k video -k edge -p "importlib.import_module('citation_crawler.init').authors_in_neo4j('neo4j://localhost:7687')" neo4j --uri neo4j://localhost:7687
```

`importlib.import_module` is flexible, you can import your own variables through this.
