from QueryGenerator.queryGenerator import QueryGenerator
from QueryMemory.VectorStore import VectorStore
from rich import print
import json

def printQueryAndResult(result: dict):
    print(f"Input user prompt:\n[cyan]{result['query']}[/cyan]")

    print(f"\nGenerated cypher query:\n[green]{result['intermediate_steps'][0]['query']}[/green]")

    print(f"\nQuery result:\n[green]{result['intermediate_steps'][1]['context']}[/green]")

    print(f"\nLLM output based on query result:\n[green]{result['result']}[/green]\n")

def runExample(example: dict, qg: QueryGenerator, vs: VectorStore):
    prompt = example["prompt"]
    res = qg.generateAndExecuteCypherQuery(user_query=prompt)

    printQueryAndResult(res)

    results = []
    for item in example["memoryItems"]:
        if len(item["prompt"]) == 0: continue

        vs.addExampleToMemory(item["prompt"], item["query"])

        few_shot_examples = vs.retrieveExamples(user_query=prompt)
        
        try:
            res = qg.generateAndExecuteCypherQuery(user_query=prompt, few_shot_examples=few_shot_examples)
            results.append(res)
        except: 
            results.append(None)

        
        printQueryAndResult(res)

if __name__ == "__main__":
    with open("Evaluation/evaluationExamples.json", "r") as f:
        evaluation_data = json.load(f)

    for language_model in evaluation_data["languageModels"]:
        qg = QueryGenerator(chat_model=language_model["model"], provider=language_model["provider"])
        print(f"Using language model: {language_model["model"]}")

        for embedding_model in evaluation_data["embeddingModels"]:
            for idx, example in enumerate(evaluation_data["evaluationExamples"]):
                vs = VectorStore(embedding_model=embedding_model["model"], is_open_ai=embedding_model["is_open_ai"] , database_folder=f"Evaluation/VectorDB/lang_{language_model}/prompt_{idx+1}", evaluation=True)
                print(f"Using embedding model: {embedding_model["model"]}")
                runExample(example=example, qg=qg, vs=vs)