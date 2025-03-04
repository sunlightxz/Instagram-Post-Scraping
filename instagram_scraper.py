from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
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
            # Open existing spreadsheet by its ID
            SPREADSHEET_ID = '1yxVXUAneiISJmO5I1ow574cJYxBOo5VVYg-WHApTDOY'  # Replace with your spreadsheet ID
            spreadsheet = self.gs.open_by_key(SPREADSHEET_ID)
            
            # Create new worksheet with timestamp if no name provided
            if sheet_name is None:
                sheet_name = f"Scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Add new worksheet
            worksheet = spreadsheet.add_worksheet(sheet_name, 1000, 20)
            
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

            print(f"\nData saved to worksheet: {sheet_name}")
            print(f"Spreadsheet URL: {spreadsheet.url}")
            return spreadsheet.url

        except Exception as e:
            print(f"Error saving to Google Sheets: {e}")
            return None

    def login(self, username, password):
        try:
            # Go to Instagram login page
            self.driver.get('https://www.instagram.com/accounts/login/')
            time.sleep(3)  # Wait for page to load

            # Enter username
            username_input = self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
            username_input.send_keys(username)

            # Enter password
            password_input = self.wait.until(EC.presence_of_element_located((By.NAME, "password")))
            password_input.send_keys(password)
            password_input.send_keys(Keys.RETURN)

            print("\nChecking if verification is needed...")
            time.sleep(8)  # Wait longer to check for verification
            
            # Check if verification code is needed
            max_verification_wait = 300  # 5 minutes max wait for code
            start_time = time.time()
            
            while time.time() - start_time < max_verification_wait:
                if "Enter the code we sent to" in self.driver.page_source:
                    print("\nVerification code required!")
                    print("Please check your email and enter the code below.")
                    print("Waiting for you to enter the code (you have 5 minutes)...")
                    verification_code = input("\nEnter the verification code: ").strip()
                    
                    # Find and fill the verification code input
                    try:
                        code_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='verificationCode']")))
                        code_input.send_keys(verification_code)
                        code_input.send_keys(Keys.RETURN)
                        print("\nVerification code submitted, checking...")
                        time.sleep(8)  # Wait for verification to complete
                        break
                    except Exception as e:
                        print(f"\nError entering verification code: {e}")
                        print("Please try entering the code again.")
                        continue
                
                # Check if we're already logged in
                try:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "svg[aria-label='Home']")))
                    print("Login successful!")
                    return True
                except:
                    time.sleep(2)  # Wait before checking again
            
            # Final login check
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "svg[aria-label='Home']")))
                print("Login successful!")
                return True
            except:
                print("Login failed!")
                return False

        except Exception as e:
            print(f"Error during login: {e}")
            return False

    def get_profile_posts(self, profile_url):
        try:
            self.driver.get(profile_url)
            time.sleep(3)  # Wait for initial load
            
            # Handle "Log in" popup if it appears
            try:
                not_now_button = self.driver.find_element(By.CSS_SELECTOR, "button._a9--._a9_1")
                not_now_button.click()
                time.sleep(1)
            except:
                pass
                
            post_urls = set()  # Using set to avoid duplicates
            consecutive_same_count = 0
            scroll_attempts = 0
            max_attempts = 50  # Maximum number of scroll attempts
            
            while scroll_attempts < max_attempts:
                # Get current post count
                old_count = len(post_urls)
                
                # Get both post and reel links
                links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/'], a[href*='/reel/']")
                for link in links:
                    post_urls.add(link.get_attribute('href'))
                
                # Check if we found new posts
                new_count = len(post_urls)
                if new_count > old_count:
                    consecutive_same_count = 0
                    print(f"Found {new_count} posts and reels so far...")
                else:
                    consecutive_same_count += 1
                    print(f"No new posts found in scroll {consecutive_same_count}/3...")
                
                # If we haven't found new posts in 3 consecutive scrolls, stop
                if consecutive_same_count >= 3:
                    print("No new posts found after 3 scrolls, finishing...")
                    break
                
                # Scroll down
                self.driver.execute_script("""
                    window.scrollTo(0, document.body.scrollHeight);
                    """)
                
                # Random delay between 2-4 seconds to seem more human-like
                time.sleep(4)
                scroll_attempts += 1
            
            print(f"Final count: {len(post_urls)} posts and reels")
            return list(post_urls)
            
        except Exception as e:
            print(f"Error getting profile content: {e}")
            return []

    def get_post_description(self, post_url):
        try:
            self.driver.get(post_url)
            time.sleep(2)  # Wait for page to load
            
            # Only get the main description with the specific classes
            elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "._ap3a._aaco._aacu._aacx._aad7._aade"
            )
            
            # Get only the first element's text (main description)
            description = elements[0].text.strip() if elements else None
            
            return {
                'url': post_url,
                'content': description,
                'success': True if description else False
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
    print("Choose an option:")
    print("1. Enter post URLs manually")
    print("2. Scrape posts from a profile")
    choice = input("Enter your choice (1 or 2): ")

    scraper = InstagramScraper()
    post_urls = []

    if choice == "2":
        # Get login credentials
        username = input("Enter Instagram username: ")
        password = input("Enter Instagram password: ")
        
        # Attempt login
        if not scraper.login(username, password):
            print("Failed to login. Exiting...")
            scraper.close()
            exit()
            
        profile_url = input("Enter Instagram profile URL (e.g., https://www.instagram.com/username/): ")
        sheet_name = input("Enter name for Google Sheet (press Enter for automatic name): ").strip()
        if not sheet_name:
            sheet_name = None
        
        print("\nScraping post URLs from profile...")
        post_urls = scraper.get_profile_posts(profile_url)
        print(f"\nFound {len(post_urls)} posts")
    elif choice == "1":
        print("Enter Instagram post URLs (one per line). Press Enter twice when done:")
        while True:
            url = input()
            if url == "":
                break
            post_urls.append(url)
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