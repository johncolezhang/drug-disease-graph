import json
from copy import deepcopy

def edge_node(node, remain_label_list, remain_property_list):
    new_node = dict()
    new_node["node_ID"] = node["node_ID"]
    property_dict = deepcopy(node["property"])
    pk = list(property_dict.keys())
    for x in pk:
        if x not in remain_property_list:
            del property_dict[x]
    new_node["property"] = property_dict

    label_list = deepcopy(node["label"])
    for x in label_list:
        if x not in remain_label_list:
            label_list.remove(x)
    new_node["label"] = label_list
    return new_node

drug_node_list = []
disease_node_list = []
symptom_node_list = []
edge_list = []

# used for deduplicate
drug_set = []
disease_set = []
symptom_set = []

with open("processed/disease_drug_list.json", "r", encoding="utf-8") as f:
    disease_drug_list = json.load(f)

with open("processed/disease_symptom_list.json", "r", encoding="utf-8") as f:
    disease_symptom_list = json.load(f)

with open("processed/disease_dict.json", "r", encoding="utf-8") as f:
    disease_dict = json.load(f)

with open("processed/drug_dict.json", "r", encoding="utf-8") as f:
    drug_dict = json.load(f)


for disease, drug in disease_drug_list:
    disease_node = {
        "label": ["disease"],
        "node_ID": "disease_name",
        "property": {
            "disease_name": disease,
            "display": disease,
            "description": disease_dict.get(disease, {}).get("desc", ""),
            "prevent": disease_dict.get(disease, {}).get("prevent", ""),
            "cause": disease_dict.get(disease, {}).get("cause", ""),
            "in_medical_insurance": disease_dict.get(disease, {}).get("yibao_status", ""),
            "susceptible_people": disease_dict.get(disease, {}).get("easy_get", ""),
            "infectious_through": disease_dict.get(disease, {}).get("get_way", "")
        }
    }
    if disease not in disease_set:
        # add disease node
        disease_set.append(disease)
        disease_node_list.append(disease_node)

    drug_node = {
        "label": ["drug"],
        "node_ID": "drug_name",
        "property": {
            "drug_name": drug,
            "display": drug,
            "component": drug_dict.get(drug, {}).get("成份", ""),
            "character": drug_dict.get(drug, {}).get("性状", ""),
            "indication": drug_dict.get(drug, {}).get("适应症", ""),
            "dosage": drug_dict.get(drug, {}).get("用法用量", ""),
            "adverse_reaction": drug_dict.get(drug, {}).get("不良反应", ""),
            "avoid": drug_dict.get(drug, {}).get("禁忌", ""),
            "attention_notice": drug_dict.get(drug, {}).get("注意事项", ""),
            "pregnant_attention": drug_dict.get(drug, {}).get("孕妇及哺乳期妇女用药", ""),
            "children_attention": drug_dict.get(drug, {}).get("儿童用药", ""),
            "older_attention": drug_dict.get(drug, {}).get("老年用药", ""),
            "storage": drug_dict.get(drug, {}).get("贮藏", ""),
            "specification": drug_dict.get(drug, {}).get("规格", ""),
            "drug_interaction": drug_dict.get(drug, {}).get("药物相互作用", ""),
            "pharmacology_toxicology": drug_dict.get(drug, {}).get("药理毒理", ""),
            "pharmacokinetics": drug_dict.get(drug, {}).get("药代动力学", ""),
            "drug_overdose": drug_dict.get(drug, {}).get("药物过量", ""),
            "expiry_date": drug_dict.get(drug, {}).get("有效期", ""),
            "package": drug_dict.get(drug, {}).get("包装", ""),
            "standard": drug_dict.get(drug, {}).get("执行标准", ""),
        }
    }
    if drug not in drug_set:
        # add drug node
        drug_set.append(drug)
        drug_node_list.append(drug_node)

    # add relation edge
    disease_drug_edge = {
        "start_node": edge_node(
            drug_node,
            remain_label_list=["drug"],
            remain_property_list=["drug_name"]
        ),
        "end_node": edge_node(
            disease_node,
            remain_label_list=["disease"],
            remain_property_list=["disease_name"]
        ),
        "edge": {
            "label": "treatment",
            "property": {}
        }
    }
    edge_list.append(disease_drug_edge)

for disease, symptom in disease_symptom_list:
    disease_node = {
        "label": ["disease"],
        "node_ID": "disease_name",
        "property": {
            "disease_name": disease,
            "display": disease,
            "desc": disease_dict.get(disease, {}).get("desc", ""),
            "prevent": disease_dict.get(disease, {}).get("prevent", ""),
            "cause": disease_dict.get(disease, {}).get("cause", ""),
            "in_medical_insurance": disease_dict.get(disease, {}).get("yibao_status", ""),
            "susceptible_people": disease_dict.get(disease, {}).get("easy_get", ""),
            "infectious_through": disease_dict.get(disease, {}).get("get_way", "")
        }
    }
    if disease not in disease_set:
        disease_node_list.append(disease_node)
        disease_set.append(disease)

    symptom_node = {
        "label": ["symptom"],
        "node_ID": "symptom_name",
        "property": {
            "symptom_name": symptom,
            "display": symptom
        }
    }
    if symptom not in symptom_set:
        symptom_node_list.append(symptom_node)
        symptom_set.append(symptom)

    # add relation edge
    disease_symptom_edge = {
        "start_node": edge_node(
            disease_node,
            remain_label_list=["disease"],
            remain_property_list=["disease_name"]
        ),
        "end_node": edge_node(
            symptom_node,
            remain_label_list=["symptom"],
            remain_property_list=["symptom_name"]
        ),
        "edge": {
            "label": "has_symptom",
            "property": {}
        }
    }
    edge_list.append(disease_symptom_edge)

print(len(symptom_node_list))
print(len(drug_node_list))
print(len(disease_node_list))
print(len(edge_list))

node_list = []
node_list.extend(symptom_node_list)
node_list.extend(drug_node_list)
node_list.extend(disease_node_list)

with open("json/nodes.json", "w") as f:
    json.dump(node_list, f)

with open("json/edges.json", "w") as f:
    json.dump(edge_list, f)