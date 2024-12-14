# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx",
#   "pandas",
#   "matplotlib",
#   "seaborn",
#   "scikit-learn",
#   "numpy",
#   "chardet",
#   "requests",
#   "tqdm"
# ]
# ///

import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import requests
import argparse

# Ensure environment variable for API Token is set
API_ACCESS_TOKEN = os.environ.get("AIPROXY_TOKEN")
if not API_ACCESS_TOKEN:
    print("Error: API_ACCESS_TOKEN environment variable is not set.")
    exit(1)

# Headers for API requests
API_ENDPOINT = "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
REQUEST_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_ACCESS_TOKEN}"
}

def send_request_to_model(chat_history, temp=0.7, max_output=500):
    """ Send a request to the AI model via API. """
    request_body = {
        "model": "gpt-4o-mini",
        "messages": chat_history,
        "temperature": temp,
        "max_tokens": max_output
    }
    response = requests.post(API_ENDPOINT, headers=REQUEST_HEADERS, json=request_body)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        print(f"Error during model request: {response.status_code}\n{response.text}")
        exit(1)

def process_csv_file(file_path, results_folder):
    """ Perform analysis on the CSV file and return summarized details. """
    try:
        # Load the CSV data
        data_frame = pd.read_csv(file_path, encoding="ISO-8859-1")
    except Exception as error:
        print(f"Error reading the CSV file: {error}")
        exit(1)

    # Summary details about the dataset
    dataset_summary = {
        "total_rows": len(data_frame),
        "total_columns": len(data_frame.columns),
        "column_types": data_frame.dtypes.to_dict(),
        "null_values": data_frame.isnull().sum().to_dict(),
        "sample_records": data_frame.head(5).to_dict()
    }

    # Extract numerical columns
    numeric_columns = data_frame.select_dtypes(include="number").columns

    if len(numeric_columns) > 0:
        # Create a heatmap for the correlation matrix
        correlation_data = data_frame[numeric_columns].corr()
        sns.heatmap(correlation_data, annot=True, cmap="coolwarm")
        plt.title("Feature Correlation Matrix")
        plt.savefig(os.path.join(results_folder, "correlation_matrix_plot.png"))
        plt.close()

        # Generate a histogram for the first numerical feature
        sns.histplot(data_frame[numeric_columns[0]].dropna(), kde=True, color="green")
        plt.title(f"Distribution of {numeric_columns[0]}")
        plt.savefig(os.path.join(results_folder, "distribution_histogram.png"))
        plt.close()

        # Create a scatter plot for the first two numerical columns if available
        if len(numeric_columns) > 1:
            sns.scatterplot(x=data_frame[numeric_columns[0]], y=data_frame[numeric_columns[1]])
            plt.title(f"Scatter Plot: {numeric_columns[0]} vs {numeric_columns[1]}")
            plt.savefig(os.path.join(results_folder, "scatter_plot_chart.png"))
            plt.close()

        # Create a pair plot for all numerical features
        sns.pairplot(data_frame[numeric_columns])
        plt.suptitle("Pairwise Relationships of Numerical Features", y=1.02)
        plt.savefig(os.path.join(results_folder, "pairwise_relationship_plot.png"))
        plt.close()
    else:
        print("No numerical columns were found for analysis.")

    # Heatmap for missing values
    sns.heatmap(data_frame.isnull(), cbar=False, cmap="viridis")
    plt.title("Missing Data Heatmap")
    plt.savefig(os.path.join(results_folder, "missing_data_heatmap.png"))
    plt.close()

    return dataset_summary

def create_report_file(summary_data, generated_analysis, results_folder):
    """ Generate a markdown file summarizing the analysis. """
    report_content = """# Dataset Analysis Report

## Overview
- Total Rows: {total_rows}
- Total Columns: {total_columns}

### Column Details:
{column_details}

## Insights from Analysis
{analysis_text}

## Visualizations
1. Correlation Matrix: ![Correlation Matrix](correlation_matrix_plot.png)
2. Histogram: ![Distribution Histogram](distribution_histogram.png)
3. Scatter Plot: ![Scatter Plot](scatter_plot_chart.png)
4. Pairwise Relationships: ![Pair Plot](pairwise_relationship_plot.png)
5. Missing Data Heatmap: ![Missing Data Heatmap](missing_data_heatmap.png)
""".format(
        total_rows=summary_data['total_rows'],
        total_columns=summary_data['total_columns'],
        column_details="\n".join([f"- {col_name}: {col_type}" for col_name, col_type in summary_data["column_types"].items()]),
        analysis_text=generated_analysis
    )

    with open(os.path.join(results_folder, "README.md"), "w") as report_file:
        report_file.write(report_content)

def execute_analysis():
    # Parse command-line inputs
    argument_parser = argparse.ArgumentParser(description="Dataset Analysis Automation")
    argument_parser.add_argument("csv_file", help="Path to the CSV file for analysis")
    args = argument_parser.parse_args()

    # Create a directory for the results
    file_basename = os.path.splitext(os.path.basename(args.csv_file))[0]
    result_directory = os.path.join(os.getcwd(), file_basename)
    os.makedirs(result_directory, exist_ok=True)

    # Step 1: Perform analysis on the dataset
    print("Performing dataset analysis...")
    analysis_summary = process_csv_file(args.csv_file, result_directory)

    # Step 2: Request narrative generation from the model
    print("Generating insights via AI...")
    chat_history = [
        {"role": "system", "content": "You are an expert data analyst."},
        {"role": "user", "content": f"Provide insights based on this dataset summary: {analysis_summary}. Keep it concise and informative."}
    ]
    
    narrative = send_request_to_model(chat_history)

    # Step 3: Create a detailed report
    print("Generating analysis report...")
    create_report_file(analysis_summary, narrative, result_directory)

    print("Analysis complete. Check the generated report and visualizations.")

if __name__ == "__main__":
    execute_analysis()
