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

When aquiring the URLs tfrom the arxiv list, there are several different ways to do this.
- 1) the arxiv:2407.03249 link
- 2) I already have the Title, Authors, Subjects

anticipated issues:
- I'm going to be rate limited on #requests
- rate limited on data



"""
import json
import requests
import time

from bs4 import BeautifulSoup
from requests import RequestException

from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import JSONB


import psycopg2


class Parser:

    def __init__(self):
        pass

    def parse_title(self, article):
        dd_tag = article.find_next_sibling('dd')
        if dd_tag:
            title_tag = dd_tag.find('div', class_='list-title')
            if title_tag:
                return title_tag.get_text(strip=True).replace('Tittle:', '').strip()

    def parse_authors(self, article):
        dd_tag = article.find_next_sibling('dd')
        if dd_tag:
            author_tags = dd_tag.find('div', class_='list-authors').find_all('a')
            if author_tags:
                return [author.get_text(strip=True) for author in author_tags]

    def parse_subjects(self, article):
        dd_tag = article.find_next_sibling('dd')
        if dd_tag:
            subject_tag = dd_tag.find('div', class_='list-subjects')
            if subject_tag:
                return subject_tag.get_text(strip=True).replace('Subjects:', '').strip()

    def parse_links(self, article):
        link_info = {}
        link_tags = article.find_all('a')
        if link_tags:
            for link in link_tags:
                href = link.get('href')
                if href and 'abs' in link.get('href'):
                    link_info['abstract'] = link.get('href')
                if href and 'pdf' in link.get('href'):
                    link_info['pdf'] = link.get('href')
                if href and 'html' in link.get('href'):
                    link_info['html'] = link.get('href')
                if href and 'format' in link.get('href'):
                    link_info['other_formats'] = link.get('href')
        return link_info


class Crawler:

    def __init__(self, db):
        self.user_agents = [
            'Mozilla/5.0 (X11; CrOS x86_64 10066.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
            'XYZ/3.0',
            'Mozilla/5.0',
            'Mozilla/5.0 (compatible; Googlebot/2.1; +https://www.google.com/bot.html)'
        ]
        self.base_url = "https://arxiv.org"
        self.db = db




    def parse_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')

        save_html = True
        if save_html:
            with open(f"soup_page.html", "w", encoding='utf-8') as file:
                file.write(soup.prettify())

        articles = soup.find_all('dt')
        seen_articles = set()
        article_data = []
        parser = Parser()
        for article in articles:
            article_info = {}
            article_info['title'] = parser.parse_title(article)

            article_info['authors'] = parser.parse_authors(article)
            article_info['subjects'] = parser.parse_subjects(article)
            article_info['links'] = parser.parse_links(article)

            # Add the article information to the list
            if article_info['title'] in seen_articles:
                break
            article_data.append(article_info)
            seen_articles.add(article_info['title'])

            for data in article_data:
                print(data)
        return article_data

    def get_links(self):
        base_url = self.base_url
        months = range(1,13)
        years = range(1991, 2025)
        page_size = 100

        categories = [
            "econ",
            "eecs",
            "stat",
            "q-fin",
            "q-bio",
            "cs",
            "math",
            "astro-ph",
            "cond-mat",
            "gr-qc",
            "hep-ex",
            "hep-lat",
            "hep-ph",
            "hep-th",
            "math-ph",
            "nlin",
            "nucl-ex",
            "nucl-th",
            "physics",
            "quant-ph"
        ]

        years = {
            "econ": range(2017, 2025),
            "eecs": range(2017, 2025),
            "stat": range(2007, 2025),
            "q-fin": range(2008, 2025),
            "q-bio": range(2003, 2025),
            "cs": range(1993, 2025),
            "math": range(1992, 2025),
            "astro-ph": range(1992, 2025),
            "cond-mat": range(1992, 2025),
            "gr-qc": range(1992, 2025),
            "hep-ex": range(1994, 2025),
            "hep-lat": range(1992, 2025),
            "hep-ph": range(1992, 2025),
            "hep-th": range(1991, 2025),
            "math-ph": range(1996, 2025),
            "nlin": range(1993, 2025),
            "nucl-ex": range(1994, 2025),
            "nucl-th": range(1992, 2025),
            "physics": range(1996, 2025),
            "quant-ph": range(1994, 2025)
        }

        categories = ["econ", "eecs"]
        for category in categories:
            year_range = years[category]
            for year in year_range:
                for month in months:

                    page = 0
                    all_data = []
                    while True:
                        #get URL data
                        url = f"{base_url}/list/{category}/{year}-{month}?skip={page*page_size}&show={page_size}"
                        print(url)

                        try:
                            response = requests.get(url, timeout=10, headers={'User-Agent': self.user_agents[4]})
                            response.raise_for_status()
                        except RequestException as e:
                            print(f"Error fetching {url}: {e}")
                            print(f"url status code: {response.status_code}")

                        data = self.parse_html(response.content)
                        all_data.extend(data)
                        if not data:
                            print("no more data!")
                            print("page=")
                            print(page)
                            print(len(all_data))
                            break

                        page +=1
                        time.sleep(1)
                    self.save_data(all_data)
    def save_data(self, data):
        self.db.save_crawler_data(data)

Base = declarative_base()
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, index=True)

class ArticleJson(Base):
    __tablename__ = "articles_json"
    id = Column(Integer, primary_key=True)
    data = Column(JSONB)


class DatabaseManager:
    def __init__(self):
        # Database connection parameters
        DB_NAME = "arxiv_db"
        DB_USER = "test"
        DB_PASS = "test"
        DB_HOST = "localhost"
        DB_PORT = "5432"
        # SQLAlchemy setup
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        self.engine = create_engine(DATABASE_URL)
        self.sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)

    def insert_data(self):
        session = self.sessionLocal()
        users = [
            User(name="John Doe", email="john.doe@example.com"),
            User(name="Jane Smith", email="jane.smith@example.com")
        ]
        session.add_all(users)
        session.commit()

    def save_crawler_data(self, arxiv_data):
        session = self.sessionLocal()
        # json for now, better to get the data and then when I know what I'm doing with it I can organize
        json = [ArticleJson(data=entry) for entry in arxiv_data]
        session.bulk_save_objects(json)
        session.commit()


    def query_data(self):
        session = self.sessionLocal()
        users = session.query(User).all()
        print("Data from 'users' table:")
        for user in users:
            print(f"ID: {user.id}, Name: {user.name}, Email: {user.email}")

    def query_arxivjson_data(self):

        session = self.sessionLocal()
        data  = session.query(ArticleJson).all()
        print("data from 'articles - json' table:")
        for j in data:
            print(f"ID: {j.id}, Name: {j.data}")


if __name__ == "__main__":

    psql = DatabaseManager()
    psql.create_tables()
    psql.insert_data()
    psql.query_data()



    arxiv_scraper = Crawler(psql)
    arxiv_scraper.get_links()
    psql.query_arxivjson_data()

