import pandas as pd
import json
import os
from fnmatch import fnmatch
import Levenshtein
import re

def generate_file():
    # read drug description
    dd_columns = ["药品名称", "成份", "性状", "适应症", "用法用量", "不良反应", "禁忌", "注意事项",
                  "孕妇及哺乳期妇女用药", "儿童用药", "老年用药", "贮藏", "规格", "药物相互作用",
                  "药理毒理", "药代动力学", "药物过量", "有效期", "包装", "执行标准"]
    df_drug_description = pd.DataFrame(columns=dd_columns)
    for fn in os.listdir("d:/pgkb_graph/processed"):
        if fnmatch(fn, "*drug_description_detail_*.csv"):
            df_drug_description = pd.concat(
                [
                    df_drug_description,
                    pd.read_csv(os.path.join("d:/pgkb_graph/processed", fn), dtype=str).fillna("")
                ],
                ignore_index=True,
                axis=0)
    df_drug_description = df_drug_description.fillna("")

    df_insurance_l2 = pd.read_csv("d:/pgkb_graph/processed/drug_insurance_L2.csv", dtype=str).fillna("")
    df_insurance_l3 = pd.read_csv("d:/pgkb_graph/processed/drug_insurance_L3.csv", dtype=str).fillna("")

    # 药品说明书数据用于药品属性的映射
    drug_dict = {}
    for index, row in df_drug_description.iterrows():
        drug_name = row["药品名称"]
        drug_dict[drug_name] = {}
        for col in dd_columns:
            drug_dict[drug_name][col] = row[col]


    # read disease details
    disease_list = []
    with open("data/medical.json", "r", encoding="utf-8") as f:
        for line in f.read().split("\n"):
            try:
                line_json = json.loads(line, strict=False)
                disease_list.append(line_json)
            except:
                pass

    # read ICD code
    df_icd = pd.read_csv("ICD10_filter.csv")
    icd_name_dict = dict(zip(list(df_icd["disease"].values),
                             list(df_icd["code"].values)))

    no_match_list = []
    for disease in disease_list:
        if disease["name"] in icd_name_dict.keys():
            disease["ICD10_code"] = icd_name_dict[disease["name"]]
        else:
            no_match_list.append(disease["name"])
            disease["ICD10_code"] = ""

    # 最短编辑比率
    # 用来匹配ICD字典与疾病名
    # after cleaning, matched disease increased from 632 to 868
    max_match_list = []
    no_match_list = list(map(lambda x: [
        x,
        re.sub(r"[性|病|症|征]", "", re.sub(r"[\(\)-\/（）\-\[\]\s、]", "", x))
        ], no_match_list))

    icd_name_list = list(map(lambda x: [
        x,
        re.sub(r"[性|病|症|征]", "", re.sub(r"[\(\)-\/（）\-\[\]\s、]", "", x))
        ], icd_name_dict.keys()))

    for no_match, no_match_clean in no_match_list:
        max_ratio = 0
        max_disease = ""
        for disease, disease_clean in icd_name_list:
            ratio = Levenshtein.ratio(no_match_clean, disease_clean)
            if ratio > max_ratio:
                max_ratio = ratio
                max_disease = disease
        max_match_list.append((no_match, max_disease, max_ratio))

    # 过滤最短编辑比率大于0.88的字符串组
    filter_match_list = list(filter(lambda x: x[2] >= 0.85, max_match_list))
    match_dict = dict(list(map(lambda x: (x[0], x[1]), filter_match_list)))

    for disease in disease_list:
        if disease["name"] in match_dict.keys():
            disease["ICD10_code"] = icd_name_dict[match_dict[disease["name"]]]

    # disease_drug_list里的药品数据最终会存到图谱当中
    disease_drug_list = []
    disease_symptom_list = []
    for disease in disease_list:
        for drug in disease["recommand_drug"]:
            disease_drug_list.append([disease["name"], drug])
        for symptom in disease["symptom"]:
            disease_symptom_list.append([disease["name"], symptom])

    disease_dict = {}
    for disease in disease_list:
        disease_dict[disease["name"]] = {}
        for key in disease.keys():
            disease_dict[disease["name"]][key] = disease[key]

    # add insurance info
    seq_regex = re.compile(r"（[\w]+-[\w]+）")
    seq_list = []
    text_list = []
    code_list = []
    for index, row in df_insurance_l2.iterrows():
        try:
            text = row["text"]
            code = row["code"]
            seq = re.findall(seq_regex, text)[0]
            text = text.replace(seq, "")
            start, end = seq.replace("（", "").replace("）", "").split("-")
            seq_list.append([start, end])
            text_list.append(text)
            code_list.append(code)
        except:
            continue

    zip_list = list(zip(seq_list, code_list, text_list))
    num_dict = {}
    for x in zip_list:
        for i in range(int(x[0][0]), int(x[0][1]) + 1):
            num_dict[i] = [x[1], x[2]]

    num_regex = re.compile(r"[\w]+")
    insurance_dict = {}
    for index, row in df_insurance_l3.iterrows():
        code = row["编号"]
        clazz = row["甲乙"]
        name = row["药品名称"]
        dosage_form = row["剂型"]
        try:
            num = re.findall(num_regex, code)[0]
            category_num = num_dict[int(num)][0]
            category = num_dict[int(num)][1]
        except:
            category_num = ""
            category = ""
        insurance_dict["{}--{}".format(name, dosage_form)] = [code, clazz, category_num, category]

    # 最短编辑比率
    for drug in drug_dict.keys():
        max_ratio = 0
        max_insurance = ""
        drug_clean = re.sub(r"[\(\)-\/（）\-\[\]\s、]", "", drug)
        drug_clean = re.sub(r"[片|注射液|颗粒|滴剂|胶囊|散剂|混悬液|乳剂|剂|膏|丸|口服溶液|口服液|咀嚼|泡腾]",
                            "", drug_clean)

        for ori_insurance in insurance_dict.keys():
            insurance, dosage_form = ori_insurance.split("--")
            insurance_clean = re.sub(r"[\(\)-\/（）\-\[\]\s、]", "", insurance)
            insurance_clean = re.sub(r"[片|注射液|颗粒|滴剂|胶囊|散剂|混悬液|乳剂|剂|膏|丸|口服溶液|口服液|咀嚼|泡腾]",
                                     "", insurance_clean)

            ratio = Levenshtein.ratio(drug_clean, insurance_clean)

            if insurance_clean in drug_clean:
                ratio += 0.15

            if ratio > max_ratio:
                max_ratio = ratio
                max_insurance = ori_insurance

        if max_ratio > 0.85:
            drug_dict[drug]["是否医保"] = "是"
            drug_dict[drug]["医保药品名"] = max_insurance.split("--")[0]
            drug_dict[drug]["甲乙"] = insurance_dict[max_insurance][1]
            drug_dict[drug]["医保药品种类"] = insurance_dict[max_insurance][3]
            drug_dict[drug]["医保药品种类编号"] = insurance_dict[max_insurance][2]
            drug_dict[drug]["剂型"] = max_insurance.split("--")[1]
        else:
            drug_dict[drug]["是否医保"] = "否"
            drug_dict[drug]["医保药品名"] = ""
            drug_dict[drug]["甲乙"] = ""
            drug_dict[drug]["医保药品种类"] = ""
            drug_dict[drug]["医保药品种类编号"] = ""
            drug_dict[drug]["剂型"] = ""

    with open("processed/disease_drug_list.json", "w", encoding="utf-8") as f:
        json.dump(disease_drug_list, f)

    with open("processed/disease_symptom_list.json", "w", encoding="utf-8") as f:
        json.dump(disease_symptom_list, f)

    with open("processed/disease_dict.json", "w", encoding="utf-8") as f:
        json.dump(disease_dict, f)

    with open("processed/drug_dict.json", "w", encoding="utf-8") as f:
        json.dump(drug_dict, f)


