# Extract English words from ConceptNet CSV with specific relationships
import csv
import json
from tqdm import tqdm

# Relationships we care about
# target_rels = {"/r/UsedFor", "/r/CapableOf", "/r/ReceivesAction"}

# graph = {}

# CSV_FILE = "/Users/mcharit2/Downloads/full_conceptnet_ass.csv"

# # First, count total lines for tqdm progress bar
# with open(CSV_FILE, encoding="utf-8") as f:
#     total_lines = sum(1 for _ in f)

# with open(CSV_FILE, encoding="utf-8") as f:
#     reader = csv.reader(f, delimiter='\t')
#     for row in tqdm(reader, total=total_lines, desc="Processing ConceptNet"):
#         if len(row) < 4:
#             continue

#         rel, uri1, uri2 = row[1], row[2], row[3]  # col0=ID, col1=rel, col2=start, col3=end

#         # Only keep target relationships
#         if rel not in target_rels:
#             continue

#         # Only keep if both ends are English
#         if uri1.startswith("/c/en/") and uri2.startswith("/c/en/"):
            
#             # get the subject
#             subject = uri1.split("/")[3].replace("_", " ")
#             object = uri2.split("/")[3].replace("_", " ")
#             if subject not in graph:
#                 graph[subject] = []
#             graph[subject].append(object)

# # Save to file
# with open("conceptnet_graph_raw.json", "w", encoding="utf-8") as f:
#     json.dump(graph, f, ensure_ascii=False, indent=2)


# parse the raw graph into a more structured format based on conceptnet_exp into noweight format

import spacy
nlp = spacy.load("en_core_web_sm")

graph = json.load(open("conceptnet_graph_raw.json", "r", encoding="utf-8"))
word_graph = {}

for subj, obj_list in tqdm(graph.items(), desc="Parsing graph into word graph"):
    if " " in subj:
        continue  # skip multi-word subjects
    if subj not in word_graph:
        word_graph[subj] = {}
    for obj in obj_list:
        # use spacy to determine pos in obj
        doc_obj = nlp(obj)
        verb = None
        noun = None
        for token in doc_obj:
            if token.pos_ == "NOUN":
                noun = token.lemma_
                
            elif token.pos_ == "VERB":
                verb = token.lemma_
            
            if verb and noun:
                break

        if verb and noun:
            if verb not in word_graph[subj]:
                word_graph[subj][verb] = []
            if noun not in word_graph[subj][verb]:
                word_graph[subj][verb].append(noun)

# save to file
with open("bank_files/full_word_graph_noweight.json", "w", encoding="utf-8") as f:
    json.dump(word_graph, f, ensure_ascii=False, indent=2)

