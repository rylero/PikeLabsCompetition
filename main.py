import dataset_utils
import pandas as pd

dataset_utils.download_kaggle_dataset('neelgajare/liberals-vs-conservatives-on-reddit-13000-posts')
dataset_utils.download_kaggle_dataset('mayobanexsantana/political-bias')

dataset_1 = dataset_utils.load_dataset('Political_Bias.csv')
dataset_2 = dataset_utils.load_dataset('file_name.csv')

print(dataset_1.head())
print(dataset_2.head())