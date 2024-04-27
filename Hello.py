import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from collections import Counter
from api_token_manager import ApiTokenManager

# Load environment variables from .env file
load_dotenv()

# Retrieve access token from environment variables
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
if ACCESS_TOKEN is None:
    raise ValueError("ACCESS_TOKEN not found in environment variables. Please set it in your .env file.")

# Set the API access token using ApiTokenManager
ApiTokenManager.set_access_token(ACCESS_TOKEN)

# Define API constants
BASE_URL = 'https://healthservice.priaid.ch'
SYMPTOM_CHECKER_ENDPOINT = '/symptoms'
HEADERS = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

# Define file paths for your CSV files
filenames = [
    'dataset.csv',
    'symptom_description.csv',
    'symptom_precaution.csv',
    'Symptom-severity.csv',
    'medquad.csv'
]

# Use os.path.join to create file paths
script_dir = os.path.dirname(os.path.abspath(__file__))
filepaths = [os.path.join(script_dir, filename) for filename in filenames]

# Read all CSV files into DataFrames and store in a dictionary
dataframes = {}
for filepath in filepaths:
    try:
        df_name = os.path.splitext(os.path.basename(filepath))[0]
        dataframes[df_name] = pd.read_csv(filepath)
        st.write(f"Successfully loaded {df_name} from {filepath}")
    except FileNotFoundError:
        st.write(f"File not found: {filepath}")
    except pd.errors.EmptyDataError:
        st.write(f"Empty DataFrame: {filepath}")
    except pd.errors.ParserError as e:
        st.write(f"Error parsing CSV file {filepath}: {e}")


def clean_symptom(symptom):
    if isinstance(symptom, str):
        return symptom.strip().lower()
    else:
        return ""


def get_user_query():
    st.sidebar.title("Health Information Query")
    choice = st.sidebar.selectbox("Select query type:", [
        "Disease Description",
        "Symptom Matching",
        "Precautions for a Disease",
        "Symptom Severity",
        "Causes of a Disease",
        "Diagnosis of a Disease",
        "Research about a Disease",
        "Exit"  # Added 'Exit' option
    ])
    return choice


def handle_user_query(choice, dataframes):
    if choice == "Disease Description":
        disease_name = st.text_input("Enter the disease name:")
        display_disease_description(disease_name, dataframes)
    elif choice == "Symptom Matching":
        symptoms_input = st.text_area("Enter your symptoms separated by commas (e.g., cough, fever):")
        match_symptoms(symptoms_input, dataframes)
    elif choice == "Precautions for a Disease":
        disease_name = st.text_input("Enter the disease name:")
        display_precautions(disease_name, dataframes)
    elif choice == "Symptom Severity":
        symptom_name = st.text_input("Enter the symptom name:")
        display_symptom_severity(symptom_name, dataframes)
    elif choice == "Causes of a Disease":
        disease_name = st.text_input("Enter the disease name:")
        display_disease_causes(disease_name, dataframes)
    elif choice == "Diagnosis of a Disease":
        disease_name = st.text_input("Enter the disease name:")
        display_disease_diagnosis(disease_name, dataframes)
    elif choice == "Research about a Disease":
        disease_name = st.text_input("Enter the disease name:")
        display_disease_research(disease_name, dataframes)
    elif choice == "Exit":
        st.stop()


def display_disease_description(disease_name, dataframes):
    if 'symptom_description' in dataframes:
        symptom_description_df = dataframes['symptom_description']
        filtered_df = symptom_description_df[symptom_description_df['Disease'].str.lower() == disease_name.lower()]
        if not filtered_df.empty:
            description = filtered_df.iloc[0]['Description']
            st.write(f"Disease Description for '{disease_name.capitalize()}':")
            st.write(description)
        else:
            st.write(f"Disease '{disease_name}' not found in the dataset.")
    else:
        st.write("Symptom description dataset not loaded.")


def match_symptoms(symptoms_input, dataframes):
    user_symptoms_list = [clean_symptom(symptom) for symptom in symptoms_input.split(',')]
    if 'dataset' in dataframes:
        dataset_df = dataframes['dataset']
        matched_diseases = dataset_df[dataset_df.apply(
            lambda row: any(clean_symptom(symptom) in user_symptoms_list for symptom in row), axis=1)]
        if not matched_diseases.empty:
            disease_counts = Counter(matched_diseases['Disease'])
            st.write("Potential diseases associated with your symptoms:")
            for disease, count in disease_counts.most_common():
                disease_percentage = (count / len(matched_diseases)) * 100
                st.write(f"- {disease} ({disease_percentage:.2f}%)")
        else:
            st.write("No matching diseases found for the provided symptoms.")
    else:
        st.write("Dataset not loaded.")


