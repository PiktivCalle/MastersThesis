from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
import os
import json
from dotenv import load_dotenv

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from langchain_chroma import Chroma

class VectorStore:
    def __init__(self, embedding_model: str = "ollama"):
        load_dotenv()

        self.embedding_model = embedding_model
        
        self.embedding = self.createEmbeddingModel(self.embedding_model)
        
        database_path = os.path.join('./VectorDB', f'{self.embedding_model}_embedding/')
        self.query_memory = Chroma(
            embedding_function=self.embedding,
            persist_directory=database_path
        )

        if len(self.query_memory._collection.get(include=['embeddings'])['embeddings']) == 0:
            self.addInitialExamplesToMemory()

        self.combineDifferentEmbeddingModelMemoryItems()

        print("==========Loaded ",database_path," Memory, Now the database has ", len(
            self.query_memory._collection.get(include=['embeddings'])['embeddings']), " items.==========")

    def createEmbeddingModel(self, embedding_model: str):
        if embedding_model == "ollama":
            return OllamaEmbeddings(
                model="mxbai-embed-large",
                base_url=os.environ.get("OLLAMA_URI")
            )
        elif embedding_model == "openAi":
            return OpenAIEmbeddings(
                model="text-embedding-3-large"
            )
        else:
            raise ValueError("Unknown embedding model, valid models are: ollama or openAi")

    def addInitialExamplesToMemory(self):
        with open("QueryMemory/initialExamples.json", 'r') as f:
            initial_few_shot_examples = json.load(f)
        
        prompts = []
        queries = []
        for example in initial_few_shot_examples["few_shot_examples"]:
            prompts.append(example["prompt"])
            queries.append({"prompt": example["prompt"], "query": example["query"]})
        self.query_memory.add_texts(texts=prompts, metadatas=queries)

    def combineDifferentEmbeddingModelMemoryItems(self):
        other_embedding_model = "openAi" if self.embedding_model == "ollama" else "ollama"
        other_memory_database_path = os.path.join('./VectorDB', f'{other_embedding_model}_embedding/')
        other_query_memory = Chroma(
            embedding_function=self.createEmbeddingModel(other_embedding_model),
            persist_directory=other_memory_database_path
        )
        other_documents = other_query_memory._collection.get(
            include=['metadatas']
        )
        
        current_documents = self.query_memory._collection.get(
            include=['metadatas']
        )

        for i in range(0, len(other_documents['metadatas'])):
            if (metadata := other_documents['metadatas'][i]) not in current_documents['metadatas']:
                self.addExampleToMemory(metadata["prompt"], metadata["query"])

    def addExampleToMemory(self, prompt: str, query: str):
        self.query_memory.add_texts(texts=[prompt], metadatas=[{"prompt": prompt, "query": query}])
        
        print("Add a memory item. Now the database has ", len(
                self.query_memory._collection.get(include=['embeddings'])['embeddings']), " items.")


    def retrieveExamples(self, user_query: str, k: int = 5):
        similarity_results = self.query_memory.similarity_search_with_score(
            query=user_query,
            k=k
        )

        fewshot_results = []
        for idx in range(0, len(similarity_results)):
            fewshot_results.append(similarity_results[idx][0].metadata)
            
        return fewshot_results

    def combineMemory(self, other_memory: Chroma):
        pass


def main():
    vs = VectorStore()

if __name__ == "__main__":
    main()