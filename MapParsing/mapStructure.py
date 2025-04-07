import math
import xml.etree.ElementTree as ET

def create_graph(file_name):
    tree = ET.parse(f"MapParsing/maps/{file_name}")
    root = tree.getroot()
    parsed_data = {"roads": {}, "junctions": {}}
    
    road_id_to_data = {}
    
    for road in root.findall("road"):
        road_id = road.get("id")
        length = float(road.get("length"))

        predecessor_road = road.find("link/predecessor")
        predecessor_road_id = predecessor_road.get("elementId")
        successor_road = road.find("link/successor")
        successor_road_id = successor_road.get("elementId")

        is_junction = road.get("junction")
        geometry = road.findall("planView/geometry")
        
        road_data = {
            "id": road_id,
            "length": length,
            "lanes": {},
            "signals": [],
            "objects": [],
            "initial_heading": float(geometry[0].get("hdg")) % (2*math.pi),
            "final_heading": float(geometry[-1].get("hdg")) % (2*math.pi),
            "is_junction": is_junction
        }
        
        for lane_section in road.findall("lanes/laneSection"):
            for lane_side in ["left", "right"]:
                lanes = lane_section.findall(f"{lane_side}/lane")
                for lane in lanes:
                    predecessor_lane = lane.find("link/predecessor")
                    successor_lane = lane.find("link/successor")
                    vector_lane = lane.find("userData/vectorLane")
                    lane_id = lane.get("id")

                    lane_type =  lane.get("type")

                    if lane_type == "driving":
                        connections = {
                            "predecessors": [{
                                "road_id": predecessor_road_id,
                                "lane_id": predecessor_lane.get("id")
                            }] if predecessor_lane is not None else [],
                            "successors": [{
                                "road_id": successor_road_id, 
                                "lane_id": successor_lane.get("id"), 
                                "direction": "straight"
                            }] if successor_lane is not None else []
                        }
                    else:
                        connections = {
                            "connections": []
                        }
                        connections["connections"].append({
                            "road_id": predecessor_road_id,
                            "lane_id": predecessor_lane.get("id")
                        }) if predecessor_lane is not None else None

                        connections["connections"].append({
                            "road_id": successor_road_id,
                            "lane_id": successor_lane.get("id")
                        }) if successor_lane is not None else None
                        

                    lane_data = {
                        "id": lane_id,
                        "type": lane_type,
                        "travel_direction": vector_lane.get("travelDir"),
                        "side": lane_side,
                    }
                    road_data["lanes"][lane_id] = lane_data | connections
        
        for signal in road.findall("signals/signal"):
            signal_data = {
                "id": signal.get("id"),
                "type": signal.get("type"),
                "name": signal.get("name"),
                "position": float(signal.get("s")),
                "orientation": "along" if signal.get("orientation") == "+" else "opposite"
            }
            road_data["signals"].append(signal_data)
            
        if len(road_data["signals"]) == 0:
            del road_data["signals"]

        for obj in road.findall("objects/object"):
            object_data = {
                "id": obj.get("id"),
                "type": obj.get("type"),
                "name": obj.get("name"),
                "position": float(obj.get("s")),
                "orientation": "along" if obj.get("orientation") == "+" else "opposite"
            }
            road_data["objects"].append(object_data)
        
        if len(road_data["objects"]) == 0:
            del road_data["objects"]

        road_id_to_data[road_id] = road_data
        parsed_data["roads"][road_id] = road_data

    for road_id in parsed_data["roads"]:
        for lane_id in parsed_data["roads"][road_id]["lanes"]:
            lane = parsed_data["roads"][road_id]["lanes"][lane_id]

            if lane["type"] != "driving": continue
        
            predecessors = lane["predecessors"]
            successors = lane["successors"]

            current_road = parsed_data["roads"][road_id]

            if lane["type"] != "driving": continue

            junction_id = int(current_road["is_junction"])
            if junction_id == -1:
                # This check is to make sure that the corners are correct
                if len(successors) > 0 and len(predecessors) > 0 and abs(int(current_road["final_heading"]) - int(current_road["initial_heading"])) > 0.1:
                    predecessors[0]["road_id"], predecessors[0]["lane_id"], successors[0]["road_id"], successors[0]["lane_id"] = successors[0]["road_id"], successors[0]["lane_id"], predecessors[0]["road_id"], predecessors[0]["lane_id"]
                    
                    if lane["travel_direction"] != "undirected":
                        lane["travel_direction"] = "backward" if lane["travel_direction"] == "forward" else "forward" 

                    current_road["initial_heading"] = parsed_data["roads"][predecessors[0]["road_id"]]["final_heading"]
                    current_road["final_heading"] = parsed_data["roads"][successors[0]["road_id"]]["initial_heading"]

                # This check makes sure that driving direction matters when it comes to turns
                if lane["travel_direction"] == "backward":
                    if len(successors) > 0 and len(predecessors) > 0:
                        predecessors[0]["road_id"], predecessors[0]["lane_id"], successors[0]["road_id"], successors[0]["lane_id"] = successors[0]["road_id"], successors[0]["lane_id"], predecessors[0]["road_id"], predecessors[0]["lane_id"]
                    elif len(successors) > 0:
                        lane["predecessors"].append({
                            "road_id": successors[0]["road_id"],
                            "lane_id": successors[0]["lane_id"]
                        })
                        lane["successors"] = []
                    elif len(predecessors) > 0:
                        lane["successors"].append({
                            "road_id": predecessors[0]["road_id"], 
                            "lane_id": predecessors[0]["lane_id"], 
                            "direction": "straight"
                        })
                        lane["predecessors"] = []

    junction_data = {}
    for junction in root.findall("junction"):
        junction_id = junction.get("id")
        junction_data[junction_id] = {}

        for connection in junction.findall("connection"):
            incoming_road_id = connection.get("incomingRoad")
            connecting_road_id = connection.get("connectingRoad")
            contact_point = connection.get("contactPoint")
                        
            for lane_link in connection.findall("laneLink"):
                to_lane_id = lane_link.get("to")
                from_lane_id = lane_link.get("from")

                dir_none = {"direction": None}
                dir_straight = {"direction": "straight"}

                con = {
                    "road_id": connecting_road_id, 
                    "lane_id": to_lane_id
                }
                inc = {
                    "road_id": incoming_road_id, 
                    "lane_id": from_lane_id 
                }

                # Make non driving roads undirected
                if parsed_data["roads"][connecting_road_id]["lanes"][to_lane_id]["type"] != "driving":
                    for con_ in parsed_data["roads"][connecting_road_id]["lanes"][to_lane_id]["connections"]:
                        if con_ != inc:
                            suc = con_

                    if inc not in parsed_data["roads"][connecting_road_id]["lanes"][to_lane_id]["connections"]:
                        parsed_data["roads"][connecting_road_id]["lanes"][to_lane_id]["connections"].append(inc)

                    if suc not in parsed_data["roads"][connecting_road_id]["lanes"][to_lane_id]["connections"]:
                        parsed_data["roads"][connecting_road_id]["lanes"][to_lane_id]["connections"].append(suc)

                    if con not in parsed_data["roads"][incoming_road_id]["lanes"][from_lane_id]["connections"]:
                        parsed_data["roads"][incoming_road_id]["lanes"][from_lane_id]["connections"].append(con)

                    if con not in parsed_data["roads"][suc["road_id"]]["lanes"][suc["lane_id"]]["connections"]:
                        parsed_data["roads"][suc["road_id"]]["lanes"][suc["lane_id"]]["connections"].append(con)

                    # Skip the rest of the calculations as they are not needed for non driveable roads
                    continue

                # Fix heading of intersection roads
                if contact_point == "end":
                    parsed_data["roads"][connecting_road_id]["initial_heading"], parsed_data["roads"][connecting_road_id]["final_heading"] = (parsed_data["roads"][connecting_road_id]["final_heading"]+math.pi) % (2*math.pi), (parsed_data["roads"][connecting_road_id]["initial_heading"]+math.pi) % (2*math.pi)
                
                if(abs(math.cos(parsed_data["roads"][connecting_road_id]["final_heading"]) - 1) < 1e-4 ):
                    parsed_data["roads"][connecting_road_id]["final_heading"] = 0

                if(abs(math.cos(parsed_data["roads"][connecting_road_id]["initial_heading"]) - 1) < 1e-4 ):
                    parsed_data["roads"][connecting_road_id]["initial_heading"] = 0

                # Adds the connecting road as suc to the incoming road
                if (con | dir_none) not in parsed_data["roads"][incoming_road_id]["lanes"][from_lane_id]["successors"]:
                    dir = {
                        "direction": determine_turn_possibility(initial_heading=parsed_data["roads"][connecting_road_id]["initial_heading"], final_heading=parsed_data["roads"][connecting_road_id]["final_heading"])
                    }
                    parsed_data["roads"][incoming_road_id]["lanes"][from_lane_id]["successors"].append(con | dir)

                # Adds the incoming road as pred to connecting road
                if inc not in parsed_data["roads"][connecting_road_id]["lanes"][to_lane_id]["predecessors"]:
                    parsed_data["roads"][connecting_road_id]["lanes"][to_lane_id]["predecessors"].append(inc)

                # Determine which road is to come, depends on where the contact point of the connection is
                tmp = "successors" if contact_point == "start" else "predecessors"

                # Will always be the first in the list since each intersection road only has one pred/suc initially
                suc = parsed_data["roads"][connecting_road_id]["lanes"][to_lane_id][tmp][0]

                # Add connecting road as predecessor to the road to come
                if con not in parsed_data["roads"][suc["road_id"]]["lanes"][suc["lane_id"]]["predecessors"]:
                    parsed_data["roads"][suc["road_id"]]["lanes"][suc["lane_id"]]["predecessors"].append(con)

                if inc | dir_straight in parsed_data["roads"][connecting_road_id]["lanes"][to_lane_id]["successors"]:
                    idx = parsed_data["roads"][connecting_road_id]["lanes"][to_lane_id]["successors"].index(inc | dir_straight)
                    parsed_data["roads"][connecting_road_id]["lanes"][to_lane_id]["successors"].pop(idx)

                if suc in parsed_data["roads"][connecting_road_id]["lanes"][to_lane_id]["predecessors"]:
                    idx = parsed_data["roads"][connecting_road_id]["lanes"][to_lane_id]["predecessors"].index(suc)

                    ret = parsed_data["roads"][connecting_road_id]["lanes"][to_lane_id]["predecessors"].pop(idx)
                    parsed_data["roads"][connecting_road_id]["lanes"][to_lane_id]["successors"].append({
                        "road_id": ret["road_id"], 
                        "lane_id": ret["lane_id"], 
                        "direction": "straight"
                    })

                    # Add reverse relationship
                    parsed_data["roads"][ret["road_id"]]["lanes"][ret["lane_id"]]["predecessors"].append(con)

    return parsed_data

def determine_turn_possibility(initial_heading, final_heading, epsilon = 1e-4):
    delta_heading = final_heading - initial_heading
    
    if abs(delta_heading) < epsilon:
        return "straight"
    elif abs(math.sin(delta_heading - math.pi / 2)) < epsilon:
        return "left"
    elif abs(math.sin(delta_heading + math.pi / 2)) < epsilon:
        return "right"
    elif abs(abs(delta_heading) - math.pi) < epsilon:
        return "u-turn"
        