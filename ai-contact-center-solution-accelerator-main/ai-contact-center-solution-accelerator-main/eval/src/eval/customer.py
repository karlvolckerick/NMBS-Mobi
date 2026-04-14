import logging

from openai import AsyncAzureOpenAI

from eval.models import TranscriptMessage

logger = logging.getLogger(__name__)


class CustomerLLM:
    """LLM-driven customer that generates responses based on scenario instructions."""

    def __init__(self, openai_client: AsyncAzureOpenAI, chat_deployment: str) -> None:
        self._client = openai_client
        self._chat_deployment = chat_deployment

    async def generate_response(
        self,
        instructions: str,
        transcript: list[TranscriptMessage],
    ) -> str:
        """Generate the next customer utterance.

        Args:
            instructions: Scenario instructions describing the customer's goal.
            transcript: Conversation history so far.

        Returns:
            The customer's next response text.
        """
        prompt = "Based on the conversation so far, generate an appropriate response.\n\n"
        for msg in transcript:
            if msg.role == "user":
                prompt += f"User: {msg.content}\n"
            else:
                prompt += f"Assistant: {msg.content}\n"
        prompt += "User: "

        messages = [
            {"role": "system", "content": instructions},
            {"role": "user", "content": prompt},
        ]

        response = await self._client.chat.completions.create(
            model=self._chat_deployment,
            messages=messages,
            temperature=0.7,
            max_tokens=64,
        )

        text = response.choices[0].message.content
        if not text or not text.strip():
            return "Could you repeat that?"
        return text.strip()
