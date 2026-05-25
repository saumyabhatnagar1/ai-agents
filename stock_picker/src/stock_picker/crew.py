from tabnanny import verbose
from crewai import Agent, Crew, Process, Task, tools
from crewai.memory import storage
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from pydantic import BaseModel, Field
from typing import List
from crewai_tools import SerperDevTool
from .tools.custom_tool import PushNotificationTool
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

class TrendingCompany(BaseModel):
    """A company in the news getting attention"""
    name: str = Field(..., description="the name of the company")
    ticker: str = Field(..., description="the ticker symbol of the company")
    reason: str = Field(..., description="the reason why the company is trending") 

class TrendingCompanies(BaseModel):
    """A list of trending companies"""
    companies: List[TrendingCompany] = Field(..., description="the list of trending companies")

class TrendingCompanyResearch(BaseModel):
    """Detailed research of the company"""
    name: str = Field(..., description="the name of the company")
    market_position: str = Field(..., description="the current market position of the company")
    future_potential: str = Field(..., description="the future potential of the company")
    investment_potential: str = Field(..., description="the investment potential and sustainability of the company")

class TrendingCompaniesResearch(BaseModel):
    """Detailed research of the companies"""
    companies: List[TrendingCompanyResearch] = Field(..., description="the list of detailed research of the companies")

@CrewBase
class StockPicker():
    """StockPicker crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def trending_company_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['trending_company_finder'], # type: ignore[index]
            verbose=True,
            tools=[SerperDevTool()],
            memory=True,
        )
    
    @agent
    def financial_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['financial_researcher'], # type: ignore[index]
            verbose=True,
            tools=[SerperDevTool()]
        )
    
    @agent
    def stock_picker(self) -> Agent:
        return Agent(
            config=self.agents_config['stock_picker'], # type: ignore[index]
            verbose=True,
            tools=[PushNotificationTool()],
            memory=True,
        )
    
    @task
    def find_trending_companies(self) -> Task:
        return Task(
            config=self.tasks_config['find_trending_companies'], # type: ignore[index]
            output_pydantic=TrendingCompanies
        )
    
    @task
    def research_trending_companies(self) -> Task:
        return Task(
            config=self.tasks_config['research_trending_companies'], # type: ignore[index]
            output_pydantic=TrendingCompaniesResearch
        )
    
    @task
    def pick_best_company(self) -> Task:
        return Task(
            config=self.tasks_config['pick_best_company'], # type: ignore[index]
        )

    @crew 
    def crew(self) -> Crew:
        """Creates the StockPicker crew"""

        manager = Agent(
            config=self.agents_config['manager'], # type: ignore[index]
            allow_delegation=True,
        )

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            verbose=True,
            manager_agent=manager,
            memory=True,
            embedder={
                "provider": "openai",
                "config": {
                    "model_name": "text-embedding-3-small",
                    "api_key": os.getenv("OPENAI_API_KEY")
                }
            },
        )
    