def generate_drug_chemical_relation():
    df_drug_chemical = pd.read_csv("d:/pgkb_graph/processed/nmpa_drug_chemical.csv",
                                   dtype=str).fillna("")[["chemical", "chn_name"]]

    df_drug_chemical = df_drug_chemical.drop_duplicates()

    with open("processed/drug_dict.json", "r", encoding="utf-8") as f:
        drug_dict = json.load(f)

    dc_drug_set = set(df_drug_chemical["chn_name"].values)
    dd_drug_set = set(drug_dict.keys())

    matched_drug_set = dc_drug_set.intersection(dd_drug_set)

    dc_drug_set = dc_drug_set - matched_drug_set
    dd_drug_set = dd_drug_set - matched_drug_set

    drug_regex = re.compile(
        r"[素|口腔|崩解|肠溶|舌下|放射免疫分析药盒|眼用|凝胶|片|注射液|颗粒|滴剂|胶囊|散剂|贴片|凝胶|咀嚼|混悬液|乳剂|剂|膏|丸|口服|口服液|糖浆|咀嚼|泡腾|缓释|分散|滴眼液|溶液|粉雾剂|速释]"
    )

    dc_match_dict = {x: x for x in matched_drug_set}

    def get_clean(drug_string, d_regex):
        drug_clean = re.sub(r"[\(\)-\/（）\-\[\]\s、]", "", drug_string)
        drug_clean = re.sub(d_regex, "", drug_clean)
        return drug_string, drug_clean

    for dc, dc_clean in [get_clean(x, drug_regex) for x in dc_drug_set]:
        max_ratio = 0
        max_dd = ""
        for dd, dd_clean in [get_clean(x, drug_regex) for x in dd_drug_set]:
            ratio = Levenshtein.ratio(dc_clean, dd_clean)
            if ratio > max_ratio:
                max_ratio = ratio
                max_dd = dd

        if max_ratio > 0.85:
            dc_match_dict[dc] = max_dd
        else:
            dc_match_dict[dc] = ""

    drug_name_alias = [dc_match_dict.get(x, "") for x in list(df_drug_chemical["chn_name"].values)]
    df_drug_chemical = df_drug_chemical.assign(name_alias=drug_name_alias)

    df_drug_chemical.to_csv("processed/drug_chemical.csv", index=False)


