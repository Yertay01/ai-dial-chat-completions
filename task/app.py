import asyncio

from task.clients.client import DialClient
from task.constants import DEFAULT_SYSTEM_PROMPT
from task.models.conversation import Conversation
from task.models.message import Message
from task.models.role import Role


async def start(stream: bool) -> None:
    # 1.1. Create DialClient
    # For this example, using "gpt-4o" as deployment_name
    # You can check available models at https://ai-proxy.lab.epam.com/openai/models
    client = DialClient(deployment_name="gpt-4o")
    
    # 2. Create Conversation object
    conversation = Conversation()
    
    # 3. Get System prompt from console or use default
    print("Provide System prompt or press 'enter' to continue.")
    system_prompt_input = input("> ").strip()
    system_prompt = system_prompt_input if system_prompt_input else DEFAULT_SYSTEM_PROMPT
    
    # Add system message to conversation history
    system_message = Message(role=Role.SYSTEM, content=system_prompt)
    conversation.add_message(system_message)
    
    print("\nType your question or 'exit' to quit.")
    
    # 4. Use infinite cycle to get user messages from console
    while True:
        # Get user input
        user_input = input("> ").strip()
        
        # 5. If user message is 'exit' then stop the loop
        if user_input.lower() == 'exit':
            print("Exiting the chat. Goodbye!")
            break
        
        # Skip empty messages
        if not user_input:
            continue
        
        # 6. Add user message to conversation history
        user_message = Message(role=Role.USER, content=user_input)
        conversation.add_message(user_message)
        
        # 7. Call appropriate completion method based on stream parameter
        try:
            if stream:
                # Call stream_completion for streaming response
                ai_message = await client.stream_completion(conversation.get_messages())
            else:
                # Call get_completion for regular response
                ai_message = client.get_completion(conversation.get_messages())
            
            # 8. Add generated message to history
            conversation.add_message(ai_message)
            
        except Exception as e:
            print(f"Error: {e}")
            # Remove the last user message if request failed
            conversation.messages.pop()


asyncio.run(
    start(True)
)
