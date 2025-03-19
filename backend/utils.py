
def reduce_lengthening(text):
    pattern = re.compile(r"(.)\1{2,}")
    return pattern.sub(r"\1\1", text)

def text_preprocess(doc):
    temp = doc.lower() # Lowercasing all the letters
    temp = re.sub("@[A-Za-z0-9_]+","", temp) # Removing hashtags and mentions
    temp = re.sub("#[A-Za-z0-9_]+","", temp)
    temp = re.sub(r"http\S+", "", temp) # Removing links
    temp = re.sub(r"www.\S+", "", temp)
    temp = re.sub("[0-9]","", temp) # removing numbers
    temp = re.sub("'"," ",temp) # Removing '
    
    temp = word_tokenize(temp) # Tokenization
    temp = [reduce_lengthening(w) for w in temp] # Fixing Word Lengthening
    temp = [spell(w) for w in temp] # spell corrector
    temp = [lemm.lemmatize(w) for w in temp] # stem
    temp = [w for w in temp if len(w)>2] # Removing short words
    temp = " ".join(w for w in temp)
    
    return temp