def generate_drug_interaction():
    with open("processed/drug_dict.json", "r", encoding="utf-8") as f:
        drug_dict = json.load(f)

    drug_interaction_dict = {}
    drug_regex_dict = {}
    drug_regex = re.compile(
        r"[喉片|素|口腔|崩解|肠溶|舌下|放射免疫分析药盒|眼用|凝胶|片|注射液|颗粒|滴剂|胶囊|散剂|贴片|凝胶|咀嚼|混悬液|乳剂|剂|膏|丸|口服|口服液|糖浆|咀嚼|泡腾|缓释|分散|滴眼液|溶液|粉雾剂|速释]"
    )
    for key, value in drug_dict.items():
        drug_interaction_dict[key] = value["药物相互作用"]
        drug_regex_dict[key] = key
        drug_regex_dict[re.sub(drug_regex, "", key)] = key

    drug_inter_list = []
    for drug, interaction in drug_interaction_dict.items():
        if interaction == "":
            continue
        for d in list(filter(lambda x: len(x) > 1 and x not in [drug, "和血", "降宁"] and x in interaction,
                             drug_regex_dict.keys())):
            drug_inter_list.append((drug, d, drug_regex_dict[d], interaction))

    drug_inter_list = list(set(map(lambda x: (x[0], x[2], x[3]), drug_inter_list)))
    drug_inter_list = list(filter(lambda x: x[0] != x[2], drug_inter_list))
    pd.DataFrame(
        drug_inter_list,
        columns=["drug", "interact_drug", "detail"]
    ).to_csv("processed/drug_interaction.csv", index=False)


if __name__ == "__main__":
    # generate_file()
    # generate_drug_chemical_relation()
    generate_drug_interaction()