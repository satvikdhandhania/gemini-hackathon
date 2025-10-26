"""
Retrieve alex_agentops_ai user data from Firestore to get actual prompt
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
print("Retrieving alex_agentops_ai User Data")
print("=" * 70)

# Get the specific document
doc_ref = db.collection('email_users').document('alex_agentops_ai')
doc = doc_ref.get()

if doc.exists:
    data = doc.to_dict()
    print(f"\nDocument ID: {doc.id}")
    print("\nAll Fields:")
    for key, value in data.items():
        print(f"  {key}: {type(value).__name__}")

    # Print relevant prompt fields
    print("\n" + "=" * 70)
    print("PROMPT-RELEVANT FIELDS")
    print("=" * 70)

    if 'contentOpinion' in data:
        print(f"\ncontentOpinion:\n{data['contentOpinion']}")

    if 'speakingStyle' in data:
        print(f"\nspeakingStyle:\n{data['speakingStyle']}")

    if 'guardrails' in data:
        print(f"\nguardrails:\n{data['guardrails']}")

    if 'bio' in data:
        print(f"\nbio:\n{data['bio']}")

    if 'description' in data:
        print(f"\ndescription:\n{data['description']}")

else:
    print(f"\n❌ Document 'alex_agentops_ai' not found in email_users collection")
