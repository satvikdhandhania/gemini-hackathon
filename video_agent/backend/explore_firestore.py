"""
Temporary script to explore Firestore structure
"""
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate('/app/firestore_credentials.json')
firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()

print("=== Exploring Firestore Collections ===\n")

# List all collections
collections = db.collections()
collection_names = [col.id for col in collections]

print(f"Found {len(collection_names)} collections:")
for name in collection_names:
    print(f"  - {name}")

print("\n=== Exploring Character-related Collections ===\n")

# Try to find character-related collections
character_collections = [name for name in collection_names if 'character' in name.lower() or 'user' in name.lower() or 'profile' in name.lower()]

if character_collections:
    print(f"Potential character collections: {character_collections}")

    # Explore the first character-related collection
    for coll_name in character_collections:
        print(f"\n--- Collection: {coll_name} ---")
        docs = db.collection(coll_name).limit(1).stream()

        for doc in docs:
            print(f"Document ID: {doc.id}")
            print(f"Document fields: {list(doc.to_dict().keys())}")
            print(f"Sample data: {doc.to_dict()}")
            break
else:
    print("No obvious character collections found. Listing all collections with sample data:")
    for coll_name in collection_names:
        print(f"\n--- Collection: {coll_name} ---")
        docs = db.collection(coll_name).limit(1).stream()

        for doc in docs:
            print(f"Document ID: {doc.id}")
            print(f"Document fields: {list(doc.to_dict().keys())}")
            # Don't print full data to avoid exposing sensitive info
            break
