import glob
import os
from mapStructure import create_graph
from graphDataBase import insertGraphIntoDB

def main():
    mapDict = create_graph("town1.xodr")
    insertGraphIntoDB(mapDict)

if __name__ == '__main__':
    main()