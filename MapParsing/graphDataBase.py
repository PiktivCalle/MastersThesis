from neo4j import GraphDatabase, exceptions

URI = "neo4j://localhost"
AUTH = ("neo4j", "secretgraph")

class RoadCreation:
    def __init__(self, uri, auth, database):
        self.driver =  GraphDatabase.driver(uri, auth=auth)
        self.database = database

    def createRoad(self, id_, length_, initialHeading_, finalHeading_, isJunction_):
        query = (
            "CREATE ( :Road {id: $id, length: $length, initialHeading: $initialHeading, finalHeading: $finalHeading, isJunction: $isJunction} )"
        )
        
        try:
            self.driver.execute_query(
                query,
                id=id_,
                length=length_,
                initialHeading=initialHeading_,
                finalHeading=finalHeading_,
                isJunction=isJunction_,
                database_= self.database
            )
        except exceptions.Neo4jError as e:
            print(f"Creating road raised an error: \n{e}\n")
            
    def createLane(self, id_, type_, roadId_, side_):
        query = """
            MATCH (r:Road) WHERE r.id = $roadId
            CREATE ( l:Lane {id: $id, type: $type} )
            CREATE (r)-[:HAS_LANE {side: $side}]->(l)
        """
        
        try:
            self.driver.execute_query(
                query,
                id=id_,
                type=type_,
                roadId=roadId_,
                side=side_,
                database_= self.database
            )
        except exceptions.Neo4jError as e:
            print(f"Creating lane raised an error: \n{e}\n")

    def createSignal(self, id_, type_, orientation_, roadId_, distance_, name_):
        query = """
            MATCH (r:Road) WHERE r.id = $roadId
            CREATE (s:Signal {id: $id, type: $type, orientation: $orientation, name: $name} )
            CREATE (r)-[:HAS_SIGNAL {atDistance: $distance}]->(s)
        """
        
        try:
            self.driver.execute_query(
                query,
                id=id_,
                type=type_,
                orientation=orientation_,
                roadId=roadId_,
                distance=distance_,
                name=name_,
                database_= self.database
            )
        except exceptions.Neo4jError as e:
            print(f"Creating signal raised an error: \n{e}\n")

    def createObject(self, id_, type_, orientation_, roadId_, distance_, name_):
        query = """
            MATCH (r:Road) WHERE r.id = $roadId
            CREATE (o:Object {id: $id, type: $type, orientation: $orientation, name: $name} )
            CREATE (r)-[:HAS_OBJECT {atDistance: $distance}]->(o)
        """
        
        try:
            self.driver.execute_query(
                query,
                id=id_,
                type=type_,
                orientation=orientation_,
                roadId=roadId_,
                distance=distance_,
                name=name_,
                database_= self.database
            )
        except exceptions.Neo4jError as e:
            print(f"Creating object raised an error: \n{e}\n")

    def addLanePrecedesRelationship(self, roadId_, laneId_, succeedingRoadId_, succeedingLaneId_, direction_):
        query = """
            MATCH (r1:Road)-[:HAS_LANE]->(l1:Lane), (r2)-[:HAS_LANE]->(l2:Lane)
            WHERE r1.id = $roadId AND r2.id = $succeedingRoadId AND l1.id = $laneId AND l2.id = $succeedingLaneId
            CREATE (l1)-[:PRECEDES {direction: $direction}]->(l2)
        """
        
        try:
            self.driver.execute_query(
                query,
                roadId=roadId_,
                laneId=laneId_,
                succeedingRoadId=succeedingRoadId_,
                succeedingLaneId=succeedingLaneId_,
                direction=direction_,
                database_= self.database
            )
        except exceptions.Neo4jError as e:
            print(f"Adding preceding lane relationship raised an error: \n{e}\n")

    def __del__(self):
        self.driver.close()

def insertGraphIntoDB(mapDict):
    database = "neo4j"
    rc = RoadCreation(URI, AUTH, database)
    for _, road in mapDict["roads"].items():
        rc.createRoad(road["id"], road["length"], road["initial_heading"], road["final_heading"], road["is_junction"])
        
        for lane_side in road["lanes"]:
            for lane in road["lanes"][lane_side]:
                rc.createLane(lane["id"], lane["type"], road["id"], lane_side)

        for lane_side in road["lanes"]:
            for lane in road["lanes"][lane_side]:
                for successor in lane["successors"]:
                    rc.addLanePrecedesRelationship(road["id"], lane["id"], successor["successor_road_id"], successor["successor_lane_id"], successor["direction"])

        if "signals" in road:
            for signal in road["signals"]:
                rc.createSignal(signal["id"], signal["type"], signal["orientation"], road["id"], signal["position"], signal["name"])

        if "objects" in road:
            for object in road["objects"]:
                rc.createObject(object["id"], object["type"], object["orientation"], road["id"], object["position"], object["name"])