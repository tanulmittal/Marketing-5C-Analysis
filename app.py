import streamlit as st
from openai import OpenAI
import os
import json

# Streamlit configuration
st.set_page_config(page_title="5C Analysis Generator", page_icon="📊")

# Set your OpenAI API key
openai_api_key = st.secrets["OPENAI_API_KEY"]

# Initialize the OpenAI client
client = OpenAI(api_key=openai_api_key)


def generate_content_for_placeholder(placeholder_type, brand_name, brand_description, c_type=None):
    if placeholder_type == 'TITLE':
        return f"5C Analysis: {brand_name}"
    elif placeholder_type == 'SUBTITLE':
        return brand_description
    elif placeholder_type == 'BODY':
        if c_type == 'Company':
            prompt = f"Write about the brand {brand_name}. Include information about its  mission, values, and key products or services. Write under 120 words"
        elif c_type == 'Customers':
            prompt = f"Write in bullet points about {brand_name}'s customer demographics. Include information such as age range, gender, income level, interests, and buying behaviors. Write under 120 words."
        elif c_type == 'Competitors':
            prompt = f"Write about the main competitors of {brand_name}. Explain how they are different or better than {brand_name}. Include information on their strengths, weaknesses, and unique selling propositions. Write under 120 words"
        elif c_type == 'Collaborators':
            prompt = f"Describe the key collaborators or partners of {brand_name}. This may include suppliers, distributors, or strategic alliances. Explain how these relationships benefit {brand_name}. Write under 120 words"
        elif c_type == 'Climate':
            prompt = f"Analyze the business climate or external factors affecting {brand_name}. This may include economic conditions, technological trends, regulatory environment, and social or cultural factors impacting the brand. Write under 120 words"
        else:
            prompt = f"Generate a brief analysis for the '{c_type}' component of the 5C analysis for the brand '{brand_name}'. Brand description: {brand_description}"

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400
        )
        return response.choices[0].message.content.strip()


def create_html_presentation(brand_name, brand_description):
    c_types = ['Company', 'Customers', 'Competitors', 'Collaborators', 'Climate']
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>5C Analysis: {brand_name}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #fff1e2;
            }}
            .page {{
                display: flex;
                height: 100vh;
                padding: 20px;
                box-sizing: border-box;
            }}
            .left-div, .right-div {{
                flex: 1;
                padding: 20px;
            }}
            .title {{
                font-family: 'Unbounded', sans-serif;
                font-size: 24px;
                margin-bottom: 10px;
            }}
            .body-text {{
                font-size: 14px;
            }}
            .image-placeholder {{
                width: 100%;
                height: 300px;
                border: 2px dashed #808080;
                display: flex;
                justify-content: center;
                align-items: center;
                color: #808080;
            }}
        </style>
    </head>
    <body>
    """.format(brand_name=brand_name)

    # Title slide
    html_content += f"""
        <div class="page">
            <div class="left-div">
                <h1 class="title">5C Analysis: {brand_name}</h1>
                <p class="body-text">{brand_description}</p>
            </div>
            <div class="right-div">
                <div class="image-placeholder">Image Placeholder</div>
            </div>
        </div>
    """

    # Content slides
    for c_type in c_types:
        content = generate_content_for_placeholder('BODY', brand_name, brand_description, c_type)
        html_content += f"""
        <div class="page">
            <div class="left-div">
                <h2 class="title">{c_type}</h2>
                <div class="body-text">
        """
        
        if c_type == 'Customers':
            # Split content into bullet points
            bullet_points = content.split('\n')
            html_content += "<ul>"
            for point in bullet_points:
                html_content += f"<li>{point}</li>"
            html_content += "</ul>"
        else:
            html_content += f"<p>{content}</p>"
        
        html_content += """
                </div>
            </div>
            <div class="right-div">
                <div class="image-placeholder">Image Placeholder</div>
            </div>
        </div>
        """

    html_content += """
    </body>
    </html>
    """

    return html_content

def main():
    st.title("5C Analysis Generator")
    
    brand_name = st.text_input("Enter the brand name:")
    brand_description = st.text_area("Enter a brief description of the brand:")
    
    if st.button("Generate Presentation"):
        if brand_name and brand_description:
            with st.spinner("Generating presentation..."):
                html_content = create_html_presentation(brand_name, brand_description)
            
            st.success("Presentation generated successfully!")
            st.download_button(
                label="Download HTML Presentation",
                data=html_content,
                file_name="5c_analysis_presentation.html",
                mime="text/html"
            )
            st.components.v1.html(html_content, height=600, scrolling=True)
        else:
            st.error("Please fill in all the fields.")

if __name__ == "__main__":
    main()
