from selenium.webdriver.firefox.service import Service
from selenium import webdriver
import yfinance as yf
import mysql.connector
from datetime import datetime
import time
import pandas as pd
from tabulate import tabulate
import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup



def scrape_symbols(url):

    try:
        geckodriver_path = '/snap/bin/geckodriver'
        service = Service(executable_path = geckodriver_path)
        driver = webdriver.Firefox(service = service)

        # Set up Firefox WebDriver 
        driver.get(url)
        time.sleep(10) # Wait for the content to load. A 10 second delay ensures that the timestamp for news data always loads.
        html_data = driver.page_source
        driver.quit()
        soup = BeautifulSoup(html_data, 'html.parser')

        # Extract titles from all rows
        titles = []
        table_rows = soup.find_all('tr', class_='Bgc($hoverBgColor):h')
        for table_row in table_rows:
            title_element = table_row.find('a', class_='Fw(b)', attrs={'data-test': 'symbol-link'})
            if title_element:
                title = title_element.get_text(strip=True)
                titles.append(title)

        # Join titles into a single string separated by commas
        titles_string = ', '.join(titles)
        print(f'The extracted titles from {url} are: {titles_string}')

    except HTTPError as e:
        if e.response.status_code == 404:
            print(f"Invalid URL or webpage not found.")
        else:
            print(f"Error accessing the webpage: {e}")

    except Exception as e:
        print(f"Error during web scraping: {e}")
