"""
Explore Firestore to find user/email data
"""
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate('/app/firestore_credentials.json')
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()

print("=" * 70)
print("Exploring Firestore for Users/Characters")
print("=" * 70)

# List all collections
collections = db.collections()
collection_names = [col.id for col in collections]

print(f"\nAll collections: {collection_names}\n")

# Explore each collection for user/email data
for coll_name in collection_names:
    print(f"\n--- Collection: {coll_name} ---")
    docs = db.collection(coll_name).limit(3).stream()

    doc_count = 0
    for doc in docs:
        doc_count += 1
        doc_data = doc.to_dict()
        print(f"\nDocument ID: {doc.id}")
        print(f"Fields: {list(doc_data.keys())}")

        # Print relevant fields if they exist
        relevant_fields = ['email', 'name', 'username', 'handle', 'prompt', 'bio', 'description']
        for field in relevant_fields:
            if field in doc_data:
                value = doc_data[field]
                if isinstance(value, str) and len(value) < 200:
                    print(f"  {field}: {value}")
                elif isinstance(value, str):
                    print(f"  {field}: {value[:200]}...")

    if doc_count == 0:
        print("  (No documents found)")
