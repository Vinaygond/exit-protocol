import json
import logging
from decouple import config  # <--- Loads from .env

# Handle import error if 'openai' isn't installed yet
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)

class BIFFEngine:
    """
    The Intelligence Engine for Secure Communications.
    Uses GPT-4 to transform hostile text into BIFF responses.
    """
    
    def __init__(self):
        # ---------------------------------------------------------
        # SECURE CONFIGURATION
        # ---------------------------------------------------------
        # This reads the key from your .env file
        self.api_key = config('OPENAI_API_KEY', default='')
        # ---------------------------------------------------------
        
        self.model = "gpt-4-turbo"
        self.client = None
        
        # Initialize client if library exists and key is found
        if OpenAI and self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            if not OpenAI:
                print("[AI Engine] Warning: 'openai' library not installed.")
            elif not self.api_key:
                print("[AI Engine] Warning: No OPENAI_API_KEY found in .env. Running in Demo Mode.")

    def rewrite_hostile_text(self, original_text, context=None):
        """
        Sends text to OpenAI to be rewritten.
        """
        # 1. Check if we can make the call
        if not self.client:
            return self.mock_rewrite(original_text)

        # 2. Construct the Prompt
        system_prompt = (
            "You are a top-tier Conflict Resolution Expert specializing in high-conflict divorce cases. "
            "Your goal is to de-escalate communication using the BIFF method (Brief, Informative, Friendly, Firm). "
            "Rewrite the user's hostile message to remove all defensiveness, anger, and emotional triggers. "
            "Stick strictly to facts and logistics. "
            "You must return a valid JSON object with two keys: "
            "'draft' (the rewritten message) and 'analysis' (a 1-sentence explanation of what you changed)."
        )

        user_content = f"Incoming Hostile Text: \"{original_text}\""
        if context:
            user_content += f"\nContext/Goal: {context}"

        try:
            # 3. Call OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )
            
            # 4. Parse Response
            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            logger.error(f"OpenAI API Failed: {e}")
            print(f"[AI Engine] Error calling API: {e}")
            return self.mock_rewrite(original_text)

    def mock_rewrite(self, original_text):
        """
        [FALLBACK MODE]
        Used if API key is missing or network fails.
        """
        text_lower = original_text.lower()
        
        # Financial heuristic
        if any(x in text_lower for x in ['money', 'pay', 'dollar', 'owe', 'bill']):
            return {
                'draft': "I have received your message regarding the expenses. I will review the receipts against our agreement and send a confirmation by Friday at 5:00 PM.",
                'analysis': "Removed emotional urgency. Acknowledged receipt (Friendly) and set a specific timeline for resolution (Firm)."
            }

        # Custody heuristic
        elif any(x in text_lower for x in ['kid', 'child', 'pick', 'drop', 'late']):
            return {
                'draft': "Thank you for the update on the schedule. I will be at the exchange point at the agreed time.",
                'analysis': "Removed defensive language regarding the schedule. Focused strictly on the logistics of the exchange."
            }

        # Generic fallback
        return {
            'draft': "I have received your message. I will review the details and respond shortly.",
            'analysis': "Neutralized tone by removing personal attacks and focusing on the information transfer."
        }