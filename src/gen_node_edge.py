import json
from copy import deepcopy
import pandas as pd

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

def gen_relation():
    # Add node, relation from disease_node_list and symptom_node_list
    drug_node_list = []
    disease_node_list = []
    symptom_node_list = []
    edge_list = []

    # used for deduplicate
    drug_set = []
    disease_set = []
    symptom_set = []

    # drug_disease relation
    with open("processed/disease_drug_list.json", "r", encoding="utf-8") as f:
        disease_drug_list = json.load(f)

    with open("processed/disease_symptom_list.json", "r", encoding="utf-8") as f:
        disease_symptom_list = json.load(f)

    with open("processed/disease_dict.json", "r", encoding="utf-8") as f:
        disease_dict = json.load(f)

    with open("processed/drug_dict.json", "r", encoding="utf-8") as f:
        drug_dict = json.load(f)

    with open("processed/warning_dict.json", "r", encoding="utf-8") as f:
        warning_dict = json.load(f)

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

        drug_node = get_drug_node(drug, drug_dict, warning_dict)
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
                "description": disease_dict.get(disease, {}).get("desc", ""),
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


def gen_drug_che_rel():
    # Add node, chemical-drug relation from drug_chemical
    # drug chemical match by english
    with open("processed/drug_dict.json", "r", encoding="utf-8") as f:
        drug_dict = json.load(f)

    with open("processed/warning_dict.json", "r", encoding="utf-8") as f:
        warning_dict = json.load(f)

    df_dc = pd.read_csv("processed/drug_chemical.csv", dtype=str).fillna("")
    dc_relation_list = []
    for index, row in df_dc.iterrows():
        chemical = row["chemical"]
        drug = row["chn_name"]
        drug_alias = row["name_alias"]

        if chemical != "" and drug != "":
            dc_relation_list.append((chemical, drug))

        if chemical != "" and drug_alias != "" and drug_alias != drug:
            dc_relation_list.append((chemical, drug_alias))

    dc_relation_list = list(set(dc_relation_list))

    edge_list = []
    drug_node_list = []
    drug_set = []
    for rel in dc_relation_list:
        drug_node = get_drug_node(rel[1], drug_dict, warning_dict)
        if rel[1] not in drug_set:
            # add drug node
            drug_set.append(rel[1])
            drug_node_list.append(drug_node)

        chemical_drug_edge = {
            "start_node": {
                "label": ["chemical"],
                "node_ID": "chemical_name",
                "property": {
                    "chemical_name": rel[0].lower(),
                }
            },
            "end_node": {
                "label": ["drug"],
                "node_ID": "drug_name",
                "property": {
                    "drug_name": rel[1],
                }
            },
            "edge": {
                "label": "chemical_drug_relation",
                "property": {}
            }
        }
        edge_list.append(chemical_drug_edge)

    with open("json/dc_edges.json", "w") as f:
        json.dump(edge_list, f)

    with open("json/dc_nodes.json", "w") as f:
        json.dump(drug_node_list, f)


def get_drug_node(drug, drug_dict, warning_dict):
    return {
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
            "in_medical_insurance": drug_dict.get(drug, {}).get("是否医保", ""),
            "insurance_drug_name": drug_dict.get(drug, {}).get("医保药品名", ""),
            "insurance_level": drug_dict.get(drug, {}).get("甲乙", ""),
            "insurance_drug_category": drug_dict.get(drug, {}).get("医保药品种类", ""),
            "insurance_drug_category_num": drug_dict.get(drug, {}).get("医保药品种类编号", ""),
            "insurance_dosage_form": drug_dict.get(drug, {}).get("剂型", ""),
            "has_fda_warning": "是" if drug in warning_dict.keys() else "否",
            "fda_warning": warning_dict.get(drug, {}).get("warning", ""),
            "fda_warning_chn": warning_dict.get(drug, {}).get("warning_chn", ""),
            "fda_warning_link": warning_dict.get(drug, {}).get("link", ""),
        }
    }


def gen_drug_interact_rel():
    # TODO need to improve
    # Add node, drug-interact relation from drug_interaction file
    df_di = pd.read_csv("processed/drug_interaction.csv", dtype=str).fillna("")

    with open("processed/warning_dict.json", "r", encoding="utf-8") as f:
        warning_dict = json.load(f)

    with open("processed/drug_dict.json", "r", encoding="utf-8") as f:
        drug_dict = json.load(f)

    drug_node_list = []
    drug_set = []
    edge_list = []
    for index, row in df_di.iterrows():
        drug_node = get_drug_node(row["drug"], drug_dict, warning_dict)
        if row["drug"] not in drug_set:
            # add drug node
            drug_set.append(row["drug"])
            drug_node_list.append(drug_node)

        drug_node = get_drug_node(row["interact_drug"], drug_dict, warning_dict)
        if row["interact_drug"] not in drug_set:
            # add drug node
            drug_set.append(row["interact_drug"])
            drug_node_list.append(drug_node)

        drug_interact_edge = {
            "start_node": {
                "label": ["drug"],
                "node_ID": "drug_name",
                "property": {
                    "drug_name": row["drug"],
                }
            },
            "end_node": {
                "label": ["drug"],
                "node_ID": "drug_name",
                "property": {
                    "drug_name": row["interact_drug"],
                }
            },
            "edge": {
                "label": "drug_interaction",
                "property": {
                    "detail": row["detail"].replace("\"", "'")
                }
            }
        }
        edge_list.append(drug_interact_edge)

    with open("json/drug_interact_edges.json", "w") as f:
        json.dump(edge_list, f)

    with open("json/drug_interact_nodes.json", "w") as f:
        json.dump(drug_node_list, f)


