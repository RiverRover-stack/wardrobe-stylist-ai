import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import json
from supabase import create_client, Client
import base64
import io
import time
import requests


def get_current_weather():
    try:
        # Get location via IP (Simplest way, might be slightly inaccurate)
        ip_info = requests.get('http://ipinfo.io/json').json()
        city = ip_info.get('city', 'Unknown Location')
        
        # Use a free weather API service
        # For simplicity, we'll use a hardcoded coordinate or a simple text-based forecast
        # For a true public app, you'd need a location API key like OpenWeatherMap
        
        # Simple Logic: Check temperature from a free service
        # Using Open-Meteo for a simple forecast
        weather_api_url = "https://api.open-meteo.com/v1/forecast?latitude=12.97&longitude=77.59&current=temperature_2m,weather_code" # Bangalore
        weather_data = requests.get(weather_api_url).json()
        temp_c = weather_data['current']['temperature_2m']
        
        if temp_c > 30:
            return "Hot and Sunny"
        elif temp_c < 18:
            return "Cold"
        else:
            return "Mild"

    except Exception:
        # Fallback if API fails
        return "Mild"


# 1. Setup Page
st.set_page_config(page_title="Wardrobe.AI", page_icon="👕", layout="wide")

# 2. Load Secrets (Works both locally and on Cloud if setup correctly)
# On Local: You need a .streamlit/secrets.toml file OR just hardcode for testing (be careful!)
# On Cloud: It reads from the Dashboard Settings
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    SUPABASE_URL = st.secrets["supabase"]["URL"]
    SUPABASE_KEY = st.secrets["supabase"]["KEY"]
except:
    st.error("Secrets not found! Make sure you added them to Streamlit Cloud.")
    st.stop()

# 3. Initialize Connections
genai.configure(api_key=GOOGLE_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.session_state['user_id'] = "demo_user"

# --- SIDEBAR: Upload & Analyze ---
with st.sidebar:
    st.title("➕ Add New Item")
    uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg", "webp"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Preview", use_column_width=True)
        
        if st.button("Analyze & Save"):
            with st.spinner("AI is analyzing..."):
                try:
                    # AI Analysis
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    prompt = """
                    Analyze this clothing item. Return ONLY a valid JSON object with these keys:
                    {
                        "item_name": "Short name",
                        "category": "Type",
                        "color": "Main color",
                        "season": "Best season",
                        "styling_tip": "One short tip"
                    }
                    """
                    response = model.generate_content([prompt, image])
                    text_response = response.text.replace("```json", "").replace("```", "")
                    item_data = json.loads(text_response)

                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format=uploaded_file.type.split('/')[-1].upper() if uploaded_file.type else 'PNG')
                    img_bytes = img_byte_arr.getvalue()
                    
                    filename = f"{st.session_state['user_id']}/{item_data['item_name'].replace(' ', '_')}_{int(time.time())}.png"

                    # Upload the file
                    supabase.storage.from_("item_images").upload(filename, img_bytes, file_options={"content-type": uploaded_file.type})

                    # Get the public URL for the image
                    image_url = supabase.storage.from_("item_images").get_public_url(filename)

                    # SAVE TO SUPABASE DB
                    data_to_insert = {
                        "item_name": item_data['item_name'],
                        "category": item_data['category'],
                        "color": item_data['color'],
                        "season": item_data['season'],
                        "styling_tip": item_data['styling_tip'],
                        "image_url": image_url
                    }
                    
                    supabase.table('clothes').insert(data_to_insert).execute()
                    
                    st.success(f"Saved {item_data['item_name']} to Database!")
                    st.rerun() # Refresh page to show new item
                    
                except Exception as e:
                    st.error(f"Error: {e}")

# --- MAIN PAGE: The Database View ---
st.title("👕 My Cloud Closet")

# Fetch Data from Supabase
response = supabase.table('clothes').select("*").execute()
closet_items = response.data

if not closet_items:
    st.info("Database is empty. Add items from the sidebar!")
else:
    # Display as a list/grid
    for item in closet_items:
        with st.expander(f"**{item['item_name']}** ({item['category']})"):
            st.image(item['image_url'], width=150)
            st.write(f"🎨 **Color:** {item['color']}")
            st.write(f"🍂 **Season:** {item['season']}")
            st.info(f"💡 **Tip:** {item['styling_tip']}")
            
            # Delete Button
            if st.button("Delete Item", key=item['id']):
                supabase.table('clothes').delete().eq("id", item['id']).execute()
                st.rerun()

# --- AI STYLIST SECTION ---
st.divider()
st.header("✨ AI Stylist")

if len(closet_items) > 0:
    col1, col2 = st.columns(2)
    with col1:
        occasion = st.selectbox("Occasion", ["Casual", "Gym", "Date Night", "Office"])

    auto_weather = get_current_weather()
    with col2:
        st.markdown(f"**Detected Weather:** `{auto_weather}`")
        # You can keep the manual selection as a fallback
        weather = st.selectbox("Override Weather", ["Auto", "Sunny", "Rainy", "Cold"], index=0)

    if st.button("Generate Outfit"):
        with st.spinner("Thinking..."):
            # Prepare text data for AI
            inventory_text = str(closet_items) 
            
            stylist_prompt = f"""
            Act as a fashion stylist. 
                Here is my closet inventory: {inventory_text}
                
                Create a complete outfit for this occasion: {occasion}
                Weather: {weather}
                
                Rules:
                1. Pick 1 Top, 1 Bottom, and (optional) Shoes/Accessories from the inventory.
                2. Explain WHY you chose this combo.
                3. If I don't have enough items, tell me what basic item I am missing to complete the look.
            """
            
            model = genai.GenerativeModel('gemini-2.5-flash')
            advice = model.generate_content(stylist_prompt)
            st.markdown(advice.text)