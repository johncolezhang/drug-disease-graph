import pandas as pd
import re
import json
import requests
from collections import defaultdict


class icdMapping:
    def __init__(self):
        df_icd10 = pd.read_excel("医保ICD10_v2.0_0122.xlsx", sheet_name="完整分类与代码")

        df_icd10_chapter = df_icd10[["章", "章代码范围", "章的名称"]]
        df_icd10_chapter = df_icd10_chapter.drop_duplicates()
        df_icd10_section = df_icd10[["节代码范围", "节名称"]]
        df_icd10_section = df_icd10_section.drop_duplicates()
        df_icd10_class = df_icd10[["类目代码", "类目名称"]]
        df_icd10_class = df_icd10_class.drop_duplicates()
        df_icd10_subclass = df_icd10[["亚目代码", "亚目名称"]]
        df_icd10_subclass = df_icd10_subclass.drop_duplicates()
        df_icd10_code = df_icd10[["诊断代码", "诊断名称"]]

        self.icd10_code_dict = dict(zip(
            list(df_icd10_code["诊断代码"].values),
            list(df_icd10_code["诊断名称"].values)
        ))

        self.icd10_subclass_dict = dict(zip(
            list(df_icd10_subclass["亚目代码"].values),
            list(df_icd10_subclass["亚目名称"].values)
        ))

        self.icd10_class_dict = dict(zip(
            list(df_icd10_class["类目代码"].values),
            list(df_icd10_class["类目名称"].values)
        ))

        self.icd10_section_dict = dict(zip(
            list(df_icd10_section["节代码范围"].values),
            list(df_icd10_section["节名称"].values)
        ))

        self.icd10_chapter_dict = dict(zip(
            list(df_icd10_chapter["章代码范围"].values),
            list(df_icd10_chapter["章的名称"].values)
        ))

        with open("processed/icd10_disease_dict.json", "r") as f:
            self.disease_dict = json.load(f)


    @staticmethod
    def gen_icd_disease_dict():
        req = requests.get("https://zstp.pcl.ac.cn:8002/load_tree/ICD10")
        node_list = json.loads(req.content)["nodes"]

        node_list = list(map(lambda x: {
            "type": "class" if "class" in x["icon"] else "disease",
            "parent_id": x["pId"],
            "id": x["id"],
            "name": x["name"]
            }, node_list))

        disease_node_list = list(filter(lambda x: x["type"] == "disease", node_list))
        icd_node_list = list(filter(lambda x: x["type"] == "class", node_list))

        disease_dict = defaultdict(dict)
        for dis in disease_node_list:
            pid = dis["parent_id"]
            icd_name = list(filter(lambda x: x["id"] == pid, icd_node_list))[0]["name"]
            icd_code, icd_name = icd_name.split(" ")
            disease_dict[dis["name"]][icd_code] = icd_name

        with open("processed/icd10_disease_dict.json", "w") as f:
            json.dump(disease_dict, f)


def get_cancer():
    with open("processed/current_disease_icd_dict.json", "r") as f:
        cur_dis_icd_dict = json.load(f)

    # 所有疾病的icd编号
    icd_map = icdMapping()
    disease_icd_dict = icd_map.disease_dict

    df_cur_dd = pd.read_csv("processed/current_disease_drug.csv")
    df_cmekg_dd = pd.read_csv("processed/cmekg_disease_drug.csv")

    df_dd = pd.concat([df_cur_dd, df_cmekg_dd], axis=0).drop_duplicates()

    all_dis_list = list(set(df_dd["disease"].values))

    icd_dict = {}

    for adl in all_dis_list:
        if adl in cur_dis_icd_dict.keys():
            icd_dict[adl] = cur_dis_icd_dict[adl]
        elif adl in disease_icd_dict.keys():
            icd_dict[adl] = disease_icd_dict[adl]
        else:
            icd_dict[adl] = {}

    cancer_list = []
    cancer_str_list = []
    # 肿瘤范围: C00-D48
    for key, value in icd_dict.items():
        icd_code_list = [x[:3] for x in value.keys()]
        if len(list(filter(lambda x: "C00" <= x <= "D48", icd_code_list))) > 0 or "癌" in key:
            value_str = ",  ".join(["\'{}\': \'{}\'".format(x, y) for x, y in value.items()])
            cancer_list.append([key, value])
            cancer_str_list.append([key, value_str])

    pd.DataFrame(cancer_str_list, columns=["disease", "ICD10_info"]).to_csv(
        "processed/cancer_ICD10_info.csv", index=False)

    with open("cancer_list.json", "w") as f:
        json.dump(cancer_list, f)

    # get cancer drug
    df_cancer_disease_drug = df_dd[df_dd["disease"].isin([x[0] for x in cancer_list])]
    cancer_drug_list = list(dict.fromkeys(df_cancer_disease_drug["drug"].values))

    with open("processed/drug_dict.json", "r") as f:
        drug_dict = json.load(f)

    can_drug_dict = defaultdict(list)
    for cd in cancer_drug_list:
        drug_info_dict = drug_dict.get(cd, {})
        indication = drug_info_dict.get("适应症", "")
        medical_insurance = drug_info_dict.get("甲乙", "")
        component = drug_info_dict.get("成份", "")

        if "癌" in cd or "瘤" in cd or "癌" in indication or "瘤" in indication:
            can_drug_dict["drug_name"].append(cd)
            can_drug_dict["indication"].append(indication)
            can_drug_dict["medical_insurance"].append(medical_insurance)
            can_drug_dict["component"].append(component)

    df_cancer_drug = pd.DataFrame(can_drug_dict)
    df_cancer_drug.to_csv("processed/cancer_drug_detail.csv", index=False)

    remain_can_drug_list = can_drug_dict["drug_name"]
    df_cancer_disease_drug[df_cancer_disease_drug["drug"].isin(remain_can_drug_list)].to_csv(
        "processed/cancer_drug_relation.csv", index=False
    )


def get_cancer_from_dict():
    with open("processed/drug_dict.json", "r") as f:
        drug_dict = json.load(f)

    can_drug_dict = defaultdict(list)

    for cd in drug_dict:
        drug_info_dict = drug_dict.get(cd, {})
        indication = drug_info_dict.get("适应症", "")
        medical_insurance = drug_info_dict.get("甲乙", "")
        component = drug_info_dict.get("成份", "")

        if "癌" in indication or "瘤" in indication:
            can_drug_dict["drug_name"].append(cd)
            can_drug_dict["indication"].append(indication)
            can_drug_dict["medical_insurance"].append(medical_insurance)
            can_drug_dict["component"].append(component)

    df_cancer_drug = pd.DataFrame(can_drug_dict)
    df_cancer_drug.to_csv("processed/all_cancer_drug_detail.csv", index=False)

if __name__ == "__main__":
    # icd_mapping = icdMapping()
    # get_cancer()
    get_cancer_from_dict()
