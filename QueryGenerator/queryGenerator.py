from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate, FewShotPromptTemplate

import os
from dotenv import load_dotenv


SYSTEM_MESSAGE = """
You are an AI specialized in generating Cypher queries for Neo4j.
Always return a correct Cypher query based on the user's question.

### Neo4j Schema:
- **Node Labels and Properties:**
  - `(:Road)`: {{ `length`: FLOAT, `finalHeading`: FLOAT, `initialHeading`: FLOAT, `junctionId`: STRING ('-1' if not a junction), `id`: STRING }}
  - `(:Lane)`: {{ `travelDirection`: STRING, `lane_type`: STRING, `id`: STRING }}
  - `(:Signal)`: {{ `name`: STRING, `id`: STRING, `orientation`: STRING, `signal_type`: STRING }}
  - `(:Object)`: {{ `object_type`: STRING, `id`: STRING, `orientation`: STRING, `name`: STRING }}

- **Relationships and Properties:**
  - `(:Road)-[:HAS_LANE {{side: STRING}}]->(:Lane)`
  - `(:Lane)-[:PRECEDES {{direction: STRING}}]->(:Lane)`
  - `(:Road)-[:HAS_OBJECT]->(:Object)`
  - `(:Road)-[:HAS_SIGNAL]->(:Signal)`
  - `(:Lane)-[:CONNECTS_TO]->(:Lane)`

### Query Guidelines:
- Use correct **property names** and **relationship directions**.
- Never use a **property name** which is not in the schema
- Always filter by **node properties** when searching.
- When using relationships, include their properties when needed.
"""

class QueryGenerator:
    def __init__(self, chat_model: str = "llama3.2-vision:latest", is_open_ai: bool = False):
        load_dotenv(override=True)

        self.roadGraph = Neo4jGraph(url=os.environ.get("NEO4J_URI"), username=os.environ.get("NEO4J_USER"), password=os.environ.get("NEO4J_PASSWORD"), database="neo4j")


        if is_open_ai:
            self.llm = ChatOpenAI(
                temperature=0,
                model=chat_model
            )   
        else:  
            self.llm = ChatOpenAI(
                openai_api_key="ollama",
                temperature=0,
                openai_api_base=os.environ.get("OLLAMA_CHAT_URI"),
                model=chat_model
            )
    
    def generateAndExecuteCypherQuery(self, user_query: str, few_shot_examples: list[dict] = None):
        if few_shot_examples:
            single_shot_template = PromptTemplate(
                input_variables=["prompt", "query"],
                template="USER: {prompt}\nCypher: {query}\n"
            )

            few_shot_template = FewShotPromptTemplate(
                examples=few_shot_examples,
                example_prompt=single_shot_template,
                suffix="\n\n### Current question:\n\nUSER: {question}\nCypher: ",
                input_variables=["question"],
                prefix=SYSTEM_MESSAGE + "\n\n### Example Queries:\n\n"
            )
            prompt_template = few_shot_template  
        else: 
            no_shot_template = PromptTemplate(
                input_variables=["question"],
                template=SYSTEM_MESSAGE + "\n\nUSER: {question}\nCypher: "
            )
            prompt_template = no_shot_template

        chain = GraphCypherQAChain.from_llm(
                llm=self.llm, graph=self.roadGraph, allow_dangerous_requests=True,
                cypher_prompt=prompt_template, return_intermediate_steps=True
            ) 

        return chain.invoke(user_query)