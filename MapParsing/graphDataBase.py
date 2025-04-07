from neo4j import GraphDatabase, exceptions
from dotenv import load_dotenv
import os

class RoadCreation:
    def __init__(self, database):
        load_dotenv()
        self.driver =  GraphDatabase.driver(uri=os.environ.get("NEO4J_URI"), auth=(os.environ.get("NEO4J_USER"), os.environ.get("NEO4J_PASSWORD")))
        self.database = database

    def createRoads(self, roadData_):
        query = """
            UNWIND COALESCE($data, []) AS entry
            CREATE ( :Road {id: entry.id, length: entry.length, initialHeading: entry.initial_heading, finalHeading: entry.final_heading, isJunction: entry.is_junction} )
        """
        
        try:
            self.driver.execute_query(
                query,
                data=roadData_,
                database_= self.database
            )
        except exceptions.Neo4jError as e:
            print(f"Creating road raised an error: \n{e}\n")
        except Exception as e:
            print(f"Adding preceding lane relationship raised an error: \n{e}\n")
            
    def createLanes(self, laneData_):
        query = """
            UNWIND COALESCE($data, []) AS entry
            MATCH (r:Road) WHERE r.id = entry.roadId
            CREATE ( l:Lane {id: entry.id, lane_type: entry.type} )
            CREATE (r)-[:HAS_LANE]->(l)
        """

        try:
            self.driver.execute_query(
                query,
                data=laneData_,
                database_= self.database
            )
        except exceptions.Neo4jError as e:
            print(f"Creating lane raised an error: \n{e}\n")
        except Exception as e:
            print(f"Adding preceding lane relationship raised an error: \n{e}\n")

    def createSignals(self, signalData_):
        query = """
            UNWIND COALESCE($data, []) AS entry
            MATCH (r:Road) WHERE r.id = entry.roadId
            CREATE (s:Signal {id: entry.id, signal_type: entry.type, orientation: entry.orientation, name: entry.name} )
            CREATE (r)-[:HAS_SIGNAL {atDistance: entry.distance}]->(s)
        """
        
        try:
            self.driver.execute_query(
                query,
                data=signalData_,
                database_= self.database
            )
        except exceptions.Neo4jError as e:
            print(f"Creating signal raised an error: \n{e}\n")
        except Exception as e:
            print(f"Adding preceding lane relationship raised an error: \n{e}\n")

    def createObjects(self, objectData_):
        query = """
            UNWIND COALESCE($data, []) AS entry
            MATCH (r:Road) WHERE r.id = entry.roadId
            CREATE (o:Object {id: entry.id, object_type: entry.type, orientation: entry.orientation, name: entry.name} )
            CREATE (r)-[:HAS_OBJECT {atDistance: entry.distance}]->(o)
        """
        
        try:
            self.driver.execute_query(
                query,
                data=objectData_,
                database_= self.database
            )
        except exceptions.Neo4jError as e:
            print(f"Creating object raised an error: \n{e}\n")
        except Exception as e:
            print(f"Adding preceding lane relationship raised an error: \n{e}\n")

    def addLanePrecedesRelationships(self, precedingLaneData_):
        query = """
            UNWIND COALESCE($data, []) AS entry
            MATCH (r1:Road)-[:HAS_LANE]->(l1:Lane), (r2)-[:HAS_LANE]->(l2:Lane)
            WHERE r1.id = entry.roadId AND r2.id = entry.succeedingRoadId AND l1.id = entry.laneId AND l2.id = entry.succeedingLaneId
            CREATE (l1)-[:PRECEDES {direction: entry.direction}]->(l2)
        """
        
        try:
            self.driver.execute_query(
                query,
                data=precedingLaneData_,
                database_= self.database
            )
        except exceptions.Neo4jError as e:
            print(f"Adding preceding lane relationship raised an error: \n{e}\n")
        except Exception as e:
            print(f"Adding preceding lane relationship raised an error: \n{e}\n")

    def addUndirectedConnectionRelationship(self, connectionData_):
        query = """
            UNWIND COALESCE($data, []) AS entry
            MATCH (r1:Road)-[:HAS_LANE]->(l1:Lane), (r2:Road)-[:HAS_LANE]->(l2:Lane)
            WHERE r1.id = entry.roadId AND r2.id = entry.conRoadId AND l1.id = entry.laneId AND l2.id = entry.conLaneId
            CREATE (l1)-[:CONNECTS_TO]->(l2)
        """
        
        try:
            self.driver.execute_query(
                query,
                data=connectionData_,
                database_= self.database
            )
        except exceptions.Neo4jError as e:
            print(f"Adding preceding lane relationship raised an error: \n{e}\n")
        except Exception as e:
            print(f"Adding preceding lane relationship raised an error: \n{e}\n")

    def __del__(self):
        self.driver.close()

def insertGraphIntoDB(mapDict):
    database = "neo4j"
    rc = RoadCreation(database)

    roadData = []
    laneData = []
    precedingLaneData = []
    undirectedLaneData = []
    signalData = []
    objectData = []
    for _, road in mapDict["roads"].items():
        roadData.append({
            "id": road["id"],
            "length": road["length"],
            "initial_heading": road["initial_heading"],
            "final_heading": road["final_heading"],
            "is_junction": road["is_junction"]
        })

        for _, lane in road["lanes"].items():
            laneData.append({
                "id": lane["id"],
                "type": lane["type"],
                "roadId": road["id"],
                "travel_direction": lane["travel_direction"],
                "side": lane["side"]
            })
        
        for _, lane in road["lanes"].items():
            if lane["type"] == "driving":
                for successor in lane["successors"]:
                    precedingLaneData.append(
                        {
                            "roadId": road["id"],
                            "succeedingRoadId": successor["road_id"], 
                            "laneId": lane["id"], 
                            "succeedingLaneId": successor["lane_id"], 
                            "direction": successor["direction"]
                        }
                    )
            else:
                for con in lane["connections"]:
                    data = {
                        "roadId": road["id"],
                        "conRoadId": con["road_id"],
                        "laneId": lane["id"],
                        "conLaneId": con["lane_id"]
                    }

                    if data not in undirectedLaneData:
                        undirectedLaneData.append(data)

        if "signals" in road:
            for signal in road["signals"]:
                signalData.append({
                    "id": signal["id"],
                    "type": signal["type"],
                    "orientation": signal["orientation"],
                    "roadId": road["id"],
                    "position": signal["position"],
                    "name": signal["name"]
                })

        if "objects" in road:
            for object in road["objects"]:
                objectData.append({
                    "id": object["id"],
                    "type": object["type"],
                    "orientation": object["orientation"],
                    "roadId": road["id"],
                    "position": object["position"],
                    "name": object["name"]
                })

    rc.createRoads(roadData)
    rc.createLanes(laneData)
    rc.createSignals(signalData)
    rc.createObjects(objectData)
    rc.addLanePrecedesRelationships(precedingLaneData)
    rc.addUndirectedConnectionRelationship(undirectedLaneData)