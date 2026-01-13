
import axcent

agent = axcent.Agent()

@agent.tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to the specified recipient."""
    # Email sending logic here
    return f"Email sent"

print(agent.ask("send an email to shipon@example.com as test"))


