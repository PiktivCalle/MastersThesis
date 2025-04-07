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
    def __init__(self, embedding_model: str, is_open_ai = False, database_folder: str = "QueryMemory/VectorDB", evaluation: bool = False):
        load_dotenv()

        self.embedding_model = embedding_model
        self.is_open_ai = is_open_ai

        self.embedding = self.createEmbeddingModel()
        self.database_folder = database_folder

        database_path = os.path.join(f'./{database_folder}', f'{self.embedding_model}/')
        self.query_memory = Chroma(
            embedding_function=self.embedding,
            persist_directory=database_path
        )

        if not evaluation:
            self.addInitialExamplesToMemory()
            self.combineDifferentEmbeddingModelMemoryItems()

        print("\n==========Loaded ",database_path," memory. The database has ", len(
            self.query_memory._collection.get(include=['embeddings'])['embeddings']), " items.==========\n")

    def createEmbeddingModel(self):
        if self.is_open_ai:
            return OpenAIEmbeddings(
                model=self.embedding_model
            )
        
        return OllamaEmbeddings(
            model=self.embedding_model,
            base_url=os.environ.get("OLLAMA_URI")
        )

    def addInitialExamplesToMemory(self):
        with open("QueryMemory/initialExamples.json", 'r') as f:
            initial_few_shot_examples = json.load(f)

        current_documents = self.query_memory._collection.get(
            include=['metadatas']
        )
        
        prompts = []
        metadatas = []
        for example in initial_few_shot_examples["few_shot_examples"]:
            query = example["query"]
            query = query.replace("{", "{{")
            query = query.replace("}", "}}")
            metadata = {"prompt": example["prompt"], "query": query}
            if metadata not in current_documents["metadatas"]:
                prompts.append(example["prompt"])
                metadatas.append(metadata)

        if( len(prompts) > 0 ):
            self.query_memory.add_texts(texts=prompts, metadatas=metadatas)

    def combineDifferentEmbeddingModelMemoryItems(self):
        embedding_models = os.listdir(path=self.database_folder)

        for model in embedding_models:
            if model == self.embedding_model: continue

            other_database_path = os.path.join(f'./{self.database_folder}', f'{model}/')
            other_query_memory = Chroma(
                embedding_function=self.createEmbeddingModel(model),
                persist_directory=other_database_path
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
        query = query.replace("{", "{{")
        query = query.replace("}", "}}")
        self.query_memory.add_texts(texts=[prompt], metadatas=[{"prompt": prompt, "query": query}])
        
        print("Added a memory item. Now the database has ", len(
                self.query_memory._collection.get(include=['embeddings'])['embeddings']), " items.\n")


    def retrieveExamples(self, user_query: str, k: int = 5, maximum_accepted_similarity_score: float = 0.8):
        similarity_results = self.query_memory.similarity_search_with_score(
            query=user_query,
            k=k
        )

        fewshot_results = []
        for idx in range(0, len(similarity_results)):
            if similarity_results[idx][-1] > maximum_accepted_similarity_score: continue

            fewshot_results.append(similarity_results[idx][0].metadata)
            
        return fewshot_results