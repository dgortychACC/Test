"""
Created on Wed Apr 3 12:12:00 2024

@author: piotr.janczewski
"""

import os
from os.path import exists
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import json
import openai

# Load configuration from JSON file
with open("C:/Users/piotr.janczewski/Desktop/genAI/Test/config.json", mode="r") as f:
    config = json.load(f)

client = openai.AzureOpenAI(
        azure_endpoint=config["AZURE_ENDPOINT"],
        api_key= config["AZURE_API_KEY"],
        api_version="2023-12-01-preview")

st.set_page_config(page_title="Feedback App",
                   # page_icon=folder + "/CVapp/images/favicon_accenture.png",
                   layout="wide",
                   initial_sidebar_state="expanded"
                   )

##############
# Functions
##############

# Function to filter feedback based on time
def filter_feedback(feedback_table, months_back_val):
    delta = timedelta(days=months_back_val * 30)
    threshold_date = datetime.now() - delta
    filtered_feedback = feedback_table[feedback_table['Date'] >= threshold_date]
    return filtered_feedback

def list_to_csv(data):
    csv_string = ''
    for item in data:
        csv_string += "\n".join(map(str, item)) + "\n"
    return csv_string

# Function to generate feedback scenario using Language Model
def generate_feedback_scenario(filtered_feedback):

    scenario = []

    prompt = "You are a thoughtful manager. Based on several pieces of individual feedback, \
                you want to draft a scenario of feedback summary for your subordinate. \
                The scenario should be composed in bullet points, max 2500 characters, \
                and contain three main sections: \
                    1. positive achievements (what went well), \
                    2. area of oppurtunity (what to improve) \
                    3. key strengths to build on in future (what seems the best in the subordinate) \
                For some pieces of individual feedback, some of the sections 1-3 might be empty. \
                If the entire feedback piece is super positive, then point 2 will be left blank. \
                If the entire feedback piece is super negative, then point 1 will be left blank, \
                but in that case still try to derive a single encouraging phrase for the subordinate. \
                Generate feedback scenario for employee based on received feedback:"
    
    # Initialize lists to store individual feedback

    for _, entry in filtered_feedback.iterrows():
        feedback = entry['Feedback']

        messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": feedback}
                ]

        response= client.chat.completions.create(
                messages=messages,
                model="PiotrJ_feedback",
                temperature=0,
                seed=445566)
    
        scenario.append(response.choices[0].message.content)

    return scenario

def main_page():

    output = ''

    st.markdown("<p style='text-align:Left;font-family:Arial;" +
            "font-weight:bold;color:hsl(0, 100%, 0%); font-size:14px;'>" +
            "Input individual feedbacks to produce discussion scenario</p>",
            unsafe_allow_html=True)

    st.write("")

    with st.form("Feedback summary", clear_on_submit=False):

        subordinate_name = st.text_input("Counselee 1st name", value="Ramon")
        subordinate_surname = st.text_input("Counselee surname", value="Puls")

        # Add a file uploader widget
        uploaded_file = st.file_uploader("Upload Excel file with individual feedbacks from WD", type=["xls", "xlsx"])

        months_back_val = st.slider("How old feedback to include: 0=latest, 24=Up to 2Y",
                              min_value=0, max_value=24, value=12)
        st.write("")
                
        # Premilinary listing before final export
        
        produce = st.form_submit_button("Produce feedback scenario")

        if produce:
            
            # Read feedback table from Excel file
            if uploaded_file is not None:
                # Read the Excel file into a pandas DataFrame
                feedback_table = pd.read_excel(uploaded_file, parse_dates=['Date'], skiprows=1)

            # Filter feedback
            filtered_feedback = filter_feedback(feedback_table, months_back_val)

            # Generate feedback scenario
            scenario = generate_feedback_scenario(filtered_feedback)
            st.write("")
            st.write(scenario)
            st.write("")



    # Save feedback scenario to a text file
    if produce:
        output = str(scenario).replace('\\n', '\n').replace('\\t', '\t')
        output_file_name = f"{subordinate_name} {subordinate_surname} - feedback scenario script.txt"
        st.download_button('Download feedback scenario', data = output, file_name=output_file_name, mime='text/csv')

    st.write("https://www.youtube.com/watch?v=WNnzw90vxrE of this form")

        
##############
# PAGE SET UP
##############

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

main_page()