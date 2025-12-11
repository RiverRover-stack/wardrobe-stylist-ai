import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
from dotenv import load_dotenv

# 1. Configuration
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") 
if api_key:
    genai.configure(api_key=api_key)

st.set_page_config(page_title="Wardrobe.AI", page_icon="👕", layout='wide')

if 'closet' not in st.session_state:
    st.session_state.closet = []

# 2. Sidebar for Uploading
with st.sidebar:
    st.title("➕ Add New Item")
    uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg", "webp"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Preview", use_column_width=True)
        
        if st.button("Analyze & Save to Closet"):
            if not api_key:
                st.error("API Key missing.")
            else:
                with st.spinner("AI is analyzing..."):
                    try:
                        # Use the model (1.5 Flash is great for speed)
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        
                        # We ask for JSON format to make it easier to display later
                        prompt = """
                        Analyze this clothing item. Return ONLY a valid JSON object with these keys:
                        {
                            "item_name": "Short name (e.g. Navy Gym Tee)",
                            "category": "Type (e.g. T-Shirt, Jeans)",
                            "color": "Main color",
                            "season": "Best season",
                            "styling_tip": "One short tip"
                        }
                        Do not use Markdown formatting. Just the JSON string.
                        """
                        
                        response = model.generate_content([prompt, image])
                        
                        # Clean up response to ensure it's valid JSON
                        import json
                        import re
                        
                        # Remove markdown code blocks if AI adds them
                        text_response = response.text.replace("```json", "").replace("```", "")
                        item_data = json.loads(text_response)
                        
                        # Add image to the data object (we keep it in memory)
                        item_data['image'] = image
                        
                        # --- SAVE TO MEMORY ---
                        st.session_state.closet.append(item_data)
                        st.success(f"Saved {item_data['item_name']} to closet!")
                        
                    except Exception as e:
                        st.error(f"Error: {e}")

# 3. Main Screen: The Closet Gallery
st.title("👕 My Digital Closet")

# Check if closet is empty
if len(st.session_state.closet) == 0:
    st.info("Your closet is empty. Upload items using the sidebar! 👈")
else:
    # Create a grid layout
    cols = st.columns(3) # 3 items per row
    
    for idx, item in enumerate(st.session_state.closet):
        with cols[idx % 3]: # Cycle through columns 0, 1, 2
            st.image(item['image'], use_column_width=True)
            st.subheader(item['item_name'])
            st.caption(f"**{item['category']}** • {item['season']}")
            with st.expander("Styling Tip"):
                st.write(item['styling_tip'])
            st.divider()


# --- NEW SECTION: The AI Stylist ---
st.divider()
st.header("✨ AI Stylist")

if len(st.session_state.closet) > 0:
    # 1. Inputs for the User
    col1, col2 = st.columns(2)
    with col1:
        occasion = st.selectbox("Occasion", ["Casual", "Gym", "Date Night", "Office", "Party"])
    with col2:
        weather = st.selectbox("Weather", ["Sunny", "Rainy", "Cold", "Hot"])

    if st.button("Generate Outfit Idea"):
        with st.spinner(f"Finding the perfect {occasion} outfit..."):
            try:
                # 2. Prepare the Data (Text only, no images)
                # We strip out the image object to keep the prompt small
                closet_text = []
                for item in st.session_state.closet:
                    closet_text.append({
                        "name": item['item_name'],
                        "category": item['category'],
                        "color": item['color']
                    })
                
                # 3. The Prompt
                prompt = f"""
                Act as a fashion stylist. 
                Here is my closet inventory: {closet_text}
                
                Create a complete outfit for this occasion: {occasion}
                Weather: {weather}
                
                Rules:
                1. Pick 1 Top, 1 Bottom, and (optional) Shoes/Accessories from the inventory.
                2. Explain WHY you chose this combo.
                3. If I don't have enough items, tell me what basic item I am missing to complete the look.
                """
                
                # 4. Call Gemini (Text-only mode is super fast)
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                
                # 5. Display Result
                st.success("Here is your look:")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Stylist Error: {e}")