from sentence_transformers import SentenceTransformer

# Load from the internet the first time
model = SentenceTransformer("all-MiniLM-L6-v2")

# Save the model locally
model.save("models/all-MiniLM-L6-v2")

print("✅ Model downloaded and saved to models/all-MiniLM-L6-v2")
