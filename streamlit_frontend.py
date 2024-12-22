from src import ImageGenerator
import streamlit as st
import json
import urllib.request
import os

image_generator = ImageGenerator()

def extract_json(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    return data

def transform_image_dict(input_dict):
    # Create a new dictionary to store the transformed structure
    transformed_dict = {}
    
    # Iterate over each key-value pair in the input dictionary
    for title, content in input_dict.items():
        img_caps_list = []
        captions = content['captions']
        urls = content['image_urls']
        for i in range(len(captions)):
            img_caps_list.append({'caption': captions[i],
                                  'url': urls[i]})

        
        # Add the transformed dictionary to the result
        transformed_dict[title] = img_caps_list
    
    return transformed_dict

# Cache the image options to avoid re-fetching
@st.cache_data
def get_image_options(paragraph_title, images_for_paragraphs):
    # Example image URLs (you can replace with actual data)
    image_options = images_for_paragraphs.get(paragraph_title, {})
    return image_options

def display_text_with_images(paragraphs, images_for_paragraphs):
# Main function to handle the UI and image selection
# def main():
    # st.title("Blog Paragraphs with Image Selection")

    # Initialize session state for tracking selected and confirmed images
    if 'selected_images' not in st.session_state:
        st.session_state.selected_images = {}
    if 'confirmed' not in st.session_state:
        st.session_state.confirmed = {}
    if 'generated_images' not in st.session_state:
        st.session_state.generated_images = {}

    # Sidebar: Show "Select a paragraph" message first
    st.sidebar.write("Select a paragraph from the dropdown to modify its image.")

    # Sidebar: Select which paragraph to modify images for
    selected_paragraph = st.sidebar.selectbox("Select a Paragraph to Add Image", list(paragraphs.keys()))

    # Display both paragraphs in the main screen
    for paragraph_title, paragraph_text in paragraphs.items():
        st.write(f"**{paragraph_title}**")
        st.write(paragraph_text)
        
        # If the image for this paragraph is confirmed, show the image under the paragraph
        if paragraph_title in st.session_state.selected_images:
            image_data = st.session_state.selected_images[paragraph_title]
            if image_data["url"]:
                # st.image(image_data['url'], caption=image_data['caption'], 
                st.image(image_data['url'], caption=f"Image: {image_data['caption']} \n Source:{image_data['url']}", 
                use_container_width=True)
        
        elif paragraph_title not in st.session_state.confirmed or not st.session_state.confirmed[paragraph_title]:
            # Display a message prompting the user to select an image for this paragraph if not confirmed yet
            if selected_paragraph == paragraph_title:
                # st.markdown("<p style='color: green;'>Select an image here</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='color: green;'>Select an image here for </p><p style='color: red;'>{paragraph_title}</p>", unsafe_allow_html=True)

                # st.markdown(f"<p style='color: green; font-size: 20px;'>Select an image here for {paragraph_title} </p>", unsafe_allow_html=True)


        # Only show image options for the selected paragraph in the sidebar
        if selected_paragraph == paragraph_title:
            image_options = get_image_options(paragraph_title, images_for_paragraphs)
            image_option = st.sidebar.radio(f"Select Image Source for {paragraph_title}",
                                           ["Suggested images from Web", "AI Generated", "Upload my Image", "No Image"],
                                           key=f"image_source_radio-{paragraph_title}")

            # Process based on image source selection
            if image_option == "Suggested images from Web":
                st.sidebar.subheader(f"Select an image for {paragraph_title} from Web")

                # Cache the image options once and use them throughout the session
                
                print(f'---> image_options : {image_options}')
                captions = [option["caption"] for option in image_options]
                selected_caption = st.sidebar.selectbox(f"Select an image for {paragraph_title}", captions)

                # Find the selected image URL
                selected_image = next(item for item in image_options if item["caption"] == selected_caption)
                selected_image_url = selected_image["url"]

                # Temporarily show the selected image in the sidebar
                st.sidebar.image(selected_image_url, caption=selected_caption, use_container_width=True)

            elif image_option == "AI Generated":
                st.sidebar.subheader(f"Generate AI Image for {paragraph_title}")

                # Predefined AI captions (for simulation)
                ai_captions = [option["caption"] for option in image_options]
                caption_choice = st.sidebar.selectbox(f"Select a caption for {paragraph_title}", ai_captions)
                style_choice = st.sidebar.selectbox("Select a style for AI-generated image", ['realistic', 'synthetic', 'cartoonist'])

                # Display the "Generate" button after caption and style are chosen
                generate_button = st.sidebar.button(f"Generate AI Image for {paragraph_title}")

                if generate_button and caption_choice and style_choice:
                    # Show spinner while generating AI image
                    with st.spinner('Generating image...'):
                        ai_image_url = image_generator.generate_image(caption_choice, style_choice)

                        # Store the generated image for later confirmation
                        st.session_state.generated_images[paragraph_title] = {
                            "url": ai_image_url,
                            "caption": f"AI Generated: {caption_choice} ({style_choice})"
                        }

                        # Temporarily show the generated AI image in the sidebar
                        st.sidebar.image(ai_image_url, caption=f"AI Generated: {caption_choice} ({style_choice})", use_container_width=True)

            elif image_option == "Upload my Image":
                uploaded_image = st.sidebar.file_uploader(f"Upload an image for {paragraph_title}", type=["jpg", "jpeg", "png"])

                if uploaded_image:
                    st.sidebar.image(uploaded_image, caption="Uploaded Image", use_container_width=True)

            elif image_option == "No Image":
                st.sidebar.write("No image selected.")

            # Confirm the selected image
            confirm_button = st.sidebar.button(f"Confirm Image for {paragraph_title}", key=f"confirm_button-{paragraph_title}")
            if confirm_button:
                # Store the selected image details in session state
                if image_option == "Suggested images from Web" and selected_caption:
                    st.session_state.selected_images[paragraph_title] = {
                        "url": selected_image_url,
                        "caption": selected_caption
                    }

                elif image_option == "AI Generated" and paragraph_title in st.session_state.generated_images:
                    ai_image_url = st.session_state.generated_images[paragraph_title]["url"]
                    caption = st.session_state.generated_images[paragraph_title]["caption"]
                    st.session_state.selected_images[paragraph_title] = {
                        "url": ai_image_url,
                        "caption": caption
                    }

                elif image_option == "Upload my Image" and uploaded_image:
                    st.session_state.selected_images[paragraph_title] = {
                        "url": uploaded_image,
                        "caption": "Uploaded Image"
                    }

                elif image_option == "No Image":
                    st.session_state.selected_images[paragraph_title] = {
                        "url": None,
                        "caption": "No Image"
                    }

                # Once confirmed, mark as confirmed and stop showing selection options
                st.session_state.confirmed[paragraph_title] = True
                st.sidebar.write(f"Image successfully confirmed for {paragraph_title}!")

            # Display small text below the button
            st.sidebar.markdown("<p style='font-size: 10px; color: gray;'>Double-click to confirm.</p>", unsafe_allow_html=True)

    st.sidebar.write("---")

def display_blog(blog_path, images_path):
    paragraphs = extract_json(blog_path)
    images_for_paragraphs = extract_json(images_path)
    images_for_paragraphs = transform_image_dict(images_for_paragraphs)
    display_text_with_images(paragraphs, images_for_paragraphs)

# Run the Streamlit app
if __name__ == "__main__":
    # st.title("Final Blog")
    blog_path = 'output1/final_blog/final_blog.json'
    images_path = 'output1  /final_blog/final_blog_images.json'
    paragraphs = extract_json(blog_path)
    images_for_paragraphs = extract_json(images_path)
    # print(f"1 : {images_for_paragraphs}")
    images_for_paragraphs = transform_image_dict(images_for_paragraphs)
    # print(f"2 : {images_for_paragraphs}")
    display_text_with_images(paragraphs, images_for_paragraphs)