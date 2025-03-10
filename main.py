from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_openai import ChatOpenAI
from langchain.prompts.prompt import PromptTemplate

import os
from dotenv import load_dotenv

CYPHER_GENERATION_TEMPLATE = """
Task: Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Schema:
{schema}
Schema attribute clarification:
Road:
    id - Unique id of the road,
    length - Length of the road,
    initialHeading - Initial global direction of the road, value in radians,
    finalHeading - Final global direction of the road, value in radians,
    isJunction - -1 if the road is not part of a junction, otherwise, id of the junction
Lane:
    id - Id of the lane. Positive ID:s to the left of the center line, negative ID:s to the right of the center line. An ID of 1 means that it is the first lane to the left of the center line,
    type - Either "driving" meaning the lane is for driving, "walking" meaning that the lane is a sidewalk or "shoulder" meaning the lane is on the shoulder of the road
Object:
    id - Unique id of the object,
    name - Name of the object. "Speed_30" means that it is a sign indicating a speed limit of 30,
    type - Do not use this to generate a prompt,
    orientation - Orientation of the object. Either "opposite" when the object is meant for traffic against the main driving direction or "along" meaning the object is meant for traffic that is driving along the main driving direction
Signal:
    id - Unique id of the signal,
    name - Name of the signal. "Signal_3Light_Post01" means that it is a traffic light,
    type - Type of the signal. No significant meaning,
    orientation - Orientation of the signal. Either "opposite" when the signal is meant for traffic against the main driving direction or "along" meaning the signal is meant for traffic that is driving along the main driving direction
Schema relationship clarification:
(:Road)-[:HAS_LANE]->(:Lane):
    side - Either "left" meaning that the lane is on the left side of the road's center line or "right" meaning that the lane is on the right side of the road's center line
(:Lane)-[:PRECEDES]->(Lane):
    direction - Either "straight" meaning that the next lane is straight ahead, "left" meaning that the next lane requires turning left, "right" meaning that the next lane requires turning right or "u-turn" meaning that the next lane requires doing a u-turn
(:Road)-[:HAS_OBJECT]->(:Object):
    atDistance - The distance at which the object appears, counted from the start of the road
(:Road)-[:HAS_SIGNAL]->(:Signal):
    atDistance - The distance at which the object appears, counted from the start of the road

Cypher examples:
# How many roads are there in the map?
MATCH (r:Road)
RETURN count(r) as roads

# How many roads contain multiple lanes?
MATCH (r:Road)-[:HAS_LANE]->(l:Lane)
WITH r, COUNT(l) AS lane_count
WHERE lane_count > 1
RETURN COUNT(r) AS roads_with_multiple_lanes;

# Return the names of the signs
MATCH (o:Object)
RETURN DISTINCT o.name AS sign_name

Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.

The question is:
{question}
"""
CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
)

def main():
    load_dotenv()

    roadGraph = Neo4jGraph(url=os.environ.get("NEO4J_URI"), username=os.environ.get("NEO4J_USER"), password=os.environ.get("NEO4J_PASSWORD"), database="neo4j")

    llama = 'llama3.2-vision:latest'
    gpt = "gpt-4o-mini"
    llm = ChatOpenAI(
        openai_api_key="ollama",
        temperature=0,
        openai_api_base=os.environ.get("OLLAMA_URI"),
        model=llama
    )
    
    try:
        chain = GraphCypherQAChain.from_llm(
            llm=llm, graph=roadGraph, verbose=True, allow_dangerous_requests=True,
            cypher_prompt=CYPHER_GENERATION_PROMPT
        )

        response = chain.invoke("How many roads have a left turn but not a right one? The direction property of the PRECEDES label can be used for this")
        print(f"{response['result']}")
    except Exception as e:
        print(f"GraphCypherQAChain failed: {e}")
    
if __name__ == '__main__':
    main()