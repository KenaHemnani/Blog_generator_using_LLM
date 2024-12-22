# Loaders
from langchain.schema import Document

# Splitters
# from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter
# Model
from langchain_openai import ChatOpenAI

# Embedding Support
# from langchain.vectorstores import FAISS
# from langchain.embeddings import OpenAIEmbeddings
from langchain_community.embeddings import OpenAIEmbeddings
# Summarizer we'll use for Map Reduce
from langchain.chains.summarize import load_summarize_chain
from langchain_core.prompts import PromptTemplate

# Data Science
import numpy as np
from sklearn.cluster import KMeans
import os
import json
from langchain.chains import LLMChain

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the environment variables using os.getenv()

OpenAI_api_key = os.getenv("OPENAI_API_KEY")

class BlogGenerator():
    def __init__(self) -> None:
        self.llm1 = ChatOpenAI(model="gpt-4o",temperature=0, openai_api_key=OpenAI_api_key)
        self.llm2 = ChatOpenAI(temperature=0,
                 openai_api_key=OpenAI_api_key,
                 max_tokens=1000,
                 model='gpt-4o'
                )
        self.writer_llm = ChatOpenAI(model="gpt-4o", api_key = OpenAI_api_key, temperature=0)
        self.summary_chain = self.get_summary_chain()
        self.elaborator_chain = self.get_elaborator_chain()

    def fetch_and_concatenate_text_from_json_files(self, folder_path):
        final_text = ""  # Initialize an empty string to accumulate the text
        
        # Iterate through all files in the specified folder
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            
            # Check if the file is a JSON file
            if filename.endswith('.json'):
                try:
                    # Open and read the JSON file
                    with open(file_path, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        
                        # Check if 'text' key exists in the JSON
                        if 'text' in data:
                            final_text += data['text'] + "\n"  # Append the text with a newline for separation
                        else:
                            print(f"Warning: 'text' key not found in {filename}")
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
        
        return final_text
    
    def markdown_to_json(self, markdown_text):
        # Split the input markdown text by lines
        lines = markdown_text.split('\n')
        
        # Initialize an empty dictionary to store the JSON structure
        markdown_dict = {}
        
        # Variables to hold the current title (key) and content (value)
        current_title = ''
        current_content = []

        # Flag to handle the case where the first paragraph doesn't start with a heading
        first_heading_found = False

        # Process each line in the Markdown text
        for line in lines:
            # Check if the line is a main heading (e.g., # Heading)
            if line.startswith('# '):  # Main heading (level 1, i.e., starts with '# ')
                # If we already have content, save it under the current title
                if current_title or current_content:
                    markdown_dict[current_title] = '\n'.join(current_content)
                
                # Set the new title and reset content for the next section
                current_title = line[2:].strip()  # Remove the '# ' and strip whitespace
                current_content = []
                first_heading_found = True
            
            # If it's not a main heading, but content under the current title
            elif first_heading_found or current_title == '':  # Only collect content if we've encountered a heading or the first block is before any heading
                current_content.append(line.strip())

        # After processing all lines, save the last title-content pair to the dictionary
        if current_title or current_content:
            markdown_dict[current_title] = '\n'.join(current_content)

        return markdown_dict

    def get_summary_chain(self):
        map_prompt = """
        You will be given a single passage of some topic or blog. This section will be enclosed in triple backticks (```)
        Your goal is to give a summary of this section so that a reader will have a full understanding of the topic and 
        give a appropriate title to the summary as well.
        Your response should be at least three paragraphs and fully encompass what was said in the passage.

        ```{text}```
        FULL SUMMARY:
        """
        map_prompt_template = PromptTemplate(template=map_prompt, input_variables=["text"])

        map_chain = load_summarize_chain(llm=self.llm2,
                                         chain_type="stuff",
                                         prompt=map_prompt_template)
        
        return map_chain
    
    def get_elaborator_chain(self):
        # prompt2 = """
        #         You are a professional writer who is proficient in writing {type_of_content}, below given is the 
        #         various title and short summary which has to be included in article.
        #         Your task is to eloborate and expand this summary into a {type_of_content}.

        #         Instruction : structure the article in a good flow into sections and sub-sections whenever necessary to cover this content and can change the title of sections 
        #         accordingly or also may avoid giving title to few. Also you have to expand this brief summaries. Ensure that the summary is consistent 
        #         and fits into the synopsis of the whole {type_of_content}.
        #         Write the first paragraph eye-catchy and use attractive language to read. 
        #         Avoid giving titles to first parapgraph.
        #         Avoid giving confidential statements.
        #         ```{text}```
        #         FULL SUMMARY:
        # """

        prompt21 = """
                You are a professional writer who is proficient in writing {type_of_content}, 
                You will be given various titles and corresponding short summary which has to be included in article.
                Your task is to eloborate and expand this summary into a {type_of_content}.
                All summaries with titles together will be enclosed in triple backticks (```). 
                Instruction : structure the article in a good flow into sections and sub-sections whenever necessary to cover this content and can change the title of sections 
                accordingly or also may avoid giving title to few. Also you have to expand this brief summaries. Ensure that the summary is consistent 
                and fits into the synopsis of the whole {type_of_content}.
                Avoid giving titles to first parapgraph.
                Write the first paragraph eye-catchy and use attractive language to read. 
                Please generate the article in Markdown format. Use appropriate headers wherever 
                there is section. Avoid placing markdowns in sub-sections.
                Avoid giving confidential statements.
                The total lenght of final article should be atleast double of following input:
                ```{text}```
                FULL SUMMARY:
        """
        prompt_template = PromptTemplate(template=prompt21, input_variables=["text", "type_of_content"])

        writer_chain = LLMChain(llm=self.writer_llm,
                        prompt=prompt_template)

        return writer_chain

    def cluster_similar_topic_texts(self, final_text):
        # all 5 texts
        print(f"The fetched data from web has {self.llm1.get_num_tokens(final_text)} tokens")

        # Split entire text into chunks/docs
        text_splitter = RecursiveCharacterTextSplitter(separators=["\n\n", "\n", "\t"], chunk_size=10000, chunk_overlap=3000)
        docs = text_splitter.create_documents([final_text])
        num_documents = len(docs)
        print (f"Now our text is split up into {num_documents} documents")

        # Get docs embedding and cluster them
        embeddings = OpenAIEmbeddings(openai_api_key=OpenAI_api_key)
        vectors = embeddings.embed_documents([x.page_content for x in docs])
        num_clusters = 5
        # Perform K-means clustering
        kmeans = KMeans(n_clusters=num_clusters, random_state=42).fit(vectors)

        vectors = np.array(vectors)  # Convert the list of vectors to a NumPy array

        # Find the closest embeddings to the centroids-docs

        # Create an empty list that will hold your closest points
        closest_indices = []

        # Loop through the number of clusters you have
        for i in range(num_clusters):
            
            # Get the list of distances from that particular cluster center
            distances = np.linalg.norm(vectors - kmeans.cluster_centers_[i], axis=1)
            
            # Find the list position of the closest one (using argmin to find the smallest distance)
            closest_index = np.argmin(distances)
            
            # Append that position to your closest indices list
            closest_indices.append(closest_index)

        selected_indices = sorted(closest_indices)

        selected_docs = [docs[doc] for doc in selected_indices]

        return selected_docs
    
    def generate_bullet_point_summary(self, selected_docs):
        # Make an empty list to hold your summaries
        summary_list = []

        # Loop through a range of the lenght of your selected docs
        # summary_text = ''
        for i, doc in enumerate(selected_docs):
            
            # Go get a summary of the chunk
            chunk_summary = self.summary_chain.run([doc])
            
            # Append that summary to your list
            summary_list.append(chunk_summary)
            
            # print (f"Summary #{i} (chunk #{selected_indices[i]}) \n - Preview: {chunk_summary[:250]} \n")
            # summary_text += f"Summary #{i} (chunk #{selected_indices[i]}) \n - Preview: {chunk_summary} \n"

        summaries = "\n".join(summary_list)
        # print(f"Summary is as shown : \n {summaries}")
        # Convert it back to a document
        # Save the string to a .txt file
        with open("summaries_clustering.txt", "w", encoding="utf-8") as file:
            file.write(summaries)

    def generate_bullet_point_summary(self, selected_docs):
        # Initialize an empty dictionary to hold summaries with their corresponding chunk number
        summary_dict = {}

        # Loop through the selected documents
        for i, doc in enumerate(selected_docs):
            # Generate the summary for the current document chunk
            chunk_summary = self.summary_chain.run([doc])

            # Add the summary to the dictionary, using the chunk index as the key
            summary_dict[f"chunk_{i+1}"] = chunk_summary

        return summary_dict
    
    def elaborate_summary(self, summary_dict, type_of_content):  
         
        final_summary = ""

        # Loop through each value (which should be a string) in the dictionary
        for _, summary in summary_dict.items():
            # Append each summary to the final summary string
            final_summary += summary + "\n\n"
            
        # print(f"final summary :{final_summary}")
        print(f"final summary has {self.writer_llm.get_num_tokens(final_summary)} tokens")
        response = self.elaborator_chain.invoke({"text": final_summary, "type_of_content": type_of_content})
        print(f"final article has {self.writer_llm.get_num_tokens(response['text'])} tokens")
        return response['text']
        
    def write_blog(self, type_of_content, input_path, output_path):
        final_text = self.fetch_and_concatenate_text_from_json_files(input_path)
        selected_docs = self.cluster_similar_topic_texts(final_text)
        summary_dict = self.generate_bullet_point_summary(selected_docs)
        # type_of_content = 'news article'
        final_blog = self.elaborate_summary(summary_dict, type_of_content)
        blog_dict = self.markdown_to_json(final_blog)
        # blog_folder = 'final_blog2'
        if not os.path.exists(output_path):
            os.makedirs(output_path) 
        # Convert the summary dictionary to a JSON format and save it to a file
        summary_path = os.path.join(output_path, "topics_summaries.json")
        with open(summary_path, "w", encoding="utf-8") as json_file:
            json.dump(summary_dict, json_file, ensure_ascii=False, indent=4)

        blog_path = os.path.join(output_path, "final_blog.json")
        with open(blog_path, "w", encoding="utf-8") as file:  # Open file in write mode
            json.dump(blog_dict, file, ensure_ascii=False, indent=4)
        print(f"final blog written at {blog_path}")
        
# Test
if __name__ == "__main__":
    blog_writer = BlogGenerator()
    blog_writer.write_blog('news_article', 'output5/search_results', 'output5/final_blog')