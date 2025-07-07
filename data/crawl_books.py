from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import os
import time

options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

books = []
DATA_FILE = "backend/data/fantasy_books.json"
BASE_URL = "https://openlibrary.org/search?subject=Fantasy&sort=readinglog&page={}"

# Load existing data if available
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        books = json.load(f)

for page in range(1, 201): 
    print(f"\n=== Scraping page {page} ===")
    driver.get(BASE_URL.format(page))
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.searchResultItem"))
    )

    results = driver.find_elements(By.CSS_SELECTOR, "li.searchResultItem")
    for i in range(len(results)):
        try:
            # Refresh elements
            results = driver.find_elements(By.CSS_SELECTOR, "li.searchResultItem")
            item = results[i]
            title = item.find_element(By.CSS_SELECTOR, "h3.booktitle").text.strip()
            author = item.find_element(By.CSS_SELECTOR, ".bookauthor a").text.strip()
            try:
                rating = item.find_element(By.CSS_SELECTOR, "span[itemprop='ratingValue']").text.strip()
            except NoSuchElementException:
                rating = "N/A"
            link = item.find_element(By.TAG_NAME, "a")

            # Open detail page
            driver.execute_script("arguments[0].click();", link)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            # Description
            try:
                desc_elem = driver.find_element(By.CSS_SELECTOR, "div.read-more__content p")
                description = desc_elem.text.strip()
            except NoSuchElementException:
                description = "No description"

            # Cover Image
            try:
                img_elem = driver.find_element(By.CSS_SELECTOR, "img[itemprop='image']")
                img_url = img_elem.get_attribute("src")
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
            except NoSuchElementException:
                img_url = "N/A"

            # Publish Date
            try:
                pub_date = driver.find_element(By.CSS_SELECTOR, "span[itemprop='datePublished']").text.strip()
            except NoSuchElementException:
                pub_date = "N/A"

            # Publisher
            try:
                publisher = driver.find_element(By.CSS_SELECTOR, "a[itemprop='publisher']").text.strip()
            except NoSuchElementException:
                publisher = "N/A"

            # Language
            try:
                language = driver.find_element(By.CSS_SELECTOR, "span[itemprop='inLanguage'] a").text.strip()
            except NoSuchElementException:
                language = "N/A"

            # Page Count
            try:
                page_elem = driver.find_element(By.CSS_SELECTOR, "span[itemprop='numberOfPages']")
                pages = page_elem.text.strip()
            except NoSuchElementException:
                pages = "N/A"

            # Click the arrow to expand subject tags
            try:
                toggle = driver.find_element(By.CSS_SELECTOR, "span[class='clamp']")
                driver.execute_script("arguments[0].click();", toggle)
                time.sleep(0.5)  
            except NoSuchElementException:
                pass  

            # Subject Tags
            subjects = []
            try:
                subject_tags = driver.find_elements(By.CSS_SELECTOR, "span[class='clamp'] a")
                subjects = [s.text.strip() for s in subject_tags if s.text.strip()]
            except NoSuchElementException:
                subjects = []

            books.append({
                "title": title,
                "author": author,
                "description": description,
                "rating": rating,
                "image_url": img_url,
                "publish_date": pub_date,
                "publisher": publisher,
                "language": language,
                "pages": pages,
                "subjects": subjects
            })

            print(f"✓ {title}")
            driver.back()
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.searchResultItem"))
            )

        except Exception as e:
            print(f"⚠️ Error: {e}")
            continue
    
    # Save progress every 10 pages
    if page % 10 == 0:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(books, f, ensure_ascii=False, indent=2)
        print(f"💾 Progress saved at page {page} (Total books: {len(books)})")

driver.quit()

# Save to file
with open("backend/data/fantasy_books.json", "w", encoding='utf-8') as f:
    json.dump(books, f, ensure_ascii=False, indent=2)

print(f"\n=== Done. Scraped {len(books)} books. ===")
