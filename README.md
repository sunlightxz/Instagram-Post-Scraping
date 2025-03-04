# Instagram Post Scraper

A Python script to scrape post descriptions from Instagram posts and save them to both JSON and Google Sheets.

## Features

- Scrape descriptions from individual posts or entire profiles
- Login support with email verification handling
- Save results to both JSON file and Google Sheets
- Support for both posts and reels
- Progress tracking and error handling
- Rate limiting protection with human-like delays

## Prerequisites

1. Python 3.6 or higher
2. Chrome browser installed
3. Google account for Google Sheets integration

## Installation

1. Clone this repository or download the files:
```bash
git clone <repository-url>
cd instagram-scraper
```

2. Install required packages:
```bash
pip install selenium gspread oauth2client
```

3. Install ChromeDriver:
   - Download ChromeDriver from: https://sites.google.com/chromium.org/driver/
   - Make sure it matches your Chrome browser version
   - Add it to your system PATH or place it in the script directory

4. Set up Google Sheets API:
   - Go to Google Cloud Console (https://console.cloud.google.com/)
   - Create a new project
   - Enable Google Sheets API and Google Drive API
   - Create credentials (Service Account Key)
   - Download the JSON key file
   - Rename it to `credentials.json` and place it in the script directory
   - Share your Google Sheet with the service account email from credentials.json

## Configuration

1. Create a Google Sheet and copy its ID from the URL:
   - Example URL: `https://docs.google.com/spreadsheets/d/1yxVXUAneiISJmO5I1ow574cJYxBOo5VVYg-WHApTDOY/edit`
   - The ID is: `1yxVXUAneiISJmO5I1ow574cJYxBOo5VVYg-WHApTDOY`

2. Update the `SPREADSHEET_ID` in the script with your sheet's ID.

## Usage

Run the script:
```bash
python instagram_scraper.py
```

Choose from two options:

1. **Manual URL Entry**:
   - Enter Instagram post URLs one per line
   - Press Enter twice when done

2. **Profile Scraping**:
   - Enter your Instagram credentials
   - Enter the profile URL you want to scrape
   - Optionally provide a name for the Google Sheet worksheet
   - Handle email verification if required

## Output

The script saves results in two formats:

1. **JSON File** (`instagram_posts.json`):
```json
[
    {
        "url": "https://www.instagram.com/p/post-id/",
        "content": "Post description text",
        "success": true
    }
]
```

2. **Google Sheet** with columns:
   - Post URL
   - Content
   - Success
   - Error
   - Timestamp

## Notes

- Instagram may require login for accessing some profiles
- The script includes delays to avoid rate limiting
- Some posts might require authentication to view
- Instagram's HTML structure changes frequently; the script may need updates
- Respect Instagram's terms of service and rate limits

## Troubleshooting

1. **ChromeDriver Error**:
   - Make sure ChromeDriver version matches your Chrome browser
   - Ensure ChromeDriver is in your PATH

2. **Google Sheets Error**:
   - Verify credentials.json is properly configured
   - Make sure the sheet is shared with the service account email

3. **Login Issues**:
   - Check your credentials
   - Handle verification codes when prompted
   - Wait for the full login process to complete

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.