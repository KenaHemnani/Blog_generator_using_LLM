from .content_extractor import WebContentExtractor
from .blog_generator import BlogGenerator
from .image_retriver import ImageRetriver
import os

class BlogWriter():
    def __init__(self) -> None:
        self.content_extractor = WebContentExtractor()
        self.blog_generator = BlogGenerator()
        self.image_retriver = ImageRetriver()
    

    def write_blog(self, query, content_type,temp_folder, search_result_folder, final_blog_folder):
        self.content_extractor.extract_content(query, temp_folder, search_result_folder)
        self.blog_generator.write_blog(type_of_content=content_type,
                                       input_path=search_result_folder, 
                                       output_path=final_blog_folder)
        self.image_retriver.retrive_images(search_result_folder, final_blog_folder)

    def call_writer(self, query, content_type, output_folder):
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        temp_folder = os.path.join(output_folder, 'temp')
        search_result_folder = os.path.join(output_folder, 'search_results')
        final_blog_folder = os.path.join(output_folder, 'final_blog')
        self.write_blog(query=query, 
                        content_type=content_type,
                        temp_folder=temp_folder, 
                        search_result_folder=search_result_folder, 
                        final_blog_folder=final_blog_folder)
# Test
if __name__ == "__main__":
    blog_writer = BlogWriter()
    query = input("Enter Topic: ")
    content_type =  input("Enter Content Type: ")
    out_folder =  input("Folder in which results are saved: ")

    blog_writer.write_blog(query=query, 
                           content_type=content_type,
                           temp_folder=os.path.join(out_folder, 'temp'), 
                           search_result_folder=os.path.join(out_folder, 'search_results'),
                           final_blog_folder=os.path.join(out_folder, 'final_blog'))