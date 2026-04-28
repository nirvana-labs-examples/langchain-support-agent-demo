"""
LangChain agent with a retriever tool for answering support questions.

Uses OpenAI function calling (not ReAct string parsing) for reliability.
verbose=True is intentional — watching tool calls happen in real time is
a core part of the demo experience.
"""

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools.retriever import create_retriever_tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import Document

from app.config import settings
from app.retriever import get_retriever

SYSTEM_PROMPT = """\
You are a knowledgeable and empathetic AI support agent for Nirvana Cloud,
a cloud infrastructure company. Your job is to help customers and support
representatives by:

1. Answering questions about Nirvana Cloud products, policies, and procedures.
2. Drafting professional, friendly support replies.
3. Summarizing patterns from support tickets.
4. Recommending relevant help articles.
5. Determining if a customer is eligible for escalation.

Always use the `search_support_docs` tool to retrieve relevant information
before answering. Cite your sources by mentioning the document name.
Be concise, accurate, and helpful.

If you cannot find relevant information in the knowledge base, say so clearly
rather than guessing.
"""

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])


def build_agent() -> AgentExecutor:
    llm = ChatOpenAI(
        model=settings.agent_model,
        temperature=0,
        openai_api_key=settings.openai_api_key,
    )

    retriever_tool = create_retriever_tool(
        retriever=get_retriever(),
        name="search_support_docs",
        description=(
            "Search the Nirvana Cloud knowledge base for information about "
            "billing, refunds, VM management, escalation policies, onboarding, "
            "and support tickets. Use this tool for any question about Nirvana Cloud."
        ),
    )

    agent = create_openai_functions_agent(
        llm=llm,
        tools=[retriever_tool],
        prompt=PROMPT,
    )

    return AgentExecutor(
        agent=agent,
        tools=[retriever_tool],
        verbose=True,
        max_iterations=5,
        return_intermediate_steps=True,
    )


def extract_sources(intermediate_steps: list) -> list[str]:
    """Extract unique source document names from agent intermediate steps."""
    sources: set[str] = set()
    for _, tool_output in intermediate_steps:
        if isinstance(tool_output, list):
            for doc in tool_output:
                if isinstance(doc, Document) and "source" in doc.metadata:
                    sources.add(doc.metadata["source"])
    return sorted(sources)


def run_agent(question: str) -> dict:
    """
    Run the agent on a question and return a structured response.

    Returns:
        {
            "answer": str,
            "sources": list[str],
            "intermediate_steps_count": int,
        }
    """
    result = build_agent().invoke({"input": question})
    sources = extract_sources(result.get("intermediate_steps", []))
    return {
        "answer": result["output"],
        "sources": sources,
        "intermediate_steps_count": len(result.get("intermediate_steps", [])),
    }
