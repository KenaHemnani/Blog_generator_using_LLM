from langchain.document_loaders import DirectoryLoader
# from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.document_loaders import WebBaseLoader
from langchain.schema import Document
from operator import itemgetter
import json
import numpy as np
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the environment variables using os.getenv()

OpenAI_api_key = os.getenv("OPENAI_API_KEY")

class ImageRetriver():

    def __init__(self) -> None:
        self.embeddings = OpenAIEmbeddings(openai_api_key=OpenAI_api_key)

    def extract_captions_from_folder(self, folder_path):
        # Initialize an empty list to hold all captions
        all_captions = []
        all_img_urls = []
        # Loop through all files in the given folder
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            
            # Only process files that end with .json
            if filename.endswith('.json'):
                try:
                    # Open and load the JSON file
                    with open(file_path, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        
                        # Check if 'captions' key exists and is a list
                        if 'captions' in data and isinstance(data['captions'], list):
                            # Append the captions list to the all_captions list
                            all_captions.extend(data['captions'])

                        # Check if 'captions' key exists and is a list
                        if 'links' in data and isinstance(data['links'], list):
                            # Append the captions list to the all_captions list
                            all_img_urls.extend(data['links'])
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error processing file {filename}: {e}")
        
        return all_captions, all_img_urls
    
    def extract_json(self, json_file_path):
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        return data

    def retrive_images(self, search_result_folder, final_blog_folder):
        captions_list, image_urls = self.extract_captions_from_folder(search_result_folder)

        # Convert each string into a Document object
        documents = [Document(page_content=text) for text in captions_list]
        caption_vectors = self.embeddings.embed_documents([x.page_content for x in documents])

        blog_content = self.extract_json(f'{final_blog_folder}/final_blog.json')
        paragraphs = list(blog_content.values())
        titles = list(blog_content.keys())

        print(f"all captions: {len(documents)}")
        print(f"all captions: {len(caption_vectors)}")

        paragraphs = [Document(page_content=text) for text in paragraphs]

        # print(f"paragraph: {paragraph}")
        caption_vectors = np.array(caption_vectors)
        paragraph_embeddings = self.embeddings.embed_documents([x.page_content for x in paragraphs])

        all_para_top_5 = {}
        for idx, para_emb in enumerate(paragraph_embeddings):
            # Get the list of distances from that particular cluster center
            distances = np.linalg.norm(caption_vectors - para_emb, axis=1)
            sorted_indices = np.argsort(distances)
            top_5 = list(sorted_indices[:5])
            img_dict = {'image_urls' :  itemgetter(*top_5)(image_urls), 
                        'captions' :  itemgetter(*top_5)(captions_list)}
            all_para_top_5[titles[idx]] = img_dict

        with open(f'{final_blog_folder}/final_blog_images.json', 'w', encoding='utf-8') as f: 
            json.dump(all_para_top_5, f, ensure_ascii=False)
    
# # print(f"distances: {distances}")
# # print(f"sorted distances {distances[sorted_indices]}")
# print(all_para_top_5)

# with open('final_blog4/final_blog_images.json', 'w', encoding='utf-8') as f: 
#     json.dump(all_para_top_5, f, ensure_ascii=False)


# Test
if __name__ == "__main__":
    image_retriver = ImageRetriver()
    image_retriver.retrive_images('output1/search_results', 'output1/final_blog')