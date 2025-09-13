import firebase_admin
from firebase_admin import credentials,  auth
import os
import requests

from dotenv import load_dotenv
load_dotenv()

# Get path to the same folder as this script
current_dir = os.path.dirname(__file__)
key_path = os.path.join(current_dir, "serviceAccountKey.json")

cred = credentials.Certificate(key_path)
firebase_admin.initialize_app(cred)

api_key=os.getenv("FIREBASE_WEB_API_KEY")

# print('api_key', api_key)
url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={api_key}"

async def authenticateUser(phone_number):
    try:
        user = auth.get_user_by_phone_number(phone_number)
        custom_token = auth.create_custom_token(user.uid)
        response = requests.post(url, {
			"token": custom_token,
			"returnSecureToken": True
		})
        response.raise_for_status() # Raise an exception for HTTP errors
        sign_in_data = response.json()
        id_token = sign_in_data['idToken']
        
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        
        return uid
    except requests.exceptions.RequestException as e:
        print(f"Error signing in with custom token: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Error details: {e.response.json()}")