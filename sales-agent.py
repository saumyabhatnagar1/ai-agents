import asyncio
from dotenv import load_dotenv
from agents import Agent, AgentOutputSchema, GuardrailFunctionOutput, Runner, function_tool, input_guardrail, trace
from brevo import AsyncBrevo
import os

from openai import BaseModel


load_dotenv(override=True)

client = AsyncBrevo(api_key=os.environ["BREVO_API_KEY"])

@function_tool
async def send_email(subject: str, html: str):
    """Send an email to all sales prospects."""
    try:
        to_email = os.environ["SALES_EMAIL_TO"]
        to_name = os.environ.get("SALES_EMAIL_TO_NAME", "Prospect")
        sender_email = os.environ["BREVO_SENDER_EMAIL"]
        sender_name = os.environ.get("BREVO_SENDER_NAME", "ComplAI")
        response = await client.transactional_emails.with_raw_response.send_transac_email(
            subject=subject,
            to=[{"email": to_email, "name": to_name}],
            html_content=html,
            sender={"email": sender_email, "name": sender_name},
        )
        return response.data
    except Exception as e:
        return f"Error sending email: {e}"


def email_manager_agent():
    subject_instructions = "You can write a subject for a cold sales email. \
    You are given a message and you need to write a subject for an email that is likely to get a response."

    html_instructions = "You can convert a text email body to an HTML email body. \
    You are given a text email body which might have some markdown \
    and you need to convert it to an HTML email body with simple, clear, compelling layout and design."

    subject_writer = Agent(name="email_subject_writer", instructions=subject_instructions, model="gpt-4o-mini")
    subject_tool = subject_writer.as_tool(tool_name="subject_writer", tool_description="Write a subject for a cold sales email")

    html_converter = Agent(name="html_email_body_converter", instructions=html_instructions, model="gpt-4o-mini")
    html_tool = html_converter.as_tool(
        tool_name="html_converter",
        tool_description="Convert a text email body to an HTML email body",
    )

    tools = [subject_tool, html_tool, send_email]

    agent_instructions = (
        "You are an email formatter and sender. You receive the body of an email to be sent. "
        "You first use the subject_writer tool to write a subject for the email, then use the html_converter tool "
        "to convert the body to HTML. Finally, you use the send_email tool to send the email with the subject and HTML body."
    )

    emailer_agent = Agent(name="emailer_agent", instructions=agent_instructions, tools=tools, model="gpt-4o-mini")
    return emailer_agent

class NameCheckOutput(BaseModel):
    name_included: bool
    name: str

def get_guard_rails_agent():
    instructions = "Check if user is including someone's name in what they want you to do."
    guard_rails_agent = Agent(
        name="guard_rails_agent",
        instructions=instructions,
        model="gpt-4o-mini",
        output_type=AgentOutputSchema(NameCheckOutput, strict_json_schema=False),
    )
    return guard_rails_agent

@input_guardrail
async def guardrail_against_name(context, agent, message):
    result = await Runner.run(get_guard_rails_agent(), message, context=context.context)
    is_name_in_message = result.final_output.name_included
    return GuardrailFunctionOutput(output_info={"name": result.final_output.name}, tripwire_triggered=is_name_in_message)


async def main():

    instructions1 = "You are a sales agent working for ComplAI, \
    a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
    You write professional, serious cold emails."

    instructions2 = "You are a humorous, engaging sales agent working for ComplAI, \
    a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
    You write witty, engaging cold emails that are likely to get a response."

    instructions3 = "You are a busy sales agent working for ComplAI, \
    a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
    You write concise, to the point cold emails."

    sales_agent1 = Agent(instructions=instructions1, name="professional_sales_agent", model="gpt-4o-mini")
    sales_agent2 = Agent(instructions=instructions2, name="engaging_sales_agent", model="gpt-4o-mini")
    sales_agent3 = Agent(instructions=instructions3, name="busy_sales_agent", model="gpt-4o-mini")

    message = "write a cold sales email"
    tool1 = sales_agent1.as_tool(tool_name="sales_agent1", tool_description=message)
    tool2 = sales_agent2.as_tool(tool_name="sales_agent2", tool_description=message)
    tool3 = sales_agent3.as_tool(tool_name="sales_agent3", tool_description=message)

    tools = [tool1, tool2, tool3]

    handoff_agent = email_manager_agent()
    handoffs = [handoff_agent]

    sales_manager_instructions = """
        You are a Sales Manager at ComplAI. Your goal is to find the single best cold sales email using the sales_agent tools.
        
        Follow these steps carefully:
        1. Generate Drafts: Use all three sales_agent tools to generate three different email drafts. Do not proceed until all three drafts are ready.
        
        2. Evaluate and Select: Review the drafts and choose the single best email using your judgment of which one is most effective.
        You can use the tools multiple times if you're not satisfied with the results from the first try.
        
        3. Handoff for Sending: Pass ONLY the winning email draft to the 'Email Manager' agent. The Email Manager will take care of formatting and sending.
        
        Crucial Rules:
        - You must use the sales agent tools to generate the drafts — do not write them yourself.
        - You must hand off exactly ONE email to the Email Manager — never more than one.
    """

    careful_sales_manager = Agent(name="sales_manager", instructions=sales_manager_instructions, tools=tools, model="gpt-4o-mini", handoffs=handoffs, input_guardrails=[guardrail_against_name])

    message = "Send a cold sales email addressed to 'Dear Sir/Madam'"

    with trace("Automate SDR"):
        result = await Runner.run(careful_sales_manager, input=message)

    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