def display_precautions(disease_name, dataframes):
    if 'symptom_precaution' in dataframes:
        symptom_precaution_df = dataframes['symptom_precaution']
        filtered_df = symptom_precaution_df[symptom_precaution_df['Disease'].str.lower() == disease_name.lower()]
        if not filtered_df.empty:
            precautions = filtered_df.iloc[0][['Precaution_1', 'Precaution_2', 'Precaution_3', 'Precaution_4']].tolist()
            precautions = [precaution for precaution in precautions if isinstance(precaution, str)]
            if precautions:
                st.write(f"Precautions for {disease_name.capitalize()}:")
                for precaution in precautions:
                    st.write(f"- {precaution}")
            else:
                st.write(f"No precautions listed for '{disease_name}' in the dataset.")
        else:
            st.write(f"Disease '{disease_name}' not found in the dataset.")
    else:
        st.write("Symptom precaution dataset not loaded.")


def display_symptom_severity(symptom_name, dataframes):
    if 'Symptom-severity' in dataframes:
        symptom_severity_df = dataframes['Symptom-severity']
        filtered_df = symptom_severity_df[symptom_severity_df['Symptom'].str.lower() == symptom_name.lower()]
        if not filtered_df.empty:
            severity = filtered_df['weight'].values[0]
            st.write(f"Severity of {symptom_name.capitalize()}: {severity}")
        else:
            st.write(f"Symptom '{symptom_name}' not found in the dataset.")
    else:
        st.write("Symptom severity dataset not loaded.")


def display_disease_causes(disease_name, dataframes):
    if 'medquad' in dataframes:
        medquad_df = dataframes['medquad']
        matched_row = medquad_df[
            medquad_df['question'].str.lower().str.contains(disease_name) &
            medquad_df['question'].str.lower().str.contains('cause')
        ]
        if not matched_row.empty:
            causes = matched_row['answer'].values.tolist()
            if causes:
                st.write(f"Causes of {disease_name.capitalize()} (from 'medquad' dataset):")
                for cause in causes:
                    st.write(f"- {cause}")
            else:
                st.write(f"No causes found for '{disease_name}' in the 'medquad' dataset.")
        else:
            st.write(f"No causes found for '{disease_name}' in the 'medquad' dataset.")
    else:
        st.write("Medquad dataset not loaded.")


def display_disease_diagnosis(disease_name, dataframes):
    if 'medquad' in dataframes:
        medquad_df = dataframes['medquad']
        matched_row = medquad_df[
            medquad_df['question'].str.lower().str.contains(disease_name) &
            medquad_df['question'].str.lower().str.contains('diagnose')
        ]
        if not matched_row.empty:
            diagnoses = matched_row['answer'].values.tolist()
            if diagnoses:
                st.write(f"Diagnosis of {disease_name.capitalize()} (from 'medquad' dataset):")
                for diagnosis in diagnoses:
                    st.write(f"- {diagnosis}")
            else:
                st.write(f"No diagnosis found for '{disease_name}' in the 'medquad' dataset.")
        else:
            st.write(f"No diagnosis found for '{disease_name}' in the 'medquad' dataset.")
    else:
        st.write("Medquad dataset not loaded.")


def display_disease_research(disease_name, dataframes):
    if 'medquad' in dataframes:
        medquad_df = dataframes['medquad']
        matched_row = medquad_df[
            medquad_df['question'].str.lower().str.contains(disease_name) &
            medquad_df['question'].str.lower().str.contains('research')
        ]
        if not matched_row.empty:
            research_info = matched_row['answer'].values.tolist()
            if research_info:
                st.write(f"Research about {disease_name.capitalize()} (from 'medquad' dataset):")
                for info in research_info:
                    st.write(f"- {info}")
            else:
                st.write(f"No research information found for '{disease_name}' in the 'medquad' dataset.")
        else:
            st.write(f"No research information found for '{disease_name}' in the 'medquad' dataset.")
    else:
        st.write("Medquad dataset not loaded.")


def main():
    st.title("Health Information System")

    while True:
        user_choice = get_user_query()

        if user_choice == "Exit":
            break

        handle_user_query(user_choice, dataframes)


if __name__ == "__main__":
    main()
