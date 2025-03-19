import pandas as pd
from sklearn.model_selection import train_test_split
from autocorrect import Speller
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from backend.utils import text_preprocess, reduce_lengthening
import numpy as np
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.models import Sequential,Model
from keras.layers.embeddings import Embedding
from keras.layers import Dense,Dropout,Bidirectional,LSTM

nltk.download('punkt')
nltk.download('wordnet')

print("Loading the dataset...")
df = pd.read_csv('./data/merged_dataset.csv')

X = df.Text.values
y = df.political_bias.values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


spell = Speller(lang='en')
lemm = WordNetLemmatizer()

X_train = [text_preprocess(doc) for doc in X_train]
X_test = [text_preprocess(doc) for doc in X_test]

### TRAINING THE MODEL
print("Preprocessing the data...")

# tk = Tokenizer(num_words=None)
# tk.fit_on_texts(X_train)

# X_train = tk.texts_to_sequences(X_train)
# X_test = tk.texts_to_sequences(X_test)

# max_len = np.max(np.array([len(s) for s in [*X_train, *X_test]]))
# marg_len = 10
# maxlen = max_len + marg_len

# X_train = pad_sequences(X_train,maxlen=maxlen)
# X_test = pad_sequences(X_test,maxlen=maxlen)

# embedding_dim = 100
# model = Sequential()
# model.add(Embedding(num_tokens,embedding_dim,input_length=maxlen))
# model.add(Bidirectional(LSTM(128,return_sequences=True)))
# model.add(Dropout(0.5))
# model.add(Bidirectional(LSTM(128,return_sequences=True)))
# model.add(Dropout(0.5))
# model.add(Dense(1,activation='sigmoid'))

# print("Compiling the model...")
# model.compile(loss='binary_crossentropy',optimizer='adam',metrics=['accuracy'])

# print("Training the model...")
# model.fit(X_train,y_train,batch_size=128,epochs=10,validation_split=0.2)

# print("Model Evaluation:")
# print(model.evaluate(X_test,y_test))

# model.save('model.h5')

# print("Model Saved")
