import pandas as pd
import json
import os
from fnmatch import fnmatch
import Levenshtein

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
max_match_list= []
for no_match in no_match_list:
    max_ratio = 0
    max_disease = ""
    for disease in icd_name_dict.keys():
        if Levenshtein.ratio(no_match, disease) > max_ratio:
            max_ratio = Levenshtein.ratio(no_match, disease)
            max_disease = disease
    max_match_list.append((no_match, max_disease, max_ratio))

# 过滤最短编辑比率大于0.88的字符串组
filter_match_list = list(filter(lambda x: x[2] >= 0.88, max_match_list))
match_dict = dict(list(map(lambda x: (x[0], x[1]), filter_match_list)))

for disease in disease_list:
    if disease["name"] in match_dict.keys():
        disease["ICD10_code"] = icd_name_dict[match_dict[disease["name"]]]

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

with open("processed/disease_drug_list.json", "w", encoding="utf-8") as f:
    json.dump(disease_drug_list, f)

with open("processed/disease_symptom_list.json", "w", encoding="utf-8") as f:
    json.dump(disease_symptom_list, f)

with open("processed/disease_dict.json", "w", encoding="utf-8") as f:
    json.dump(disease_dict, f)

with open("processed/drug_dict.json", "w", encoding="utf-8") as f:
    json.dump(drug_dict, f)