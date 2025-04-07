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

# Remove incorrect successor to intersection road
for idx, val in enumerate(parsed_data["roads"][connecting_road_id]["lanes"][to_lane_id]["successors"]):
    if incoming_road_id == val["road_id"] and from_lane_id == val["lane_id"]:
        parsed_data["roads"][connecting_road_id]["lanes"][to_lane_id]["successors"].pop(idx)

# Swap incorrect predecessor to successor
for idx, val in enumerate(parsed_data["roads"][connecting_road_id]["lanes"][to_lane_id]["predecessors"]):
    if incoming_road_id != val["road_id"] and from_lane_id != val["lane_id"]:
        ret = parsed_data["roads"][connecting_road_id]["lanes"][to_lane_id]["predecessors"].pop(idx)
        parsed_data["roads"][connecting_road_id]["lanes"][to_lane_id]["successors"].append({
            "road_id": ret["road_id"], 
            "lane_id": ret["lane_id"], 
            "direction": "straight"
        })

        # Add reverse relationship
        parsed_data["roads"][ret["road_id"]]["lanes"][ret["lane_id"]]["predecessors"].append(con)