import streamlit as st
from openai import OpenAI
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Streamlit configuration
st.set_page_config(page_title="5C Analysis Generator", page_icon="📊")

# Set your OpenAI API key
openai_api_key = st.secrets["OPENAI_API_KEY"]

# Initialize the OpenAI client
client = OpenAI(api_key=openai_api_key)

# Set your Google Slides API credentials
SERVICE_ACCOUNT_INFO = st.secrets["GOOGLE_SERVICE_ACCOUNT"]
SCOPES = [
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/drive'
]

# Authenticate and build the Google Slides and Drive services
credentials = service_account.Credentials.from_service_account_info(
    SERVICE_ACCOUNT_INFO, scopes=SCOPES)
slides_service = build('slides', 'v1', credentials=credentials)
drive_service = build('drive', 'v3', credentials=credentials)

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


def create_presentation_with_slides(title, num_slides=6):
    presentation = slides_service.presentations().create(body={'title': title}).execute()
    presentation_id = presentation['presentationId']
    
    requests = []
    for i in range(num_slides):
        requests.append({
            'createSlide': {
                'objectId': f'slide_{i+1}',
                'insertionIndex': i,
                'slideLayoutReference': {
                    'predefinedLayout': 'BLANK'
                }
            }
        })
        # Set background color for each slide
        requests.append({
            'updatePageProperties': {
                'objectId': f'slide_{i+1}',
                'pageProperties': {
                    'pageBackgroundFill': {
                        'solidFill': {
                            'color': {
                                'rgbColor': {
                                    'red': 255/255,
                                    'green': 241/255,
                                    'blue': 226/255
                                }
                            }
                        }
                    }
                },
                'fields': 'pageBackgroundFill'
            }
        })
    
    body = {'requests': requests}
    slides_service.presentations().batchUpdate(presentationId=presentation_id, body=body).execute()
    
    return presentation_id

def create_text_box_request(slide_id, content, left, top, width, height, font_size, is_title=False):
    requests = [
        {
            'createShape': {
                'objectId': f'{slide_id}_{left}_{top}',
                'shapeType': 'TEXT_BOX',
                'elementProperties': {
                    'pageObjectId': slide_id,
                    'size': {'width': {'magnitude': width, 'unit': 'PT'},
                             'height': {'magnitude': height, 'unit': 'PT'}},
                    'transform': {'scaleX': 1, 'scaleY': 1,
                                  'translateX': left, 'translateY': top,
                                  'unit': 'PT'}
                }
            }
        },
        {
            'insertText': {
                'objectId': f'{slide_id}_{left}_{top}',
                'insertionIndex': 0,
                'text': content
            }
        },
        {
            'updateTextStyle': {
                'objectId': f'{slide_id}_{left}_{top}',
                'style': {
                    'fontSize': {'magnitude': font_size, 'unit': 'PT'},
                    'fontFamily': 'Unbounded' if is_title else 'Arial'
                },
                'textRange': {'type': 'ALL'},
                'fields': 'fontSize,fontFamily'
            }
        }
    ]
    return requests

def create_image_placeholder(slide_id, left, top, width, height):
    return [
        {
            'createShape': {
                'objectId': f'{slide_id}_image_placeholder',
                'shapeType': 'RECTANGLE',
                'elementProperties': {
                    'pageObjectId': slide_id,
                    'size': {'width': {'magnitude': width, 'unit': 'PT'},
                             'height': {'magnitude': height, 'unit': 'PT'}},
                    'transform': {'scaleX': 1, 'scaleY': 1,
                                  'translateX': left, 'translateY': top,
                                  'unit': 'PT'}
                }
            }
        },
        {
            'updateShapeProperties': {
                'objectId': f'{slide_id}_image_placeholder',
                'shapeProperties': {
                    'outline': {
                        'dashStyle': 'DASH',
                        'weight': {'magnitude': 1, 'unit': 'PT'},
                        'outlineFill': {
                            'solidFill': {
                                'color': {'rgbColor': {'red': 0.5, 'green': 0.5, 'blue': 0.5}}
                            }
                        }
                    }
                },
                'fields': 'outline'
            }
        }
    ]

def insert_content_into_slides(presentation_id, brand_name, brand_description):
    requests = []
    c_types = ['Company', 'Customers', 'Competitors', 'Collaborators', 'Climate']
    
    for i in range(6):
        slide_id = f'slide_{i+1}'
        if i == 0:
            # Title slide
            requests.extend(create_text_box_request(slide_id, f"5C Analysis: {brand_name}", 50, 50, 600, 50, 24, is_title=True))
            requests.extend(create_text_box_request(slide_id, brand_description, 50, 120, 600, 50, 12))
        else:
            # Content slides
            content = generate_content_for_placeholder('BODY', brand_name, brand_description, c_types[i-1])
            requests.extend(create_text_box_request(slide_id, c_types[i-1], 50, 50, 300, 50, 18, is_title=True))
            
            if c_types[i-1] == 'Customers':
                # Split content into bullet points
                bullet_points = content.split('\n')
                for j, point in enumerate(bullet_points):
                    requests.extend(create_text_box_request(slide_id, f"• {point}", 50, 120 + j*40, 300, 40, 12))
            else:
                requests.extend(create_text_box_request(slide_id, content, 50, 120, 300, 300, 12))
            
            # Add image placeholder on the right side
            requests.extend(create_image_placeholder(slide_id, 400, 50, 300, 400))
    
    body = {'requests': requests}
    slides_service.presentations().batchUpdate(presentationId=presentation_id, body=body).execute()


def share_presentation(presentation_id, email):
    drive_service.permissions().create(
        fileId=presentation_id,
        body={
            'type': 'user',
            'role': 'writer',
            'emailAddress': email
        },
        fields='id'
    ).execute()

def main():
    st.title("5C Analysis Generator")
    
    brand_name = st.text_input("Enter the brand name:")
    brand_description = st.text_area("Enter a brief description of the brand:")
    user_email = st.text_input("Enter your Gmail ID for edit access:")
    
    if st.button("Generate Presentation"):
        if brand_name and brand_description and user_email:
            presentation_title = f"5C Analysis: {brand_name}"
            default_email = "tanul.mittal40@gmail.com"
            
            with st.spinner("Generating presentation..."):
                # Create a new presentation with 6 slides (title + 5Cs)
                presentation_id = create_presentation_with_slides(presentation_title, num_slides=6)
                
                # Share the presentation with the specified emails
                share_presentation(presentation_id, default_email)
                share_presentation(presentation_id, user_email)
                
                # Generate content and insert into slides
                insert_content_into_slides(presentation_id, brand_name, brand_description)
            
            st.success("Presentation generated successfully!")
            st.markdown(f"[View Presentation](https://docs.google.com/presentation/d/{presentation_id}/edit)")
            st.write(f"Edit access granted to: {default_email} and {user_email}")
        else:
            st.error("Please fill in all the fields.")

if __name__ == "__main__":
    main()
