import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import json
from supabase import create_client, Client

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
                    
                    # SAVE TO SUPABASE DB
                    data_to_insert = {
                        "item_name": item_data['item_name'],
                        "category": item_data['category'],
                        "color": item_data['color'],
                        "season": item_data['season'],
                        "styling_tip": item_data['styling_tip']
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
    with col2:
        weather = st.selectbox("Weather", ["Sunny", "Rainy", "Cold"])

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