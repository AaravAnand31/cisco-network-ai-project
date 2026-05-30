import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel("gemini-2.0-flash")

SYSTEM_PROMPT = """
You are a Cisco IOS networking assistant.

Convert user requests into Cisco IOS commands.

Rules:
- Return only Cisco commands.
- No explanations.
- No markdown.
- No extra text.

Examples:

User: Show all interfaces
Output:
show interfaces

User: Disable port GigabitEthernet0/1
Output:
configure terminal
interface GigabitEthernet0/1
shutdown
"""

while True:
    user_input = input("\nCommand: ")

    response = model.generate_content(
        SYSTEM_PROMPT + "\nUser: " + user_input
    )

    print("\nGenerated Cisco Commands:\n")
    print(response.text)