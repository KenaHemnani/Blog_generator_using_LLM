import streamlit as st
import os
import time
import streamlit as st
import urllib.parse
from src.writer import BlogWriter
from streamlit_frontend import display_blog

# Function to process the addition
def process_string(topic, content_type, folder_name):
     ans = f"""
              topic:{topic},
              content_type:{content_type},
              folder_name:{folder_name}
           """
     return ans

# Function to monitor the folder for new blog files
def get_latest_blog_files(folder_path):
    while True:
        blog_file = os.path.join(folder_path, "final_blog.json")
        images_file = os.path.join(folder_path, "final_blog_images.json")
        
        # Check if both files exist
        if os.path.exists(blog_file) and os.path.exists(images_file):
            return blog_file, images_file
        else:
            time.sleep(2)  # Wait for files to be generated


# Give Inputs
topic = st.sidebar.text_input("What topic do you want to write about?", "")
content_type = st.sidebar.selectbox("Select content type", ["news article", "educational blog", "travel blog"])
folder_name = st.sidebar.text_input("What you want to save temporary files locally, give folder name ?", "")

blog_writer = BlogWriter()

# Perform addition and create a link to the result page
if st.sidebar.button("Generate Content"):
    # Process the addition
    if topic and content_type and folder_name:
        with st.spinner("Generating blog... Please wait..."):
            # Generate blog content and save to JSON files
            blog_writer.call_writer(query=topic, 
                                    content_type=content_type,
                                    output_folder=folder_name)
            
            # Display message in the main area
            st.write(f"Blog '{topic}' is being generated... Please wait...")
        
            # Wait until both files are generated
            blog_folder = os.path.join(folder_name, 'final_blog')
            blog_file, images_file = get_latest_blog_files(blog_folder)  # Wait for the JSON files to be created

    
    # Create a URL with query parameters (for result display)
    query_params = urllib.parse.urlencode({'blog_file': blog_file, 'images_file': images_file})
    result_url = f"/?{query_params}"  # Use a relative URL for local use

    # Show the generated link in the sidebar
    st.sidebar.success("Click the link below to see generated blog:")
    st.sidebar.markdown(f"[View Generated Blog](http://localhost:8501{result_url})")

# Main content: Check for query parameters in the URL
query_params = st.query_params

# Conditional rendering based on the presence of query parameters
if 'blog_file' in query_params and 'images_file' in query_params:
    # Extract the result from the query parameter
    blog_path = query_params['blog_file']
    images_path = query_params['images_file']
    
    # Display the result
    st.header(f"{topic}")
    display_blog(blog_path, images_path)  # Display the blog with the paths
else:
    st.header("Create your own Content using AI !")
    st.write("Enter the details in sidebar to generate blog.")

# if __name__ == "__main__":
#     st.title("Write your content faster with AI ...")
#     blog_writer = BlogWriter()
#     main(blog_writer)