def gen_drug_dict_node():
    # Add all drug node from drug_dict file
    with open("processed/warning_dict.json", "r", encoding="utf-8") as f:
        warning_dict = json.load(f)

    with open("processed/drug_dict.json", "r", encoding="utf-8") as f:
        drug_dict = json.load(f)

    node_list = []
    for key in drug_dict.keys():
        if key != "":
            node_list.append(get_drug_node(key, drug_dict, warning_dict))

    with open("json/all_drug_nodes.json", "w") as f:
        json.dump(node_list, f)


def gen_new_che_drug_relation():
    # 通过化合物中文翻译匹配新的药物化合物关系
    df_new_che_drug = pd.read_csv("processed/new_match_drug_chemical.csv", dtype=str).fillna("")
    edge_list = []

    for index, row in df_new_che_drug.iterrows():
        chemical_name = row["chemical"]
        drug_name = row["drug"]

        chemical_drug_edge = {
            "start_node": {
                "label": ["chemical"],
                "node_ID": "chemical_name",
                "property": {
                    "chemical_name": chemical_name,
                }
            },
            "end_node": {
                "label": ["drug"],
                "node_ID": "drug_name",
                "property": {
                    "drug_name": drug_name,
                }
            },
            "edge": {
                "label": "chemical_drug_relation",
                "property": {}
            }
        }
        edge_list.append(chemical_drug_edge)

    with open("json/new_che_drug_edges.json", "w") as f:
        json.dump(edge_list, f)


def generate_cn_drug_label():
    df_cn_dl = pd.read_csv("processed/cn_drug_label.csv", dtype=str).fillna("")
    node_name_set = []
    node_list = []
    edge_list = []
    for index, row in df_cn_dl.iterrows():
        gene_name = row["gene"]
        chemical_name = row["en_drug"]
        remark = row["remark"]
        gene_node = {
            "label": ["gene"],
            "node_ID": "gene_name",
            "property": {
                "gene_name": gene_name,
                "display": gene_name
            }
        }
        if gene_name not in node_name_set:
            node_list.append(gene_node)
            node_name_set.append(gene_name)

        chemical_node = {
            "label": ["chemical"],
            "node_ID": "chemical_name",
            "property": {
                "chemical_name": chemical_name,
                "display": chemical_name
            }
        }
        if chemical_name not in node_name_set:
            node_list.append(chemical_node)
            node_name_set.append(chemical_name)

        cn_label_edge = {
            "end_node": {
                "label": ["chemical"],
                "node_ID": "chemical_name",
                "property": {
                    "chemical_name": chemical_name,
                }
            },
            "start_node": {
                "label": ["gene"],
                "node_ID": "gene_name",
                "property": {
                    "gene_name": gene_name,
                }
            },
            "edge": {
                "label": "cn_drug_label",
                "property": {
                    "remark": remark
                }
            }
        }
        edge_list.append(cn_label_edge)

    with open("json/cn_dl_nodes.json", "w") as f:
        json.dump(node_list, f)

    with open("json/cn_dl_edges.json", "w") as f:
        json.dump(edge_list, f)


def gen_new_drug_disease():
    edge_list = []
    # drug_disease relation
    with open("processed/disease_drug_new_list.json", "r", encoding="utf-8") as f:
        disease_drug_list = json.load(f)

    for drug, disease in disease_drug_list:
        # add relation edge
        disease_drug_edge = {
            "start_node": {
                "label": ["drug"],
                "node_ID": "drug_name",
                "property": {
                    "drug_name": drug,
                }
            },
            "end_node": {
                "label": ["disease"],
                "node_ID": "disease_name",
                "property": {
                    "disease_name": disease
                }
            },
            "edge": {
                "label": "treatment",
                "property": {}
            }
        }
        edge_list.append(disease_drug_edge)

    with open("json/new_drug_disease_edges.json", "w") as f:
        json.dump(edge_list, f)


if __name__ == "__main__":
    gen_relation()
    gen_drug_che_rel()
    # gen_drug_interact_rel()
    gen_drug_dict_node()
    gen_new_che_drug_relation()
    generate_cn_drug_label()
    gen_new_drug_disease()