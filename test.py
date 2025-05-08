from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import json

# 1. Decomposition with LLM
decomp_prompt = PromptTemplate(
    input_variables=["user_query"],
    template="""
Break the following question into its atomic sub-questions. 
Output a JSON list of objects with keys:
  - text: the sub-question

Example output:
[
  {{"text":"How to match roads to lanes?"}},
  ...
]

Question:
{user_query}
"""
)
llm = ChatOpenAI(model="gpt-4o-mini")

chain = decomp_prompt | llm

raw_fragments = chain.invoke("Give me a route which is between 400 and 500 meters long, involves at least two turns, minimum of one being a left turn. The route should have at least 1 traffic sign which changes the speed on the road. Return the ids of the roads in the route.")
print(raw_fragments)