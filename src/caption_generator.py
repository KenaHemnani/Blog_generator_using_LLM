import os
import json
import requests
from io import BytesIO
from langchain_core.messages import HumanMessage
import openai
import base64
import httpx
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the environment variables using os.getenv()

OpenAI_api_key = os.getenv("OPENAI_API_KEY")

class ImageCaptionGenerator:
    def __init__(self, api_key=OpenAI_api_key):
        self.model = ChatOpenAI(model="gpt-4o", temperature=0, api_key=api_key)

    def generate_caption_for_image(self, image_url):
        """
        Generates a caption for the provided image URL by encoding it to base64
        and passing it to the GPT-4 model.
        """
        try:
            # Encode the image to base64
            image_data = base64.b64encode(httpx.get(image_url).content).decode("utf-8")
            
            # Construct the message for the model
            message = HumanMessage(
                content=[
                    {
                        "type": "text", 
                        "text": """
                            You are a Professional Image Explainer.
                            You have to use the available data on the internet to perform the task.
                            Your task is to write a brief caption of up to 30 words for this image.
                        """
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                    },
                ]
            )
            
            # Invoke the model and get the response
            response = self.model.invoke([message])
            return response.content

        except Exception as e:
            print(f"Error generating caption for image {image_url}: {e}")
            return None

    def add_captions_to_json(self, input_json_path, output_json_path):
        """
        Process the input JSON file, generate captions for each image, and save the results to an output JSON file.
        """
        try:
            # Load the input JSON data
            with open(input_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if 'links' key exists in the data
            if 'links' not in data:
                print("No 'links' key found in the input JSON.")
                return

            captions = []
            
            # Process each image URL in the 'links' list
            for idx, image_url in enumerate(data['links']):
                print(f"Processing image {idx + 1}: {image_url}")
                
                # Generate caption for the image
                caption = self.generate_caption_for_image(image_url)
                
                if caption:
                    captions.append(caption)
                else:
                    captions.append('')

            # Append the generated captions to the original JSON data
            data['captions'] = captions

            # Save the updated data to the output JSON file
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            
            print(f"Processed JSON with captions saved to {output_json_path}")
        
        except Exception as e:
            print(f"Error processing the JSON file: {e}")