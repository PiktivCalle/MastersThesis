import glob
import os
from mapStructure import create_graph
from graphDataBase import insertGraphIntoDB
import json

def main():
    mapDict = create_graph("town1.xodr")

    with open("tmp", "w") as fp:
        fp.write(json.dumps(mapDict, indent=2)) 

    insertGraphIntoDB(mapDict)

if __name__ == '__main__':
    main()