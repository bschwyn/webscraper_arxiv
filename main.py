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
import requests
from bs4 import BeautifulSoup
import time

from requests import RequestException


from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base


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

    def __init__(self):
        self.user_agent = "Googlebot"
        self.base_url = "https://arxiv.org"
        self.categories = [
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


    def parse_soup_test(self):

        print("TESTING")
        filename = 'soup_page2.html'
        with open(filename, 'r', encoding='utf-8') as file:
            html_content = file.read()
        soup = BeautifulSoup(html_content, 'html.parser')

        articles = soup.find_all('dt')
        article_data = []

        for article in articles:
            article_info = {}

            title_tag = article.find_next_sibling('dd').find('div',class_='list-title')
            if title_tag:
                article_info['title'] = title_tag.get_text(strip=True).replace('Tittle:', '').strip()

            # Extract the atuthors
            author_tags = article.find_next_sibling('dd').find('div', class_='list-authors').find_all('a')
            if author_tags:
                article_info['authors'] = [author.get_text(strip=True) for author in author_tags]

                # Extract the subjects
            subject_tag = article.find_next_sibling('dd').find('div', class_='list-subjects')
            if subject_tag:
                article_info['subjects'] = subject_tag.get_text(strip=True).replace('Subjects:', '').strip()

            # Extract the links
            article_info['links'] = {}
            link_tags = article.find_all('a')
            for link in link_tags:
                href = link.get('href')
                if href and 'abs' in link.get('href'):
                    article_info['links']['abstract'] = link.get('href')
                if href and 'pdf' in link.get('href'):
                    article_info['links']['pdf'] = link.get('href')
                if href and 'html' in link.get('href'):
                    article_info['links']['html'] = link.get('href')
                if href and 'format' in link.get('href'):
                    article_info['links']['other_formats'] = link.get('href')

            # Add the article information to the list
            article_data.append(article_info)

            for data in article_data:
                print(data)

    def get_links(self):
        base_url = self.base_url
        months = range(1,13)
        years = range(1991, 2025)
        page_size = 100

        #for now
        year = 2023
        month = 10
        category = "hep-th"
        years = [year]
        years = [2020]
        months = [month]
        categories = [category]
        for category in categories:
            for year in years:
                for month in months:

                    page = 0
                    all_data = []
                    while True:
                        #get URL data
                        url = f"{base_url}/list/{category}/{year}-{month}?skip={page*page_size}&show={page_size}"
                        print(url)

                        try:
                            response = requests.get(url, timeout=10)
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
                        # find article links
                        #links = [a['href'] for a in soup.find_all('a', href=True) if /abs/ in a['href']]
                        # if not links:
                        #     break
                        # all_links.extend(links)
                        page +=1
                        time.sleep(1)
                    self.save_data(all_data)


class Database:
    def __init__(self):
        # Database connection parameters
        self.DB_NAME = "arxiv_db"
        self.DB_USER = "test"
        self.DB_PASS = "test"
        self.DB_HOST = "localhost"
        self.DB_PORT = "5432"

    # Function to connect to the PostgreSQL database
    def connect_to_db(self):
        try:
            conn = psycopg2.connect(
                dbname=self.DB_NAME,
                user=self.DB_USER,
                password=self.DB_PASS,
                host=self.DB_HOST,
                port=self.DB_PORT
            )
            return conn
        except Exception as e:
            print(f"Error connecting to the database: {e}")
            return None

    # Function to create the users table
    def create_table(self, conn):
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100),
                        email VARCHAR(100)
                    )
                """)
                conn.commit()
                print("Table 'users' created successfully.")
        except Exception as e:
            print(f"Error creating table: {e}")
            conn.rollback()

    def create_table_articles(self, conn):




        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS articles (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100),
                        email VARCHAR(100)
                    )
                """)
                conn.commit()
                print("Table 'users' created successfully.")
        except Exception as e:
            print(f"Error creating table: {e}")
            conn.rollback()
    # Function to insert sample data into the users table
    def insert_data(self, conn):
        try:
            with conn.cursor() as cursor:
                insert_query = """
                    INSERT INTO users (name, email) VALUES (%s, %s)
                """
                users = [
                    ('John Doe', 'john.doe@example.com'),
                    ('Jane Smith', 'jane.smith@example.com')
                ]
                cursor.executemany(insert_query, users)
                conn.commit()
                print("Data inserted successfully.")
        except Exception as e:
            print(f"Error inserting data: {e}")
            conn.rollback()

    def insert_article(self, data):

    # Function to query and print data from the users table
    def query_data(self, conn):
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users")
                rows = cursor.fetchall()
                print("Data from 'users' table:")
                for row in rows:
                    print(row)
        except Exception as e:
            print(f"Error querying data: {e}")


if __name__ == "__main__":

    psql = Database()
    conn = psql.connect_to_db()
    if conn is not None:
        psql.create_table(conn)
        psql.insert_data(conn)
        psql.query_data(conn)
        conn.close()

    #arxiv_scraper = Crawler()
    #arxiv_scraper.get_links()

