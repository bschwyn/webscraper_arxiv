"""

what data am I collection?
- title
- author
- pdf link
- abstract
- date

technical stack
- python
- requests -- make HTTP requests
- beautifulsoup --- parsing html
- Scrapy --- framework for complex & scalable scraping tasks

#other considerations, Selenium, Pandas

Scraper components:
- initialization (rate limits, headers (why config for headers, url, proxies?)
- request handling, retry logic

Scale:
2.4 million articles
2500 bytes
= 6 Gigs

since this is entirely a single site, it would take ~ 30 days to crawl at 1 link/s, and a year at the 1 page per 15 seconds
that the robots.txt file requires

Acquiring URLS:
- 1) find all categories
- 2) paginate through arxiv.org/list/{category}/{year}-{month}?skip&show=25
- 3) start by just choosing one category

anticipated issues:
- I'm going to be rate limited on #requests
- rate limited on data

"""
import requests
from bs4 import BeautifulSoup
import time


class LinkScraper:


    def __init__(self):
        base_url = "https://arxiv.org"
        categories = [
            "econ",
            "eecs",
            "stat",
            "q-fin",
            "q-bio",
            "cs",
            "math",
            "asto-ph",
            "cond-mat",
            "gr-qc",
            "hep-ex",
            "hep-lat",
            "hep-ph",
            "hep-th",
            "nlin",
            "nucl-ex",
            "nucl-th",
            "physics",
            "quant-ph"
        ]

    def get_links(self):
        base_url = self.base_url
        months = range(1,13)
        years = range(1991, 2025)
        page_size = 100

        #for now
        year = 1991
        month = 10
        category = "hep-th"
        years = [year]
        months = [month]
        categories = [category]
        for category in categories:
            for year in years:
                for month in months:

                    page = 0
                    all_links = []
                    while True:
                        #get URL data
                        url = f"{base_url}/list/{category}/{year}-{month}?skip={page*page_size}&show={page_size}"
                        response = requests.get(url)
                        if response.status_code != 200:
                            print(f"Fail to retrive page {url}")
                            break

                        soup  = BeautifulSoup(response.content, 'html.parser')
                        # find article links
                        #links = [a['href'] for a in soup.find_all('a', href=True) if /abs/ in a['href']]
                        if not links:
                            break
                        all_links.extend(links)
                        page +=1
                        time.sleep(1)






if __name__ == "__main__":
    print("test")
