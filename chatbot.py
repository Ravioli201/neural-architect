import streamlit as st
from neural_architect.llm.gemini_client import GeminiClient

class SOCChatbot:
    def __init__(self, api_key: str):
        self.client = GeminiClient(api_key=api_key)

    def start_session(self, attack_chain_summary: str):
        system_instructions = (
            "You are an expert SOC Tier 3 Analyst. You are assisting a user with an "
            "incident they just analyzed. Context of the incident: \n"
            f"{attack_chain_summary}\n\n"
            "Answer questions accurately, suggest remediation steps, and explain MITRE techniques."
        )
        return self.client.model.start_chat(history=[])

    def ask(self, chat_session, query: str):
        response = chat_session.send_message(query)
        return response.text