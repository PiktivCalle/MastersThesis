from QueryGenerator.queryGenerator import QueryGenerator
from QueryMemory.VectorStore import VectorStore
from rich import print
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import PreservedScalarString
import re
import os
  
def printQueryAndResult(result: dict):
    print(f"Input user prompt:\n[cyan]{result['query']}[/cyan]")

    print(f"\nGenerated cypher query:\n[green]{result['intermediate_steps'][0]['query']}[/green]")

    print(f"\nQuery result:\n[green]{result['intermediate_steps'][1]['context']}[/green]")

    print(f"\nLLM output based on query result:\n[green]{result['result']}[/green]\n")

def remove_cypher_comments(query: str) -> str:
    """
    Remove all ‘// …’ style comments (up to end of line),
    and collapse any blank lines left behind.
    """
    # 1) Remove // comments
    no_comments = re.sub(r'//[^\n]*', '', query)
    # 2) Collapse multiple blank lines
    no_comments = re.sub(r'\n\s*\n+', '\n', no_comments)
    return no_comments.strip()

def simple_format(query: str, indent: int = 6) -> str:
    query = query.replace('cypher', '')
    query = remove_cypher_comments(query)
    # Add newline before MATCH, WHERE, RETURN, CALL, WITH, AND
    clauses = ["MATCH", "WITH", "WHERE", "AND", "RETURN"]
    # Build regex pattern to split on these, capturing the keyword
    pattern = re.compile(r'(?i)\b(' + '|'.join(clauses) + r')\b')
    
    # Split into segments: e.g. ["", "MATCH", " (n)...", "WHERE", " n.prop...", ...]
    parts = pattern.split(query)
    
    # Reassemble with desired formatting
    lines = []
    for i in range(1, len(parts), 2):
        kw = parts[i].upper()
        body = parts[i+1].strip()
        
        # Remove trailing semicolon from body if it's the last clause
        if body.endswith(';'):
            body = body[:-1].rstrip()
            is_last = True
        else:
            is_last = False
        
        # Clause keyword on its own line
        lines.append(kw)
        # Indented body lines (could be multi-part, split on comma or newline)
        for segment in re.split(r'\n|,', body):
            seg = segment.strip()
            if not seg:
                continue
            # Add comma back if it was split on comma
            if body.find(segment + ",") != -1:
                seg += ","
            lines.append(" " * indent + seg)
        
        # If this clause had the semicolon, append it to the last line
        if is_last:
            lines[-1] = lines[-1].rstrip() + ";"
    
    return "\n".join(lines)


def runExample(qg: QueryGenerator, prompt, few_shot_examples=None):
    try:
        res = qg.generateAndExecuteCypherQuery(user_query=prompt, few_shot_examples=few_shot_examples)
        printQueryAndResult(res)
        
        res['intermediate_steps'][0]['query'] = PreservedScalarString(simple_format(res['intermediate_steps'][0]['query']))
        del res["query"]
        return res
    except: 
        return {'result': 'None'}

def runExamples(example: dict, qg: QueryGenerator, vs: VectorStore):
    prompt = example["prompt"]
    results = []

    print(f"Running example prompt:\n{prompt}")

    res = runExample(qg, prompt)
    results.append(res)
    few_shot_examples = []
    for item in example["memoryItems"]:
        if len(item["prompt"]) == 0: continue

        vs.addExampleToMemory(item["prompt"], item["query"])
        few_shot_examples = vs.retrieveExamples(user_query=prompt)

        res = runExample(qg, prompt, few_shot_examples)
        results.append(res)
    
    return results

if __name__ == "__main__":
    yaml = YAML()
    with open("Evaluation/evaluationExamples.yaml", "r") as f:
        evaluation_data = yaml.load(f)

    results = [{}, {}, {}, {}]
    for language_model in evaluation_data["languageModels"]:
        qg = QueryGenerator(chat_model=language_model["model"], provider=language_model["provider"])
        print(f"Using language model: {language_model['model']}")
        for embedding_model in evaluation_data["embeddingModels"]:
            for idx, example in enumerate(evaluation_data["evaluationExamples"]):
                if idx != 0: continue

                if language_model['model'] not in results[idx].keys():
                    results[idx][language_model['model']] = {}

                if embedding_model['model'] not in results[idx][language_model['model']].keys():
                    results[idx][language_model['model']][embedding_model['model']] = []


                vs = VectorStore(embedding_model=embedding_model["model"], is_open_ai=embedding_model["is_open_ai"] , database_folder=f"Evaluation/VectorDB/lang_{language_model['model']}/prompt_{idx+1}", evaluation=True)
                print(f"Using embedding model: {embedding_model['model']}")
                res = runExamples(example=example, qg=qg, vs=vs)

                results[idx][language_model['model']][embedding_model['model']].append({
                    "results": res
                })

                path = os.path.join("./Evaluation/results", f"prompt-{idx+1}.yaml")
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f:
                    yaml.dump(results[idx], f)