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

    for item in example["memoryItems"]:
        if len(item["prompt"]) == 0: continue

        vs.addExampleToMemory(item["prompt"], item["query"])

        few_shot_examples = vs.retrieveExamples(user_query=prompt)
        res = qg.generateAndExecuteCypherQuery(user_query=prompt, few_shot_examples=few_shot_examples)

        printQueryAndResult(res)

if __name__ == "__main__":
    with open("Evaluation/evaluationExamples.json", "r") as f:
        evaluation_data = json.load(f)

    for language_model in evaluation_data["languageModels"]:
        qg = QueryGenerator(chat_model=language_model["model"], is_open_ai=language_model["is_open_ai"])

        for embedding_model in evaluation_data["embeddingModels"]:
            vs = VectorStore(embedding_model=embedding_model["model"], is_open_ai=["is_open_ai"] , database_folder="Evaluation/VectorDB", evaluation=True)

            for example in evaluation_data["evaluationExamples"]:
                runExample(example=example, qg=qg, vs=vs)