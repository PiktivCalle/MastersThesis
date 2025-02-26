from MapParsing.mapStructure import create_graph
from MapParsing.graphDataBase import insertGraphIntoDB
import glob
import os
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain

def main():
    opendrive_files = glob.glob(os.path.join("maps", "town1.xodr"))

    #mapDict = create_graph(opendrive_files[0])
    #insertGraphIntoDB(mapDict)
    
    #
    #tmp = nx.to_dict_of_dicts(roads)
    ##print(roads.nodes[2])
    #print(junctions)

    client = Client(host="192.168.100.112:11434")
    llama = 'llama3.2-vision:latest'
    deep = 'deepseek-r1'
    res = client.generate(model=llama, prompt=f"How is your day?")
    print(res['response'])

if __name__ == '__main__':
    main()