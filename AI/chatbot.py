from transformers import pipeline  

# mô hình BERT
classifier = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")

def analyze_symptoms(text):
    result = classifier(text)
    return result

text_input = input('How are you feeling:')
#acb
print(analyze_symptoms(text_input))
