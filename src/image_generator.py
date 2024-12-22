from langchain.chains import LLMChain
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI
from langchain.agents import initialize_agent, load_tools
import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the environment variables using os.getenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

class ImageGenerator():
    def __init__(self):
        self.llm = OpenAI(temperature=0.9)
        self.prompt = PromptTemplate(
        input_variables=["image_desc", "image_type"],
        template="Generate a detailed prompt within 30 words to generate an image based on the following description: {image_desc}. Use content from web to find meaninful description to generate and image of {image_type} style",
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt, verbose=False)
    
    def generate_image(self, caption, style):
        input_cap = {"image_desc": caption, "image_type": style}
        image_url = None  # Initialize the variable to avoid uninitialized error
        try:
            # Attempt to generate the image using the DallEAPIWrapper
            image_url = DallEAPIWrapper().run(self.chain.run(input_cap))
        except Exception as e:
            # Catch any other exception and display a generic message
            st.error("An unexpected error occurred while generating the image.")  # Custom message
            # Log the exception (optional, for debugging purposes)
            # print(f"Exception: {str(e)}")
        
        return image_url

# Test
if __name__ == "__main__":
    image_generator = ImageGenerator()
    # url = image_generator.generate_image('A halloween night at a haunted museum', 'realistic')
    url = image_generator.generate_image('A halloween night at a haunted museum with a house and Scooby-doo caracters', 'cartoonist')
    print(f"Find image here : {url}")
