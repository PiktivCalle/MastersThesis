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
            "lanes": {"left": [], "right": []},
            "signals": [],
            "objects": [],
            "initial_heading": float(geometry[0].get("hdg")),
            "final_heading": float(geometry[-1].get("hdg")),
            "is_junction": is_junction
        }
        
        for lane_section in road.findall("lanes/laneSection"):
            for lane_side in ["left", "right"]:
                lanes = lane_section.findall(f"{lane_side}/lane")
                for lane in lanes:
                    predecessor_lane = lane.find("link/predecessor")
                    successor_lane = lane.find("link/successor")
                    vector_lane = lane.find("userData/vectorLane")

                    lane_data = {
                        "id": lane.get("id"),
                        "type": lane.get("type"),
                        "travel_direction": vector_lane.get("travelDir") if lane.get("type") != "driving" else None,
                        "predecessors": [{
                            "predecessor_road_id": predecessor_road_id,
                            "predecessor_lane_id": predecessor_lane.get("id")
                        }] if predecessor_lane is not None else [],
                        "successors": [{
                            "successor_road_id": successor_road_id, 
                            "successor_lane_id": successor_lane.get("id"), 
                            "direction": None
                        }] if successor_lane is not None else [],
                    }

                    road_data["lanes"][lane_side].append(lane_data)

        if len(road_data["lanes"]["left"]) == 0:
            del road_data["lanes"]["left"]

        if len(road_data["lanes"]["right"]) == 0:
            del road_data["lanes"]["right"]
        
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
        for lane_side in parsed_data["roads"][road_id]["lanes"]:
            for lane in parsed_data["roads"][road_id]["lanes"][lane_side]:
                for successor in lane["successors"]:
                    turn_direction = determine_turn_possibility(road_id, successor["successor_road_id"], parsed_data["roads"])
                    successor["direction"] = turn_direction

    for junction in root.findall("junction"):
        junction_id = junction.get("id")
        junction_data = {"id": junction_id, "connections": [], "traffic_lights": []}
        
        for connection in junction.findall("connection"):
            incoming_road_id = connection.get("incomingRoad")
            connecting_road_id = connection.get("connectingRoad")
            
            turn_direction = determine_turn_possibility(incoming_road_id, connecting_road_id, road_id_to_data)

            for lane_link in connection.findall("laneLink"):
                from_lane_id = lane_link.get("from")
                to_lane_id = lane_link.get("to")

                all_lanes = parsed_data["roads"][incoming_road_id]["lanes"]["left"] + parsed_data["roads"][incoming_road_id]["lanes"]["right"]
                for lane in all_lanes:
                    if lane["id"] == from_lane_id:
                        lane["successors"].append({
                            "successor_road_id": connecting_road_id, 
                            "successor_lane_id": to_lane_id, 
                            "direction": turn_direction
                        })
                    
                    if lane["id"] == to_lane_id:
                        predecessor_entry = {
                            "predecessor_road_id": incoming_road_id, 
                            "predecessor_lane_id": from_lane_id
                        }

                        lane["predecessors"].append(predecessor_entry) if predecessor_entry not in lane["predecessors"] else None

            junction_data["connections"].append({
                "incoming_road": incoming_road_id,
                "connecting_road": connecting_road_id,
                "turn_direction": turn_direction
            })

        for controller in junction.findall("controller"):
            for control in controller.findall("control"):
                signal_id = control.get("signalId")
                junction_data["traffic_lights"].append({"id": signal_id, "position": 5.0})

    return parsed_data

def determine_turn_possibility(incoming_road_id, connecting_road_id, road_data, epsilon = 0.1):
    if incoming_road_id in road_data and connecting_road_id in road_data:
        incoming_heading = road_data[incoming_road_id]["final_heading"]
        connecting_heading = road_data[connecting_road_id]["initial_heading"]

        delta_heading = (connecting_heading - incoming_heading) % (2 * math.pi)
        if delta_heading > math.pi:
            delta_heading -= 2 * math.pi
        
        if abs(delta_heading) < epsilon:
            return "straight"
        elif abs(delta_heading - math.pi / 2) < epsilon:
            return "left"
        elif abs(delta_heading + math.pi / 2) < epsilon:
            return "right"
        elif abs(abs(delta_heading) - math.pi) < epsilon:
            return "u-turn"
        
    return "unknown"