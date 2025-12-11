# 👕 Wardrobe Stylist AI

A smart digital closet and personal stylist application powered by **Google Gemini** and **Streamlit**. This tool allows you to digitize your wardrobe by uploading photos of your clothes and uses AI to organize them and suggest outfits for any occasion.

## ✨ Features

* **AI Image Analysis**: Upload photos of your clothes. The app uses **Gemini 2.5 Flash** (Vision) to automatically detect the item's name, category, color, best season, and provides a styling tip.
* **Digital Closet**: View your wardrobe in a visual grid layout.
* **Personalized Stylist**: Ask the AI for outfit recommendations based on your current inventory, specific occasions (e.g., Date Night, Office), and weather conditions.
* **Session Storage**: Your closet is saved in your session while you use the app.

## 🛠️ Tech Stack

* **Frontend**: [Streamlit](https://streamlit.io/)
* **AI Model**: Google Gemini 2.5 Flash (via `google-generativeai`)
* **Image Processing**: Pillow (PIL)
* **Environment Management**: python-dotenv

## 🚀 Getting Started

### Prerequisites

* Python 3.8 or higher
* A **Google API Key** (Get one from [Google AI Studio](https://aistudio.google.com/))

### Installation

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/your-username/wardrobe-stylist-ai.git](https://github.com/your-username/wardrobe-stylist-ai.git)
    cd wardrobe-stylist-ai
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables**
    Create a `.env` file in the root directory and add your Google API Key:
    ```env
    GOOGLE_API_KEY=your_actual_api_key_here
    ```

### Running the App

Run the Streamlit application:

```bash
streamlit run app.py
