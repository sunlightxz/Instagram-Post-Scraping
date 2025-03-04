from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

class InstagramScraper:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 10)
        # Initialize Google Sheets connection
        self.gs = self.setup_google_sheets()

    def setup_google_sheets(self):
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            'credentials.json', scope
        )
        return gspread.authorize(credentials)

    def save_to_sheets(self, results, sheet_name=None):
        try:
            if sheet_name is None:
                sheet_name = f"Instagram_Scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create new spreadsheet
            spreadsheet = self.gs.create(sheet_name)
            
            # Share with your email (replace with your email)
            spreadsheet.share('instagramscraper@maps-437318.iam.gserviceaccount.com', perm_type='user', role='writer')
            
            # Get the first sheet
            worksheet = spreadsheet.get_worksheet(0)
            
            # Prepare headers
            headers = ['Post URL', 'Content', 'Success', 'Error', 'Timestamp']
            worksheet.append_row(headers)
            
            # Prepare and write data
            for result in results:
                row = [
                    result['url'],
                    result.get('content', ''),
                    str(result['success']),
                    result.get('error', ''),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
                worksheet.append_row(row)

            print(f"\nData saved to Google Sheet: {sheet_name}")
            print(f"Spreadsheet URL: {spreadsheet.url}")
            return spreadsheet.url

        except Exception as e:
            print(f"Error saving to Google Sheets: {e}")
            return None

    def get_profile_posts(self, profile_url):
        try:
            self.driver.get(profile_url)
            time.sleep(3)  # Wait for initial load
            
            post_urls = set()  # Using set to avoid duplicates
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while True:
                # Get all post links on current view
                posts = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
                for post in posts:
                    post_urls.add(post.get_attribute('href'))
                
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Wait for content to load
                
                # Calculate new scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break  # If height didn't change, we've reached the bottom
                last_height = new_height
                
                print(f"Found {len(post_urls)} posts so far...")
                
            return list(post_urls)
            
        except Exception as e:
            print(f"Error getting profile posts: {e}")
            return []

    def get_post_description(self, post_url):
        try:
            self.driver.get(post_url)
            time.sleep(2)  # Wait for page to load
            
            # Find all elements with the specified classes
            elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "._ap3a._aaco._aacu._aacx._aad7._aade"
            )
            
            # Collect all text content
            descriptions = []
            for element in elements:
                text = element.text.strip()
                if text:  # Only add non-empty text
                    descriptions.append(text)
            
            return {
                'url': post_url,
                'content': '\n\n'.join(descriptions) if descriptions else None,
                'success': True
            }
            
        except Exception as e:
            print(f"Error processing {post_url}: {e}")
            return {
                'url': post_url,
                'content': None,
                'success': False,
                'error': str(e)
            }

    def process_multiple_posts(self, post_urls):
        results = []
        try:
            total = len(post_urls)
            for i, url in enumerate(post_urls, 1):
                print(f"Processing post {i}/{total}: {url}")
                result = self.get_post_description(url)
                results.append(result)
                time.sleep(1)  # Small delay between requests
        finally:
            self.close()
        return results

    def save_to_file(self, results, filename='instagram_posts.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)

    def close(self):
        self.driver.quit()

if __name__ == "__main__":
    # Example usage
    print("Choose an option:")
    print("1. Enter post URLs manually")
    print("2. Scrape posts from a profile")
    choice = input("Enter your choice (1 or 2): ")

    scraper = InstagramScraper()
    post_urls = []

    if choice == "1":
        print("Enter Instagram post URLs (one per line). Press Enter twice when done:")
        while True:
            url = input()
            if url == "":
                break
            post_urls.append(url)
    elif choice == "2":
        profile_url = input("Enter Instagram profile URL (e.g., https://www.instagram.com/username/): ")
        sheet_name = input("Enter name for Google Sheet (press Enter for automatic name): ").strip()
        if not sheet_name:
            sheet_name = None
        
        print("\nScraping post URLs from profile...")
        post_urls = scraper.get_profile_posts(profile_url)
        print(f"\nFound {len(post_urls)} posts")
    else:
        print("Invalid choice!")
        scraper.close()
        exit()

    if post_urls:
        print("\nProcessing posts...")
        results = scraper.process_multiple_posts(post_urls)
        
        # Save to both JSON and Google Sheets
        scraper.save_to_file(results)
        sheet_url = scraper.save_to_sheets(results, sheet_name)
        
        # Print results
        print("\nResults:")
        for result in results:
            print(f"\nURL: {result['url']}")
            if result['success']:
                print("Content:")
                print(result['content'])
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
        
        print(f"\nResults have been saved to:")
        print(f"1. JSON file: instagram_posts.json")
        if sheet_url:
            print(f"2. Google Sheet: {sheet_url}")
    else:
        print("No posts to process!") 