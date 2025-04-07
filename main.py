from QueryGenerator.queryGenerator import QueryGenerator
from QueryMemory.VectorStore import VectorStore
from rich import print

REFLECTION = True

def printQueryAndResult(result: dict):
    print(f"Input user prompt:\n[cyan]{result['query']}[/cyan]")

    print(f"\nGenerated cypher query:\n[green]{result['intermediate_steps'][0]['query']}[/green]")

    print(f"\nQuery result:\n[green]{result['intermediate_steps'][1]['context']}[/green]")

    print(f"\nLLM output based on query result:\n[green]{result['result']}[/green]\n")

def main():
    vc = VectorStore(embedding_model="text-embedding-3-large", is_open_ai=True)
    qg = QueryGenerator(chat_model="gpt-4o-mini", is_open_ai=True)

    user_query = "How long would it take me to drive on every unique road if I drive 5mph if the roads are defined in meters?"
    
    examples = vc.retrieveExamples(user_query)
    #print(examples)
    result = qg.generateAndExecuteCypherQuery(user_query, few_shot_examples=examples)

    printQueryAndResult(result)
    
    if REFLECTION:
        choice = input("Do you want to add this new memory item to update memory module? (Y/N):").strip().upper()
        
        if choice == 'Y':
            vc.addExampleToMemory(prompt=result['query'], query=result['intermediate_steps'][0]['query'])
        else:
            print("[blue]Ignore this new memory item[/blue]\n")

if __name__ == '__main__':
    main()