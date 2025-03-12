import dataset_utils
import pandas as pd

dataset_utils.download_kaggle_dataset('neelgajare/liberals-vs-conservatives-on-reddit-13000-posts')
dataset_utils.download_kaggle_dataset('mayobanexsantana/political-bias')

dataset_1 = dataset_utils.load_dataset('Political_Bias.csv')
dataset_2 = dataset_utils.load_dataset('file_name.csv')

dataset_1["political_bias"] = dataset_1["Bias"].map({"left": -1, "lean left": -0.5, "center left": 0, "center right": 0.5, "lean right": 1, "right": 1})
dataset_2["political_bias"] = dataset_2["Political Lean"].map({"Liberal": -1, "Conservative": 1})

merged_dataset = pd.merge(dataset_1, dataset_2, on="Text", how="inner")

print(merged_dataset.head())