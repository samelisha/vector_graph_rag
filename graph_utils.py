from typing import List

def get_adjacent(node, all_nodes_dict):
    results = []

    if "next" in node.metadata:
        nid = node.metadata["next"]
        if nid in all_nodes_dict:
            results.append(all_nodes_dict[nid])

    if "prev" in node.metadata:
        nid = node.metadata["prev"]
        if nid in all_nodes_dict:
            results.append(all_nodes_dict[nid])

    return results