import psycopg2
from psycopg2 import sql
import requests

# Database connection parameters
DB_NAME = "arxiv_db"
DB_USER = "test"
DB_PASS = "test"
DB_HOST = "localhost"
DB_PORT = "5432"

# Function to connect to the PostgreSQL database
def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

# Function to create the users table
# def create_table(conn):
#     try:
#         with conn.cursor() as cursor:
#             cursor.execute("""
#                 CREATE TABLE IF NOT EXISTS users (
#                     id SERIAL PRIMARY KEY,
#                     name VARCHAR(100),
#                     email VARCHAR(100)
#                 )
#             """)
#             cursor.execute("""
#                 DROP TABLE articles
#             """)
#             conn.commit()
#             print("Table 'users' created successfully.")
#     except Exception as e:
#         print(f"Error creating table: {e}")
#         conn.rollback()

# Function to insert sample data into the users table
def insert_data_test(conn):
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

# Function to query and print data from the users table
def query_data(conn):
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM articles")
            rows = cursor.fetchall()
            print("Data from 'users' table:")
            for row in rows:
                print(row)
    except Exception as e:
        print(f"Error querying data: {e}")

def get_terence_tao_papers(conn):
    try:
        with conn.cursor() as cursor:
            x = "SELECT pdf FROM articles where 'terence tao' in authors limit 100"
            cursor.execute("SELECT pdf from articles where authors like '%Terence Tao%'")
            rows = cursor.fetchall()
            print("Data from 'articles' table:")
            print(len(rows))
            for row in rows:
                print(row)
            with open('text_files/terence_tao.txt', 'w') as f:
                for row in rows:
                    print(row)
                    f.write( ', '.join([str(item) for item in row]) + '\n')

    except Exception as e:
        print(f"Error querying data: {e}")

def download_pdfs():
    base_url = 'https://arxiv.org'
    with open('text_files/terence_tao.txt', 'r') as file:
        urls = file.readlines()

    for url in urls:
        full_url = base_url + url
        response = requests.get(full_url)
        new_filename = url.replace('/','-')
        with open('text_files/terence_tao/' + new_filename+ '.pdf', 'wb') as f:
            f.write(response.content)
    print('xxxxx')

# Main function to run the example
def main():
    conn = connect_to_db()
    if conn is not None:
        #create_table(conn) #DROP TABLE!
        #insert_data(conn)
        query_data(conn)
        get_terence_tao_papers(conn)
        conn.close()
    download_pdfs()

if __name__ == "__main__":
    main()