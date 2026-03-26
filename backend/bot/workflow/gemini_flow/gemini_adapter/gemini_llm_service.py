from google import genai
from langchain_google_genai import GoogleGenerativeAI, ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv()


# class GeminiLLMService:
#     def __init__(self):
#         self.api_key = os.getenv("GEMINI_API_KEY")
#         self.model = "gemini-2.0-flash"
#         # self.client = genai.Client(api_key=self.api_key)
#         print("--",self.api_key)

#     def generate_response(self, prompt):
#         model = ChatGoogleGenerativeAI(
#             model=self.model,
#         )

#         messages = [("system", "You are a helpful assistant."),
#                     ("user", prompt)]
        
#         ai_msg = model.invoke(messages)
#         print(ai_msg)

# GeminiLLMService().generate_response("hi, their")

from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_content(
    model="gemini-2.0-flash", contents="Explain how AI works in a few words"
)
print(response.text)