from QueryGenerator.queryGenerator import QueryGenerator
from QueryMemory.VectorStore import VectorStore
from rich import print

REFLECTION = False

languageModels= [
        {
            "model": "llama3.3:70b",
            "provider": "ollama"
        },
        {
            "model": "aravhawk/llama4",
            "provider": "ollama"
        },
        {
            "model": "deepseek-r1:8b",
            "provider": "ollama"
        },
        {
            "model": "deepseek-r1:1.5b",
            "provider": "ollama"
        },
        {
            "model": "phi4",
            "provider": "ollama"
        },
        {
            "model": "gemma3:27b",
            "provider": "ollama"
        },
        {
            "model": "tinyllama",
            "provider": "ollama"
        },
        {
            "model": "gpt-4o-mini",
            "provider": "openAi"
        },
        {
            "model": "gpt-4o",
            "provider": "openAi"
        },
        {
            "model": "gemini-2.5-pro-exp-03-25",
            "provider": "google"
        },
        {
            "model": "claude-3-7-sonnet-20250219",
            "provider": "anthropic"
        }
    ]

def printQueryAndResult(result: dict):
    print(f"Input user prompt:\n[cyan]{result['query']}[/cyan]")

    print(f"\nGenerated cypher query:\n[green]{result['intermediate_steps'][0]['query']}[/green]")

    print(f"\nQuery result:\n[green]{result['intermediate_steps'][1]['context']}[/green]")

    print(f"\nLLM output based on query result:\n[green]{result['result']}[/green]\n")

def main():
    vc = VectorStore(embedding_model="nomic-embed-text", is_open_ai=False)

    idx = -3
    qg = QueryGenerator(chat_model=languageModels[idx]["model"], provider=languageModels[idx]["provider"])

    user_query = "How many three way intersections are there on the map?"
    
    examples = vc.retrieveExamples(user_query)
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