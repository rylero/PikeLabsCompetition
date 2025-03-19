import fastapi
from keras.models import load_model
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from backend.utils import text_preprocess

app = fastapi.FastAPI()

model = keras.models.load_model('model.h5')
tk = Tokenizer(num_words=None)

@app.get("/")
def read_root():
    return {"message": "Root api endpoint"}

@app.get("/generate_report")
def generate_report(text: str):
    tk.fit_on_text(text)
    text = tk.texts_to_sequences(text)

    max_len = np.max(np.array([len(s) for s in [text]]))
    marg_len = 10
    maxlen = max_len + marg_len

    text = pad_sequences(text,maxlen=maxlen)
    prediction = model.predict(text)
    return {"score": prediction}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
