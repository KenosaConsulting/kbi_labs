import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def test_google_places():
    api_key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not api_key:
        print("❌ No Google API key found in .env")
        return
    
    # Test business
    business_name = "Microsoft Corporation Redmond"
    
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        'input': business_name,
        'inputtype': 'textquery',
        'fields': 'place_id,name,rating,user_ratings_total,formatted_address',
        'key': api_key
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            
            if data.get('status') == 'OK':
                print("✅ Google Places API working!")
                if data.get('candidates'):
                    place = data['candidates'][0]
                    print(f"📍 Found: {place.get('name')}")
                    print(f"⭐ Rating: {place.get('rating')}/5")
                    print(f"📊 Reviews: {place.get('user_ratings_total')}")
            else:
                print(f"❌ Error: {data.get('status')}")
                print(f"Message: {data.get('error_message', 'No error message')}")

asyncio.run(test_google_places())
