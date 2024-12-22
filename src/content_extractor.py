import os
import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
import html2text
import pandas as pd
import re
import json
from urllib.parse import urlparse
from .caption_generator import ImageCaptionGenerator
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access the environment variables using os.getenv()
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

# Custom subclass of HTML2Text to handle <a> tags differently
class CustomHTML2Text(html2text.HTML2Text):
    def handle_a(self, t, attrs):
        self.out(" [{}] ".format(attrs["href"]))  # Override the anchor tag handler

class WebContentExtractor:
    def __init__(self):
        # self.url = url
        # self.output_file = output_file
        self.config = self._initialize_html2text_config()

    # Function to perform Google search using SerpApi
    def get_top_5_search_results(self, query):
        params = {
            "q": query,
            "api_key": SERPAPI_API_KEY,
            "engine": "google"
        }
        search = GoogleSearch(params)
        results = search.get_dict()

        # Extract URLs from the search results
        urls = []
        for result in results.get('organic_results', [])[:5]:  # Get top 5 organic results
            url = result.get('link')
            if url:
                urls.append(url)
        return urls

    def _initialize_html2text_config(self):
        # Initialize and configure the custom HTML2Text object
        config = CustomHTML2Text()
        config.body_width = 0  # Disable line wrapping
        config.wrap_links = True
        config.wrap_lists = True
        config.ignore_links = True  # Ignore links (don't convert them to Markdown)
        return config

    def fetch_html_content(self, url):
        # Send a GET request to the URL
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup.encode().decode()  # Return HTML content as a string
        else:
            raise Exception(f"Failed to retrieve content from {url}. Status code: {response.status_code}")

    def convert_html_to_text(self, html_content):
        # Convert the HTML content to text using the configured HTML2Text object
        return self.config.handle(html_content)

    def save_to_file(self, text_content, txt_file):
        # Write the extracted text to a file
        with open(txt_file, "w", encoding="utf-8") as file:
            file.write(text_content)

    def extract_and_save_content(self, url, txt_file):
        # Orchestrate the process: fetch, convert, and save
        try:
            html_content = self.fetch_html_content(url)
            text_content = self.convert_html_to_text(html_content)
            self.save_to_file(text_content, txt_file)
            print(f"Content successfully saved to {txt_file}")
            return True
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def extract_links_from_text(self, file_path):
        # Define regex pattern to match ![attribute](link), without restricting to http/https
        pattern = r'!\[([^\]]*)\]\(([^)]+)\)'  # Capture any string inside ()
        
        # Read the content from the text file
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()

        # Find all matches for the pattern
        matches = re.findall(pattern, text)

        # Convert the list of matches into a pandas DataFrame
        # Each match returns a tuple (attribute, link)
        df = pd.DataFrame(matches, columns=['text', 'link'])

        return df
    
    def save_df_to_excel(self, df, output_file):
        # Save the DataFrame to an Excel file
        df.to_excel(output_file, index=False, engine='openpyxl')  # `index=False` avoids writing row numbers
        print(f"Data successfully saved to {output_file}")

    def extract_links_from_text_as_json(self, file_path, output_json_file):
        # Define regex pattern to match ![attribute](link), without restricting to http/https
        pattern = r'!\[([^\]]*)\]\(([^)]+)\)'  # Capture any string inside ()
        
        # Read the content from the text file
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()

        # Find all matches for the pattern
        matches = re.findall(pattern, text)
        
        # Initialize an empty list to store valid links
        valid_links = []
        raw_links_for_valid = []
        # Iterate over all matches to process and validate the links
        for match in matches:
            link = match[1]
            raw_link = link[:] # save a copy of link
            # Prepend 'https://' if the link doesn't already have a valid scheme
            if not urlparse(link).scheme:
                link = 'https:' + link
            
            # Validate the URL by checking if it's reachable and an image
            try:
                # Attempt a HEAD request to check if the link is valid (without downloading the content)
                response = requests.head(link, allow_redirects=True, timeout=5)
                
                # Check if the response status code indicates a successful request (2xx status)
                if response.status_code >= 200 and response.status_code < 300:
                    # Check if the Content-Type header indicates an image
                    if 'image' in response.headers.get('Content-Type', '').lower():
                        valid_links.append(link)
                        raw_links_for_valid.append(raw_link)
            except requests.exceptions.RequestException as e:
                # If the link is not valid or there's an error, print the error and move on
                print(f"Invalid link: {link} ({e})")

        # Create the dictionary with text and valid links
        result = {
            "text": text,  # Entire text from the file
            "raw_links": raw_links_for_valid,
            "links": valid_links  # List of valid image links
        }

        # Save the result to a JSON file
        with open(output_json_file, 'w', encoding='utf-8') as json_file:
            json.dump(result, json_file, ensure_ascii=False, indent=4)

        print(f"Data successfully saved to {output_json_file}")

    def find_image_link_string(self, text, raw_link):
        # Escape raw_link to ensure special characters are treated literally in the regex
        escaped_raw_link = re.escape(raw_link)
        
        # Define the regex pattern: ![any text](raw_link)
        pattern = r'!\[([^\]]*)\]\(' + escaped_raw_link + r'\)'
        
        # Find all matches of the pattern in the text
        matches = re.findall(pattern, text)
        # Reconstruct the full pattern and return it
        full_matches = [f'![{match}]{raw_link}' for match in matches]
        
        # Return the list of matches (captions in the [] part)
        return full_matches[0]

    def rewrite_text(self, input_json_path, output_json_path):
        
        # Read the input JSON file
        with open(input_json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Check if required keys exist in the input data
        if 'text' not in data or 'raw_links' not in data or 'captions' not in data or 'links' not in data:
            print("Missing required keys in input JSON.")
            return

        # Extract text, raw_links, captions, and links from the input data
        text = data['text']
        raw_links = data['raw_links']
        captions = data['captions']
        links = data['links']

        # Step 1: Replace raw_link instances with captions in the format 'Paste image with caption: {caption}'
        for raw_link, caption in zip(raw_links, captions):
            # Create a regex pattern to find !()[raw_link]
            # f'!\[([^\]]*)\]\({raw_link})\)'
            # Escape raw_link to avoid special characters interfering with regex
            escaped_raw_link = re.escape(raw_link)
            pattern = r'!\[([^\]]*)\]\(' + escaped_raw_link + r'\)'
            replacement = f""" 
                            \n 
                            ********** Paste image with caption ********** : \n {caption} \n 
                            ------\n
                                """
            
            # Replace the pattern in the text
            text = re.sub(pattern, replacement, text)

        # Step 2: Remove all other image links of the form !()[link]
        for link in links:
            # Create a regex pattern to find !()[link]
            pattern = re.escape(f'!()[{link}]')
            
            # Remove the pattern from the text
            text = re.sub(pattern, '', text)

        # Step 3: Prepare the updated data
        updated_data = {
            "text": text,
            "raw_links": raw_links,  # Keep raw_links unchanged
            "links": links,          # Keep links unchanged
            "captions": captions     # Keep captions unchanged
        }

        # Step 4: Save the updated JSON to the output file
        with open(output_json_path, 'w', encoding='utf-8') as output_file:
            json.dump(updated_data, output_file, ensure_ascii=False, indent=4)
        
        print(f"Processed JSON with updated text saved to {output_json_path}")

    def extract_json(self, url, caption_generator, txt_file, json_file):
        status = self.extract_and_save_content(url, txt_file)
        if status:
            self.extract_links_from_text_as_json(txt_file, json_file)
            caption_generator.add_captions_to_json(json_file, json_file)
            self.rewrite_text(json_file, json_file)

    def make_dirs(self, txt_folder, json_folder):
        if not os.path.exists(json_folder):
            os.makedirs(json_folder)
        if not os.path.exists(txt_folder):
            os.makedirs(txt_folder)  
        
    def extract_content(self, query, temp_folder, json_folder):
        # txt_folder = 'temp1'
        # json_folder = 'search_results1'
        self.make_dirs(temp_folder, json_folder)
        caption_generator = ImageCaptionGenerator()

        # Get top 5 search results using SerpApi
        urls = self.get_top_5_search_results(query)

        for idx, url in enumerate(urls, start=1):
            print(f"Processing {url}...")

            # Fetch and process content
            txt_file = os.path.join(temp_folder, f"text_{idx}.txt")
            json_file = os.path.join(json_folder, f"json_{idx}.json")
            self.extract_json(url, caption_generator, txt_file, json_file)


# Test
if __name__ == "__main__":
    content_extractor = WebContentExtractor()
    query = input("Enter Topic: ")
    out_folder = input("Enter Folder name to save results: ")
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)
    
    temp_folder = os.path.join(out_folder, 'temp')
    search_results = os.path.join(out_folder, 'search_results')
    content_extractor.extract_content(query, temp_folder, search_results)