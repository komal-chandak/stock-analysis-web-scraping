from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import random
from bs4 import BeautifulSoup
import csv
import time
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from tqdm import tqdm
import pandas as pd
import os

def getSoup(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup

def get_page_html(url):
    # List of user agents
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14"
    ]
    try:
        options = Options()
        options.add_argument(f'user-agent={random.choice(user_agents)}')

        driver = webdriver.Chrome(options=options)
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        html = driver.page_source
        return html
    except Exception as e:
        print(e)
        return None


def extract_table(html_content_main_page):
    rows=[]
    base_url = 'https://stockanalysis.com'
    table = getSoup(html_content_main_page).find('table', {'id': 'main-table'})
    tbody = table.find('tbody')
    for row in tbody.find_all('tr'):
        cols = row.find_all('td')
        symbol_tag = cols[1].find('a')
        symbol_href = base_url + symbol_tag['href'] if symbol_tag and symbol_tag.has_attr('href') else ''

        data = {
            'No': cols[0].text.strip(),
            'Symbol': cols[1].text.strip(),
            'Symbol URL': symbol_href,
            'Company Name': cols[2].text.strip(),
            'Market Cap': cols[3].text.strip(),
            'Stock Price': cols[4].text.strip(),
            '% Change': cols[5].text.strip(),
            'Revenue': cols[6].text.strip(),
        }
        rows.append(data)
    return rows

def close_popup_if_present(driver):
    try:
        # Wait briefly in case popup takes a second to load
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Close"]'))
        )
        close_button = driver.find_element(By.CSS_SELECTOR, '[aria-label="Close"]')
        close_button.click()
        print("Popup closed.")
        time.sleep(1)  # allow UI to update
    except:
        # Popup not present — that's fine
        pass

def setup_driver():
    options = Options()
    options.headless = False  
    driver = webdriver.Chrome(options=options)
    return driver

def scrape_all_pages(start_url):
    driver = setup_driver()
    driver.get(start_url)
    all_data = []

    while True:
        # Wait for table to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "main-table"))
        )
        html = driver.page_source
        page_data = extract_table(html)
        all_data.extend(page_data)
        print(f"Extracted {len(page_data)} rows, total so far: {len(all_data)}")
        time.sleep(10) 
        close_popup_if_present(driver)
        try:
            next_button = driver.find_element(By.XPATH, "//button[span[text()='Next']]")
            if next_button.get_attribute('disabled') is not None:
                print("Reached last page.")
                break
            else:
                next_button.click()
                time.sleep(2)  # Wait for new page to load
        except Exception as e:
            print("No more pages or error occurred:", e)
            break

    driver.quit()
    return all_data


def get_profile_url(html, base_url="https://stockanalysis.com"):
    nav_menu = getSoup(html).find('ul', class_='navmenu')
    if nav_menu:
        profile_li = nav_menu.find('a', attrs={'data-title': 'Profile'})
        if profile_li and profile_li.has_attr('href'):
            return base_url + profile_li['href']
    return None

def get_company_data(html_content_profile_page):
    # available_keys = ['Country', 'Founded', 'Industry', 'Sector', 'Employees', 'CEO']
    desired_keys = ['Country', 'Employees', 'CEO']
    company_data = {key: None for key in desired_keys}
    try:    
        soup = getSoup(html_content_profile_page)
        table = soup.find('table', class_='w-full')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                key = cols[0].text.strip()
                value = cols[1].text.strip()
                if key in company_data:
                    company_data[key] = value
    except Exception as e:
        print('Error in table1', e)

    executives = []
    try:
        table = soup.find('table', class_='mb-6 w-full text-base xs:mb-8') 
        if table:
            rows = table.find_all('tr')
            for row in rows[1:]:  
                cols = row.find_all('td')
                if len(cols) == 2:
                    name = cols[0].text.strip()
                    position = cols[1].text.strip()
                    executives.append({'Name': name, 'Position': position})

        company_data['Executives'] = executives
        try:
            company_data['Number of Executives'] = len(executives)
        except Exception as e:
            print('error in number of executives',e)
            company_data['Number of Executives'] = 0 
    except Exception as e: 
        print('error in table2:',e)

    try:
        contact_heading = soup.find('h2', string="Contact Details")
        if contact_heading:
            contact_table = contact_heading.find_next('table')
            if contact_table:
                rows = contact_table.find_all('tr')
                try:
                    address_cell = rows[0].find('td')
                    if address_cell:
                        address_lines = address_cell.find_all('div')[1].stripped_strings
                        company_data["Address"] = ', '.join(address_lines)
                except Exception as e:
                    print('error in address data:',e)
                    company_data["Address"] = None

                try:
                    for row in rows[1:]:
                        cols = row.find_all('td')
                        if len(cols) == 2:
                            label = cols[0].text.strip()
                            value = cols[1].text.strip()
                            if "Phone" in label:
                                # contact_data["Phone"] = value
                                pass
                            elif "Website" in label:
                                company_data["Website"] = value
                except Exception as e:
                    print('Error in domain data:', e)
                    company_data["Website"] = None
        else:
            company_data["Website"] = None
            company_data["Address"] = None
    except Exception as e:
        print('error in table 3:', e)
    
    return company_data

if __name__ == "__main__":

# Part 1 to get the main table
    # used to scrape nanocap and midcap stocks as well
    # nano_cap_stocks_url = "https://stockanalysis.com/list/nano-cap-stocks/"
    # midcap_cap_stocks_url = "https://stockanalysis.com/list/mid-cap-stocks/"
    url = "https://stockanalysis.com/list/otc-stocks/"  
    all_rows = scrape_all_pages(url)
    print(f"\nTotal rows scraped: {len(all_rows)}")
    df = pd.DataFrame(all_rows)
    # df.to_csv("otc_stocks_table.csv", index=False)

# Part 2 to get all the url info from table
    # df = pd.read_csv("otc_stocks_table.csv")

    df.drop(columns=['No','Market Cap','Stock Price','% Change','Revenue'], inplace=True)
    df['Country'] = None
    df['Employees'] = None
    df['CEO'] = None
    df['Executives'] = None
    df['Number of Executives'] = None
    df['Address'] = None
    df['Website'] = None

    try:
        for idx, row in tqdm(df.iterrows(),total=len(df), desc="Scraping companies"):
            url = row["Symbol URL"]
            profile_url = url + 'company/'
            try:
                html_content_profile_page = get_page_html(profile_url)
            except:
                html_content_main_page = get_page_html(url)
                profile_url = get_profile_url(html_content_main_page)
                html_content_profile_page = get_page_html(profile_url)

            company_data = get_company_data(html_content_profile_page)

            df.at[idx, "Country"] = company_data.get("Country")
            df.at[idx, "Employees"] = company_data.get("Employees")
            df.at[idx, "CEO"] = company_data.get("CEO")
            df.at[idx, "Executives"] = company_data.get("Executives")
            df.at[idx, "Number of Executives"] = company_data.get("Number of Executives")
            df.at[idx, "Address"] = company_data.get("Address")
            df.at[idx, "Website"] = company_data.get("Website")
    except Exception as e:
        print('Error:',e)
    df.to_csv("otc_stocks.csv", index=False)
       
        


   

