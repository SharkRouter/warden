"""Example ungoverned AI agent — scan with Warden to see findings."""

import openai

# Hardcoded API key (D4: Credential Management)
OPENAI_API_KEY = "sk-proj-abc123def456ghi789jkl012mno345pqr678stu901"

client = openai.OpenAI(api_key=OPENAI_API_KEY)


class MyAgent:
    """A simple agent with no governance controls."""

    def __init__(self):
        self.tools = get_all_tools()  # Unrestricted tool access (D3)

    def run(self, user_input: str) -> str:
        # No input validation or prompt injection protection (D10)
        # No cost tracking or token limits (D12)
        # No permission model (D8)
        while True:  # No exit condition (D2)
            response = client.chat.completions.create(
                model="gpt-4",  # Hardcoded model (D12)
                messages=[{"role": "user", "content": user_input}],
            )

            result = response.choices[0].message.content

            # Tool result used without verification (D15)
            tool_output = self.tools.run_tool(result)
            print(f"Result: {tool_output}")  # print() instead of logging (D5)

            return tool_output


def get_all_tools():
    """Returns all available tools without scoping."""
    pass


if __name__ == "__main__":
    agent = MyAgent()
    agent.run("Do something dangerous")
