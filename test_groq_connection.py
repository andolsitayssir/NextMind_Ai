# Create: c:\Bureau\NextMind\test_groq_connection.py

import os
from openai import OpenAI

def test_groq_api():
    """Test if Groq API is working"""
    
    print("🧪 Testing Groq API Connection...")
    
    # Check environment variable
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY environment variable not found!")
        print("   Please set it using: set GROQ_API_KEY=your_key_here")
        return False
    
    print(f"✅ API Key found: {api_key[:20]}...")
    
    try:
        # Initialize client
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        print("✅ Client initialized successfully")
        
        # Simple test
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": "Say 'Hello from Groq!' and nothing else."}],
            max_tokens=10,
            temperature=0.1,
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ API Response: {result}")
        
        if "Hello" in result:
            print("🎉 Groq API is working perfectly!")
            return True
        else:
            print("⚠️ Groq API responded but with unexpected content")
            return False
            
    except Exception as e:
        print(f"❌ Groq API Error: {str(e)}")
        print(f"   Error Type: {type(e)}")
        return False

if __name__ == "__main__":
    test_groq_api()