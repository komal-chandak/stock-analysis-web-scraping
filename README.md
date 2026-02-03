# 📈 Stock Analysis Web Scraping 

## Overview

This script scrapes **Over-The-Counter (OTC) stock data** from **stockanalysis.com** using **Selenium and BeautifulSoup**.  
It collects both **tabular market data** and **detailed company profile information**, and exports the final dataset as a CSV file for further analysis.

The scraper is designed to handle:
- Dynamic content (JavaScript-rendered pages)
- Pagination across multiple listing pages
- Popups and UI interruptions
- Company-level deep scraping
  
---

## Supported Stock Categories

The same scraping pipeline is reusable across multiple stock categories on *stockanalysis.com*.  
By changing the starting URL, the script can scrape:

- **Mid-Cap Stocks**
- **Nano-Cap Stocks**

Example URLs used:
- OTC Stocks: `https://stockanalysis.com/list/otc-stocks/`
- Mid-Cap Stocks: `https://stockanalysis.com/list/mid-cap-stocks/`
- Nano-Cap Stocks: `https://stockanalysis.com/list/nano-cap-stocks/`


## Data Collected

### From OTC stocks listing pages:
- Symbol  
- Company Name  
- Symbol URL  

### From individual company profile pages:
- Country  
- Number of Employees  
- CEO  
- Executive leadership list  
- Number of Executives  
- Company Address  
- Website  

---

## Tech Stack & Libraries

- **Python**
- **Selenium** – browser automation for dynamic content
- **BeautifulSoup** – HTML parsing
- **Pandas** – data transformation and storage
- **Chrome WebDriver**
- **tqdm** – progress tracking

---

## Disclaimer

Please review and comply with the target website’s terms of service before scraping.

