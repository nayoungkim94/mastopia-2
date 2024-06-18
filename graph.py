import os
from langgraph.graph import StateGraph, END
from typing import Annotated, Any, Dict, List, Optional, Sequence, TypedDict
import operator
import functools
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_community.agent_toolkits.sql.prompt import SQL_FUNCTIONS_SUFFIX
from langchain.tools.retriever import create_retriever_tool
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser


from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)

import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]


class AgentState(TypedDict):
    # The annotation tells the graph that new messages will always
    # be added to the current states
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # The 'next' field indicates where to route to next
    next: str


class GraphModel:
    def __init__(self):
        self.members = ["Searcher", "Retriever"]
        self.llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-4-1106-preview", temperature=0)
        self.system_prompt = """You are an efficient supervisor tasked with managing a conversion between
            the following workers: {members}. Given the following user request, you
            should precisely determine which worker will act next. Each worker will
            skillfully perform a task and respond with thorough explanations of results
            and status. When finished, respond with FINISH. Use Searcher if user asks for a specific 
            document content. Use Retriever otherwise."""
        self.retriever_prompt = """Identify and retrieve only documents relevant to the query, and then filter
            these documents to extract key details and information. Order the events
            outlined in the documents chronologically, and construct a detailed timeline,
            including a specific date for when any anticipated terrorist action may occur.
            Make sure to include document IDs in your response."""
        
        
    
    def load_vector_retriever(self, file_path):
        # Load the saved _retriever object from file
        saved_db = FAISS.load_local(file_path, embeddings=OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY), allow_dangerous_deserialization=True)
        _retriever = saved_db.as_retriever()
        return _retriever


    def agent_node(self, state, agent, name):
        result = agent.invoke(state)
        return {"messages": [HumanMessage(content=result["output"], name=name)]}

    
    def create_agent_sql(self):
        db_path = os.path.join(os.getcwd(), "dataset", "vast.db")
        db = SQLDatabase.from_uri(f"sqlite:///{db_path}")

        toolkit = SQLDatabaseToolkit(db=db, llm=self.llm)
        context = toolkit.get_context()
        tools = toolkit.get_tools()
        
        instruction = """You are an SQL agent tasked with analyzing and querying the VAST database to extract relevant information. Given document ids, which are 'doc_id' column in vastable, find relevant rows."""

        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=instruction),
                HumanMessagePromptTemplate.from_template("{input} Return the rows from the vastable where the doc_id is in the provided list of document ids."),
                AIMessage(content=SQL_FUNCTIONS_SUFFIX),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        prompt = prompt.partial(input="{input}", **context)

        agent = create_openai_tools_agent(self.llm, tools, prompt)
        executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

        return executor

    def create_agent(self, tools: list, system_prompt: str):
        # Each worker node will be given a name and some tools.
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    system_prompt,
                ),
                MessagesPlaceholder(variable_name="messages"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        agent = create_openai_tools_agent(self.llm, tools, prompt)
        executor = AgentExecutor(agent=agent, tools=tools)
        return executor


    def create_workflow(self):
        workflow = StateGraph(AgentState)
        retriever_path = "./dataset/faiss_index"
        retriever = self.load_vector_retriever(retriever_path)
        retriever_tool = create_retriever_tool(
            retriever,
            "search_vast",
            "Searches and returns excerpts from the VAST 2011 Mini-Challenge 3 dataset.",
        )
        retrieval_agent = self.create_agent(
            [retriever_tool],
            self.retriever_prompt
        )
        retrieval_node = functools.partial(self.agent_node, agent=retrieval_agent, name="Retriever")

        sql_agent = self.create_agent_sql()
        sql_node = functools.partial(self.agent_node, agent=sql_agent, name="Searcher")



        options = self.members # No FINISH option for supervisor
        # options = ["FINISH"] + self.members

        # Using openai function calling can make output parsing easier for us
        function_def = {
            "name": "route",
            "description": "Select the next role.",
            "parameters": {
                "title": "routeSchema",
                "type": "object",
                "properties": {
                    "next": {
                        "title": "Next",
                        "anyOf": [
                            {"enum": options},
                        ],
                    }
                },
                "required": ["next"],
            },
        }
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                MessagesPlaceholder(variable_name="messages"),
                (
                    "system",
                    """Given the conversation above, who should act next?
                    Or should we FINISH? Select one of: {options}.
                    FINISH only if you already visited one of the {members}""",
                ),
            ]
        ).partial(options=str(options), members=", ".join(self.members))

        supervisor_chain = (
            prompt
            | self.llm.bind_functions(functions=[function_def], function_call="route")
            | JsonOutputFunctionsParser()
        )
        workflow.add_node("Retriever", retrieval_node)
        workflow.add_node("Searcher", sql_node)        
        workflow.add_node("Supervisor", supervisor_chain)

        conditional_map = {"FINISH" : END}
        for member in self.members:
            # We want our workers to ALWAYS "report back" to the supervisor when done
            conditional_map[member] = member
            # workflow.add_edge(member, "Supervisor")
        workflow.add_conditional_edges("Supervisor", lambda x: x["next"], conditional_map)
        workflow.set_entry_point("Supervisor")
        return workflow


    def execute(self, input_message, recursion_limit=5, max_iterations=1):
        workflow = self.create_workflow()
        graph = workflow.compile()
        return graph.stream(input_message,
                                 {"max_iterations": max_iterations})
