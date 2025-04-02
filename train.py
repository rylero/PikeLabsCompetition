import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer, BertModel
from sklearn.model_selection import train_test_split

# 1. Define custom dataset class
class SentimentDataset(Dataset):
    def __init__(self, dataframe, tokenizer, max_length=128):
        self.texts = dataframe['text'].values
        self.labels = dataframe['label'].values
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]

        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_length,
            return_token_type_ids=False,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt'
        )

        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.float)
        }

# 2. Define the sentiment regression model
class BertSentimentRegressor(nn.Module):
    def __init__(self, dropout_rate=0.1):
        super(BertSentimentRegressor, self).__init__()
        self.bert = BertModel.from_pretrained('bert-base-uncased')
        self.dropout = nn.Dropout(dropout_rate)
        self.regressor = nn.Linear(self.bert.config.hidden_size, 1)  # Single output for regression
        self.tanh = nn.Tanh()  # To constrain output between -1 and 1

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        pooled_output = outputs[1]  # [CLS] token
        pooled_output = self.dropout(pooled_output)
        output = self.regressor(pooled_output)
        return self.tanh(output)  # Output between -1 and 1

# 3. Training function modified for regression
def train_model(model, train_loader, val_loader, device, epochs=3):
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
    criterion = nn.MSELoss()  # Mean Squared Error for regression

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        
        for i, batch in enumerate(train_loader):
            print(f"batchid: {i}")
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device).float().unsqueeze(1)  # Reshape to [batch_size, 1]

            optimizer.zero_grad()
            outputs = model(input_ids, attention_mask)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()

        # Validation
        model.eval()
        val_loss = 0
        
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['labels'].to(device).float().unsqueeze(1)

                outputs = model(input_ids, attention_mask)
                loss = criterion(outputs, labels)
                val_loss += loss.item()

        print(f'Epoch {epoch + 1}:')
        print(f'Training Loss: {total_loss/len(train_loader):.4f}')
        print(f'Validation Loss: {val_loss/len(val_loader):.4f}')

# 4. Main execution
def main(df):
    # Split data
    train_df, val_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42
    )

    # Initialize tokenizer and model
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = BertSentimentRegressor().to(device)

    # Create datasets and dataloaders
    train_dataset = SentimentDataset(train_df, tokenizer)
    val_dataset = SentimentDataset(val_df, tokenizer)
    
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=16)

    print("training")
    # Train the model
    train_model(model, train_loader, val_loader, device)

    print("saving")
    # Save the model
    torch.save(model.state_dict(), 'sentiment_regressor.pth')
    
    return model, tokenizer, device

# 5. Inference function modified for regression
def predict_sentiment(text, model, tokenizer, device, max_length=128):
    model.eval()
    encoding = tokenizer.encode_plus(
        text,
        add_special_tokens=True,
        max_length=max_length,
        return_token_type_ids=False,
        padding='max_length',
        truncation=True,
        return_attention_mask=True,
        return_tensors='pt'
    )

    input_ids = encoding['input_ids'].to(device)
    attention_mask = encoding['attention_mask'].to(device)

    with torch.no_grad():
        output = model(input_ids, attention_mask)
        score = output.item()  # Single float value between -1 and 1
    
    return score

# Example usage
if __name__ == "__main__":
    # Sample DataFrame (replace with your actual DataFrame)
    df = pd.read_csv("./data/merged_dataset.csv")

    df = df.rename(columns={"political_bias": "label", "Text": "text"})
    
    print(df.head())

    # Train the model
    model, tokenizer, device = main(df)
    
    # Example prediction
    test_text = "This is a wonderful experience"
    sentiment_score = predict_sentiment(test_text, model, tokenizer, device)
    print(f"Sentiment Score: {sentiment_score:.4f}")