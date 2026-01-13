import json
import aiohttp
import requests

from task.clients.base import BaseClient
from task.constants import DIAL_ENDPOINT
from task.models.message import Message
from task.models.role import Role


class DialClient(BaseClient):
    _endpoint: str
    _api_key: str

    def __init__(self, deployment_name: str):
        super().__init__(deployment_name)
        self._endpoint = DIAL_ENDPOINT + f"/openai/deployments/{deployment_name}/chat/completions"

    def _get_content_snippet(self, chunk: str) -> str:
        """
        Parse streaming data chunk and extract content snippet.
        Chunks start with 'data: ' prefix (6 chars).
        Final chunk is 'data: [DONE]'.
        """
        # Remove 'data: ' prefix (6 characters)
        if not chunk.startswith("data: "):
            return ""
        
        json_str = chunk[6:].strip()
        
        # Check for end of stream
        if json_str == "[DONE]":
            return ""
        
        try:
            data = json.loads(json_str)
            # Extract content from delta in choices
            if "choices" in data and len(data["choices"]) > 0:
                delta = data["choices"][0].get("delta", {})
                return delta.get("content", "")
        except json.JSONDecodeError:
            return ""
        
        return ""

    def get_completion(self, messages: list[Message]) -> Message:
        # 1. Create headers dict with api-key and Content-Type
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json"
        }
        
        # 2. Create request_data dictionary
        request_data = {
            "messages": [msg.to_dict() for msg in messages]
        }
        
        # 3. Make POST request
        response = requests.post(
            self._endpoint,
            headers=headers,
            json=request_data
        )
        
        # 5. Check status code
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        
        # 4. Get content from response
        response_data = response.json()
        content = response_data["choices"][0]["message"]["content"]
        print(content)
        
        return Message(role=Role.AI, content=content)

    async def stream_completion(self, messages: list[Message]) -> Message:
        # 1. Create headers dict with api-key and Content-Type
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json"
        }
        
        # 2. Create request_data dictionary with streaming enabled
        request_data = {
            "stream": True,
            "messages": [msg.to_dict() for msg in messages]
        }
        
        # 3. Create empty list to store content snippets
        contents = []
        
        # 4. Create aiohttp.ClientSession
        async with aiohttp.ClientSession() as session:
            # 5. Make POST request
            async with session.post(
                self._endpoint,
                json=request_data,
                headers=headers
            ) as response:
                # 6. Get content from chunks
                async for line in response.content:
                    chunk = line.decode('utf-8').strip()
                    if chunk:
                        content_snippet = self._get_content_snippet(chunk)
                        if content_snippet:
                            print(content_snippet, end='', flush=True)
                            contents.append(content_snippet)
        
        print()  # Print newline after streaming
        full_content = ''.join(contents)
        return Message(role=Role.AI, content=full_content)

