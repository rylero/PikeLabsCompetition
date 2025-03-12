import os
from kaggle.api.kaggle_api_extended import KaggleApi
import pandas as pd

"""
Download a dataset from Kaggle.
    
Args:
    dataset_name (str): Name of the dataset in format 'owner/dataset-name'
    save_path (str): Local path to save the dataset
"""
def download_kaggle_dataset(dataset_name: str, save_path='./data'):
    try:
        # Initialize the Kaggle API
        api = KaggleApi()
        api.authenticate()
        
        # Create the save directory if it doesn't exist
        os.makedirs(save_path, exist_ok=True)
        
        # Download the dataset
        api.dataset_download_files(dataset_name, path=save_path, unzip=True)
        print(f"Dataset successfully downloaded to {save_path}")
        
    except Exception as e:
        print(f"Error downloading dataset: {str(e)}")

def load_dataset(dataset_name: str, save_path='./data'):
    """
    Load a dataset from a CSV file.
    
    Args:
        dataset_name (str): Name of the dataset in format 'owner/dataset-name'
        save_path (str): Local path to save the dataset
    """
    return pd.read_csv(os.path.join(save_path, dataset_name))