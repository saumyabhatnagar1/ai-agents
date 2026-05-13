import asyncio
import os

from agents import Agent, ModelSettings, Runner, WebSearchTool, function_tool, trace
from brevo import AsyncBrevo
from dotenv import load_dotenv
from pydantic import BaseModel
import gradio as gr

load_dotenv(override=True)

HOW_MANY_SEARCHES = 3

client = AsyncBrevo(api_key=os.environ["BREVO_API_KEY"])


@function_tool
async def send_email(subject: str, html: str, to_email: str):
    """Send an email to all sales prospects."""
    try:
        sender_email = os.environ["BREVO_SENDER_EMAIL"]
        sender_name = os.environ.get("BREVO_SENDER_NAME", "Research Report")
        response = await client.transactional_emails.with_raw_response.send_transac_email(
            subject=subject,
            to=[{"email": to_email}],
            html_content=html,
            sender={"email": sender_email, "name": sender_name},
        )
        return response.data
    except Exception as e:
        return f"Error sending email: {e}"


class WebSearchItem(BaseModel):
    reason: str
    "Your reasoning for why this search is important"
    query: str
    "The search term to use"

class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem]
    "The list of search terms to use"

class ReportData(BaseModel):
    short_summary: str
    "A short summary of 2-3 sentences of the report"

    markdown_report: str
    "The report in markdown format"

    follow_up_questions: list[str]
    "A list of follow-up questions that the reader may have based on the report"

class ResearchManager:
    def __init__(self):
        self.search_agent = self.search_agent()
        self.writer_agent = self.writer_agent()
        self.email_agent = self.email_agent()
        self.planner_agent = self.planner_agent()


    def planner_agent(self):
        INSTRUCTIONS = f"You are a helpful research assistant. Given a query, come up with a set of web searches \
        to perform to best answer the query. Output {HOW_MANY_SEARCHES} terms to query for."
        planner_agent = Agent(name="planner_agent", instructions=INSTRUCTIONS, model="gpt-4o-mini", output_type=WebSearchPlan)
        return planner_agent

    def email_agent(self):
        INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
            You will be provided with a detailed report. You should use your tool to send one email, providing the 
            report converted into clean, well presented HTML with an appropriate subject line."""
        return Agent(name="email_agent", instructions=INSTRUCTIONS, model="gpt-4o-mini", tools=[send_email])

    def writer_agent(self):
        INSTRUCTIONS = (
            "You are a senior researcher tasked with writing a cohesive report for a research query. "
            "You will be provided with the original query, and some initial research done by a research assistant.\n"
            "You should first come up with an outline for the report that describes the structure and "
            "flow of the report. Then, generate the report and return that as your final output.\n"
            "The final output should be in markdown format, and it should be lengthy and detailed. Aim "
            "for 5-10 pages of content, at least 1000 words."
        )
        return Agent(name="writer_agent", instructions=INSTRUCTIONS, model="gpt-4o-mini", output_type=ReportData)

    def search_agent(self):
        INSTRUCTIONS = (
            "You are a research assistant. Given a search term, you search the web for that term and "
            "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 "
            "words. Capture the main points. Write succintly, no need to have complete sentences or good "
            "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
            "essence and ignore any fluff. Do not include any additional commentary other than the summary itself."
        )
        return Agent(
                name="search_agent",
                instructions=INSTRUCTIONS, model="gpt-4o-mini",
                tools=[WebSearchTool(search_context_size="low")],
                model_settings=ModelSettings(tool_choice="required")
            )
    async def search(self, item: WebSearchItem) -> str | None:
        """Perform a search for the query"""
        input = f"Search term: {item.query}. \n Reason for search: {item.reason}"
        try:
            result = await Runner.run(self.search_agent, input)
            return str(result.final_output)
        except Exception as e:
            return None
    
    async def plan_searches(self, query: str):
        """Use the planner agent to plan which searches to perform to best answer the query"""
        print(f"Planning searches for query: {query}")
        result = await Runner.run(self.planner_agent, query)
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output

    async def perform_searches(self, search_plan: WebSearchPlan):
        """Call search() for each item in the search plan """
        print("Searching.....")
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        num_completed = 0
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Completed {num_completed} of {len(tasks)} searches")
        print(f"Completed searching")
        return results
    
    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """Write a report based on the query and search results"""
        print("Writing report.....")
        input = f"Query: {query}. \n Summarized Search results: {search_results}"
        try:
            result = await Runner.run(self.writer_agent, input)
            return result.final_output_as(ReportData)
        except Exception as e:
            return None
    async def deliver_report_via_email(self, report: ReportData, to_email: str):
        print("Sending email.....")
        input = f"Report: {report.markdown_report}. Email to send to: {to_email}"
        result = await Runner.run(self.email_agent, input)
        print(f"Email sent")
        return result.final_output
    
    async def run(self, query: str, to_email: str):
        with trace("Research Manager"):
            print("Starting research manager")
            yield "Planning searches..."
            search_plan = await self.plan_searches(query)
            yield "Searches planned, performing searches..."
            search_results = await self.perform_searches(search_plan)
            yield "Searches completed, writing report..."
            report = await self.write_report(query, search_results)
            yield "Report written, sending email..."
            await self.deliver_report_via_email(report, to_email)
            yield "Email sent"


async def main():

    research_manager = ResearchManager()
    async def run(query:str, to_email:str):
        async for step in research_manager.run(query, to_email):
            yield step
    
    with gr.Blocks(theme=gr.themes.Default(primary_hue="blue")) as demo:
        gr.Markdown("Deep Research Agent")
        query_textbox = gr.Textbox(label="What topic do you want to research?")
        email_textbox = gr.Textbox(label="Email to send the report to?")
        run_button = gr.Button("Run", variant="primary")
        report = gr.Markdown(label="Report")

        run_button.click(fn=run, inputs=[query_textbox, email_textbox], outputs=report)
        query_textbox.submit(fn=run, inputs=[query_textbox, email_textbox], outputs=report)

    demo.launch(inbrowser=True)



if __name__ == "__main__":
    asyncio.run(main())