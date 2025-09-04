import random
import numpy as np
import json
import spacy
import re
import datetime
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import yaml
import sys
import os
import pickle
import matplotlib.pyplot as plt

# ===== GLOBAL VARIABLES ===== #
# These will be initialized by the setup function
nlp = None
st_model = None
ALL_SUBJS = None
ALL_OBJS = None
ALL_VERBS = None
CN_GRAPH = None
AF_VERBS = None
pre_verb_enc = None
pre_ent_enc = None
af_verb_enc_dict = None

# Constants
MC_MUTATE_PERC = 0.25
ENT_MUTATE_PERC = 0.1
VERB_MUTATE_PERC = 0.25
POP_SIZE = 10
NUM_GENERATIONS = 20

# ===== SETUP FUNCTION ===== #
def setup_models_and_data(data_path='bank_files'):
    """Initialize models and load data for the novelty search algorithm."""
    global nlp, st_model, ALL_SUBJS, ALL_OBJS, ALL_VERBS, CN_GRAPH
    global AF_VERBS, af_verb_enc_dict
    
    # Set models for NLP tasks
    nlp = spacy.load("en_core_web_sm")
    st_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Import data
    ALL_SUBJS = np.load(f'{data_path}/SUBJECTS_clean.npy', allow_pickle=True)
    ALL_OBJS = np.load(f'{data_path}/OBJECTS_clean.npy', allow_pickle=True)
    ALL_VERBS = np.load(f'{data_path}/VERBS_clean.npy', allow_pickle=True)
    CN_GRAPH = json.load(open(f'{data_path}/full_word_graph_noweight.json'))

    # Convert to normal lists
    ALL_SUBJS = [str(s) for s in ALL_SUBJS]
    ALL_OBJS = [str(o) for o in ALL_OBJS]
    ALL_VERBS = [str(v) for v in ALL_VERBS]

    # Create verbs and verb encodings
    AF_VERBS = ["moved", "died", "cloned", "took", "pushed", "added", "transformed", "blocked", "chased"]
    all_af_verb_encs = st_model.encode(AF_VERBS)
    af_verb_enc_dict = {AF_VERBS[i]: all_af_verb_encs[i] for i in range(len(AF_VERBS))}
    
    print(f"Loaded data: {len(ALL_SUBJS)} subjects, {len(ALL_OBJS)} objects, {len(ALL_VERBS)} verbs")


def pre_encode_data(use_file=True):
    ''' Uses the sentence transformer to encode all the ents and verbs beforehand to reduce bottleneck'''
    global pre_ent_enc, pre_verb_enc

    # try to reload from file if exists
    if use_file:
        try:
            if os.path.exists('bank_files/pre_encoded_data.pkl'):
                with open('bank_files/pre_encoded_data.pkl', 'rb') as f:
                    data = pickle.load(f)
                    try:
                        pre_ent_enc = data['entities']
                        pre_verb_enc = data['verbs']

                    except KeyError as e:
                        print(f"Key error: {e}")
                    finally:
                        print(f"# (Imported) Entity Vecs: {len(pre_ent_enc)}")
                        print(f"# (Imported) Verb Vecs: {len(pre_verb_enc)}")
                        return
        except Exception as e:
            print("Unable to load data from file :(")
            print(e)
            print("Re-encoding all entities and verbs...")



    # encode the combination of entities and verbs
    pre_ent_enc = {}
    pre_verb_enc = {}
    for e in tqdm((ALL_SUBJS + ALL_OBJS), desc="Encoding entities"):
        pre_ent_enc[e] = st_model.encode(e)
    for v in tqdm(ALL_VERBS, desc="Encoding verbs"):
        pre_verb_enc[v] = st_model.encode(v)

    print(f"# (Encoded) Entity Vecs: {len(pre_ent_enc)}")
    print(f"# (Encoded) Verb Vecs: {len(pre_verb_enc)}")



    # export the encodings to a pickle file for quick reload
    if use_file:
        with open('bank_files/pre_encoded_data.pkl', 'wb') as f:
            pickle.dump({'entities': pre_ent_enc, 'verbs': pre_verb_enc}, f)


# ===== HELPER FUNCTIONS ===== #
def get_assoc_dat(mc_ent):
    """Gets the associative data (related subjects, objects, and verbs) for a given entity representation"""
    if not mc_ent or mc_ent not in CN_GRAPH:
        return {}
    
    dat = CN_GRAPH[mc_ent]
    verbs = dat.keys()
    assoc_ents = []
    for v in verbs:
        assoc_ents.extend(dat[v])
    subj_ents = [e for e in assoc_ents if e in ALL_SUBJS]
    obj_ents = [e for e in assoc_ents if e in ALL_OBJS]
    subj_ents = list(set(subj_ents))  # remove duplicates
    obj_ents = list(set(obj_ents))    # remove duplicates
    return {'subj': subj_ents, 'obj': obj_ents, 'verbs': list(verbs)}


def get_assoc_verbs(ent):
    """Gets the associative verbs for a given entity representation"""
    if not ent or ent not in CN_GRAPH:
        return []
    dat = CN_GRAPH[ent]
    verbs = list(dat.keys())
    return verbs


def get_ent_encs(ents):
    """Gets the sentence transformer encodings for a list of entities"""
    # return {e: st_model.encode(re.sub(r'[0-9]+', '', e)) for e in ents}
    result = {}
    for e in ents:
        cleaned_e = re.sub(r'[0-9]+', '', e)
        encoding = pre_ent_enc.get(cleaned_e)
        if encoding is None:
            # Encode on-the-fly if not found in pre-encoded data
            encoding = st_model.encode(cleaned_e)
        result[e] = encoding
    return result

# def plot_fitness(fitness_values, file_path=None):
#     plt.plot(fitness_values)
#     plt.xlabel("Generation")
#     plt.ylabel("Fitness")
#     plt.title("Fitness over Generations")
#     if file_path:
#         plt.savefig(file_path)
#     plt.close()

def plot_graph(values, x_label, y_label, file_path=None):
    plt.plot(values)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(f"{y_label} over {x_label}")
    if file_path:
        plt.savefig(file_path)
    plt.close()

# ===== CLASSES ===== #
class AF_Story:
    """Maps a log for usage in the novelty search"""
    
    def __init__(self, log_file):
        self.log_file = log_file
        with open(log_file, 'r') as f:
            self.og_text = [line.strip() for line in f.readlines()]
        self.ent_ids = self.find_spec_ents()        # dict of entities with subject/object designation
        self.ent_reps = self.get_ent_reps()

        self.ent_order, self.mc_ent = self.find_ents()      # list of all entities in the original text
        self.verb_set = self.find_verbs()          # list of tuples of (subject entity, verb)
        self.verb_order = [v[1] for v in self.verb_set.values()]    # list of all verbs in the original text

    def find_ents(self):
        """Find all AF entities in the original text."""
        af_ents = []
        for line in self.og_text:
            match = re.findall(r'(\[.\..{4}\])', line)
            if match:
                af_ents.extend(match)

        # get highest occuring entity as main character
        random.shuffle(af_ents) # shuffle to avoid biasing first entity as MC
        mc_ent = max(set(af_ents), key = af_ents.count)
        return list(set(af_ents)), mc_ent

    def find_spec_ents(self):
        """Identifies entities and whether they are the subject or object in the sentence."""
        af_ents = {}
        for line in self.og_text:
            match = re.findall(r'(\[.\..{4}\])', line)
            if match:
                for i in range(len(match)):
                    if i == 0:
                        af_ents[match[i]] = 'subject'
                    elif match[i] not in af_ents:
                        af_ents[match[i]] = 'object'
                    
        return af_ents
    
    def get_ent_reps(self):
        """Get the symbol representations of the entities in the story"""
        return list(set([e[1] for e in self.ent_ids.keys()]))
    
    def find_verbs(self):
        """Find all verbs in the original text"""
        af_verbs = {}
        for i, line in enumerate(self.og_text):
            subj_ent = re.findall(r'(\[.\..{4}\])', line)
            for verb in AF_VERBS:
                if verb in line:
                    af_verbs[i] = (subj_ent[0], verb)
                    break # only take the first verb found
        return af_verbs


class FicGenome:
    """Object to store the genome info"""
    
    def __init__(self, story_file: str, mc: str, ent: dict = {}, verbs: dict = {}):
        """
        Initialize FicGenome
        
        Args:
            story_file: path to story file
            mc: main character string
            ent: {og_story_id: fic_rep_ent}
            verbs: {line: fic_rep_verb} (associated with line number in original story and verb_set)
        """
        self.story_file = story_file

        # entities and main character
        self.mc = mc
        self.mc_dat = get_assoc_dat(mc)
        self.ent = ent
        self.ent_encs = get_ent_encs(list(ent.values()))

        # verbs
        self.verbs = verbs

        # algorithm properties
        self.fitness = 0
        # self.fit_set = {'intra': 0, 'inter': 0, 'ent': 0, 'verb': 0}
        self.fit_set = {'inter': 0, 'ent': 0, 'verb': 0}
        self.genome = self.make_genome()

    # ----- MUTATION METHODS ----- #
    def assign_new_ents(self, story, form='random'):
        """Generates a new set of entities for the FicGenome object
        
        Args:
            story: AF_Story object
            form: 'random' | 'assoc'
        """
        new_ent = {}

        # assume the main character is already set
        mc_subjs = self.mc_dat['subj'][:] if self.mc_dat and form == 'assoc' else []
        mc_objs = self.mc_dat['obj'][:] if self.mc_dat and form == 'assoc' else []

        mc_subjs = list(set(mc_subjs) - {self.mc})  # remove the MC from associated subjects
        mc_objs = list(set(mc_objs) - {self.mc})    # remove the MC from associated objects

        random.shuffle(mc_subjs)
        random.shuffle(mc_objs)

        # reassign entities based on the associative data
        saved_ents = {}     # class symbol : {"ent": entity, 'ct': count}
        mc_symb = story.mc_ent[1]
        saved_ents[mc_symb] = {'ent': self.mc, 'ct': 1}   # always assign the MC to its symbol

        local_subjs = ALL_SUBJS[:]  # copy to avoid modifying the original list
        if self.mc and self.mc in local_subjs:
            local_subjs.remove(self.mc)  # remove the main character from the subject list

        local_objs = ALL_OBJS[:]  # copy to avoid modifying the original list
        if self.mc and self.mc in local_objs:
            local_objs.remove(self.mc)  # remove the main character from the object list
        
        for ent_id, ent_type in story.ent_ids.items():
            symbol = ent_id[1]   # get the symbol (e.g. A, b, 7, $, &, etc)

            if ent_id == story.mc_ent and self.mc is not None:      # assign the main character
                new_ent[ent_id] = self.mc
            elif symbol in saved_ents:                              # Reuse previously assigned entity if available
                new_ent[ent_id] = saved_ents[symbol]['ent'] + f"{saved_ents[symbol]['ct']+1}" #if ent_id != story.mc_ent else self.mc
                saved_ents[symbol]['ct'] += 1
                continue
            elif ent_type == 'subject':                             # assign subject entity
                if self.mc_dat and len(mc_subjs) > 0:
                    new_ent[ent_id] = mc_subjs.pop()
                else:
                    new_ent[ent_id] = random.choice(local_subjs)      # out of subject entities or random
            else:             # assign object entity    
                if self.mc_dat and len(mc_objs) > 0:
                    new_ent[ent_id] = mc_objs.pop()
                else:
                    new_ent[ent_id] = random.choice(local_objs)      # out of object entities


            added_ent = re.sub(r'[0-9]+', '', new_ent[ent_id])  # remove numbers from the entity

            if added_ent in local_subjs:  
                local_subjs.remove(added_ent)     # remove copies of the newly added entity

            if added_ent in local_objs:
                local_objs.remove(added_ent)      # remove copies of the newly added entity

            if added_ent in mc_objs: 
                mc_objs.remove(added_ent)        # remove copies of the newly added entity
            if added_ent in mc_subjs:
                mc_subjs.remove(added_ent)        # remove copies of the newly added entity

            if symbol not in saved_ents:
                saved_ents[symbol] = {'ent': new_ent[ent_id], 'ct': 1}

        # assign new entities
        self.ent = new_ent
        self.ent_encs = get_ent_encs(list(new_ent.values()))

    def assign_new_verbs(self, story, form='random', debug=False):
        """Generates a new set of verbs for the FicGenome object
        
        Args:
            story: AF_Story object
            form: 'random' | 'assoc'
            debug: print debug info
        """
        if debug:
            print(self.ent)

        new_verbs = {}
        for line, (subj_ent, og_verb) in story.verb_set.items():
            if form == 'random':        # assign random verb
                new_verbs[line] = random.choice(ALL_VERBS)
            elif form == 'assoc':       # assign associated verb to noun
                assoc_verbs = get_assoc_verbs(self.ent[subj_ent]) if subj_ent in self.ent and story.ent_ids[subj_ent] == 'subject' else []
                if len(assoc_verbs) > 0:
                    new_verbs[line] = random.choice(assoc_verbs)
                else:
                    new_verbs[line] = random.choice(ALL_VERBS)
        self.verbs = new_verbs

    def hard_mutate(self, story, mc_form='random', ent_form='random', verb_form='random'):
        """Mutates the FicGenome object COMPLETELY
        
        Args:
            story: AF_Story object
            mc: 'random' | 'same'
            ent: 'random' | 'assoc'
            verbs: 'random' | 'assoc'
        """
        self.genome = None # reset genome

        if mc_form == 'random':
            self.mc = random.choice(ALL_SUBJS)
            self.mc_dat = get_assoc_dat(self.mc)

        self.assign_new_ents(story, form=ent_form)      # assign new entities (random or associated)
        self.assign_new_verbs(story, form=verb_form)     # assign new verbs (random or associated)

        # remake the genome based on new values
        self.genome = self.make_genome()

    def mutate(self, story, mut_chance=0.25, ent_form='random', verb_form='random', debug=False):
        """Keeps the main character the same but any verb or entity has a chance to be randomly replaced 
        Does not use associated entities
        
        Args:
            story: AF_Story object
            mut_chance: probability of mutation for each element
            ent_form: 'random' | 'assoc'
            verb_form: 'random' | 'assoc'
            debug: print debug info
        """

        mc_subjs = self.mc_dat['subj'][:] if self.mc_dat and ent_form == 'assoc' else []
        mc_objs = self.mc_dat['obj'][:] if self.mc_dat and ent_form == 'assoc' else []

        full_set = list(set(mc_subjs + mc_objs))

        local_subjs = ALL_SUBJS[:]  # copy to avoid modifying the original list
        if self.mc and self.mc in local_subjs:
            local_subjs.remove(self.mc)  # remove the main character from the subject list

        local_objs = ALL_OBJS[:]  # copy to avoid modifying the original list
        if self.mc and self.mc in local_objs:
            local_objs.remove(self.mc)  # remove the main character from the object list

        random.shuffle(local_subjs)
        random.shuffle(local_objs)

        if debug:
            print(self.ent)

        # get all the unique entities and their associated ids
        unique_ents = {}
        for id, ent in self.ent.items():
            class_ent = re.sub(r'[0-9]+', '', ent)  # remove numbers from the entity
            if class_ent not in unique_ents:
                unique_ents[class_ent] = {'ids': [], 'ent_type': story.ent_ids[id]}
            elif unique_ents[class_ent]['ent_type'] == 'object' and story.ent_ids[id] == 'subject': # override the type
                unique_ents[class_ent]['ent_type'] = 'subject'

            if id != self.mc:
                unique_ents[class_ent]['ids'].append(id)

        if debug:
            print(unique_ents)

        # get all of the current entities in use and remove from possibilities as a new choice
        current_ents = []
        for e in self.ent.values():
            if e not in current_ents:
                current_ents.append(e)

        # remove the in-use entities from the local lists
        for e in current_ents:
            e = re.sub(r'[0-9]+', '', e)
            if e in local_subjs:
                local_subjs.remove(e)
            if e in local_objs:
                local_objs.remove(e)
            if e in mc_subjs:
                mc_subjs.remove(e)
            if e in mc_objs:
                mc_objs.remove(e)

        # change entity groups
        changed_ent = []
        new_ent = {}
        new_picks = []
        for class_ent, info in unique_ents.items():

            # change the entity group
            if random.random() < mut_chance:
                if info['ent_type'] == 'subject':
                    ne = mc_subjs.pop() if ent_form == 'assoc' and len(mc_subjs) > 0 else random.choice(local_subjs)
                    added_ent = re.sub(r'[0-9]+', '', ne)  # remove numbers from the entity
                    if added_ent in local_subjs:
                        local_subjs.remove(added_ent)
                    if added_ent in local_objs:
                        local_objs.remove(added_ent)
                    if added_ent in mc_objs:
                        mc_objs.remove(added_ent)

                    for i in range(len(info['ids'])):
                        new_ent[info['ids'][i]] = ne + f"{i+1}" if i > 0 else ne
                else:
                    ne = mc_objs.pop() if ent_form == 'assoc' and len(mc_objs) > 0 else random.choice(local_objs)
                    added_ent = re.sub(r'[0-9]+', '', ne)  # remove numbers from the entity
                    if added_ent in local_objs:
                        local_objs.remove(added_ent)
                    if added_ent in local_objs:
                        local_objs.remove(added_ent)
                    if added_ent in mc_objs:
                        mc_objs.remove(added_ent)

                    for i in range(len(info['ids'])):
                        new_ent[info['ids'][i]] = ne + f"{i+1}" if i > 0 else ne
                changed_ent.append(info['ids'][0])
                
            # keep the same
            else:
                for i in range(len(info['ids'])):
                    new_ent[info['ids'][i]] = self.ent[info['ids'][i]]
            

        if debug:
            print("~~ ~ ~ ~ ~ ~ ~ ~AA A A AS DSA SAD SADA ~ ~ ~ ~ ~ ~ ~ ~ ~")
            print(new_ent.values())
            

        if debug:
            print(f"# of changed entity groups: {len(changed_ent)} / {len(unique_ents)}")
            for id in self.ent.keys():
                if self.ent[id] != new_ent[id]:
                    print(f"{id}: {self.ent[id]} -> {new_ent[id]}")
            print("")

        # change verbs
        new_verbs = {}
        changed_verbs = 0
        for line, (subj_ent, og_verb) in story.verb_set.items():
            if random.random() < mut_chance:  # if this verb is to be changed
                if verb_form == 'assoc':
                    assoc_verbs = get_assoc_verbs(self.ent[subj_ent]) if subj_ent in self.ent else []
                    if len(assoc_verbs) > 0:
                        new_verb = random.choice(assoc_verbs)
                    else:
                        new_verb = random.choice(ALL_VERBS)
                else:
                    new_verb = random.choice(ALL_VERBS)
                new_verbs[line] = new_verb
                changed_verbs += 1
            else:
                new_verbs[line] = self.verbs[line]  # keep the original verb if not changed

        if debug:
            print(f"# of changed verbs: {changed_verbs} / {len(self.verbs)}")
            for id in self.verbs.keys():
                if self.verbs[id] != new_verbs[id]:
                    print(f"{id}: {self.verbs[id]} -> {new_verbs[id]}")
            print("")

        # set and re-embed
        self.ent = new_ent
        self.verbs = new_verbs
        self.ent_encs = get_ent_encs(list(self.ent.values()))
        self.genome = self.make_genome()

    # ------ NOVELTY / EVOLUTION METHODS ------ #
    def clone(self):
        """Returns a separate copy of this object"""
        new_fic = FicGenome(self.story_file, self.mc, {k: v for k, v in self.ent.items()}, {k: v for k, v in self.verbs.items()})
        new_fic.fitness = self.fitness
        new_fic.genome = self.genome
        new_fic.fit_set = {k: v for k, v in self.fit_set.items()}
        return new_fic

    def eval(self, af_story, debug=False, internal_debug=False):
        """Evaluates the fitness of the FicGenome object 
        Fitness is based on:
            - Semantic closeness of each sentence
            - Semantic closeness of the story sentences
            - Semantic closeness of the entities to the main character
            - Semantic closeness of the verb selection to the original verbs
        """

        # check if the correct story
        if af_story.log_file != self.story_file:
            print(f"Error: Story file mismatch. Expected {self.story_file}, got {af_story.log_file}")
            return 0

        # Intersentence cohesion score: Sentence-to-sentence cohesion score
        story_sentences = self.generate_story(af_story, out_file=None)
        embeddings = st_model.encode(story_sentences)

        # cohesion = average cosine similarity of consecutive pairs
        sims = []
        for i in range(len(embeddings) - 1):
            cos_sim = np.dot(embeddings[i], embeddings[i+1]) / (np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[i+1]))
            sims.append(float(cos_sim))
            if internal_debug:
                print(f"\t- Inter Sentence Cohesion ({i},{i+1}): {float(cos_sim):.4f}")
        inter_sentence_cohesion_score = float(np.mean(sims)) if sims else 0.0

        if debug:
            print(f"- Inter Cohesion: {inter_sentence_cohesion_score:.4f}")

        # # Intrasentence cohesion score: Within each sentence cohesion score
        # intra_scores = []
        # for sent in story_sentences:
        #     words = [tok.strip("[]") for tok in sent.replace("]", " [").split() if tok.strip()]

        #     embeddings = st_model.encode(words)
        #     # compute all pairwise similarities
        #     sims = []
        #     for i in range(len(embeddings)):
        #         for j in range(i + 1, len(embeddings)):
        #             cos_sim = np.dot(embeddings[i], embeddings[j]) / (np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j]))
        #             sims.append(float(cos_sim))
            
        #             if internal_debug:
        #                 print(f"\t- Inter Sentence Cohesion ({i},{j}): {float(cos_sim):.4f}")
                    
        #     intra_scores.append(float(np.mean(sims)))

        # intra_cohesion = float(np.mean(intra_scores)) if intra_scores else 0.0
        # if debug:
        #     print(f"- Intra Cohesion: {intra_cohesion:.4f}")

        # ENT SIMILARITY METRIC
        if len(self.ent_encs) == 0 or af_story.mc_ent not in self.ent:
            ent_score = 0
        else:
            mc_enc = pre_ent_enc.get(self.mc)
            if mc_enc is None:
                # Encode on-the-fly if not found in pre-encoded data
                mc_enc = st_model.encode(self.mc)
                if debug:
                    print(f"  Warning: Main character '{self.mc}' not in pre-encoded data, encoding on-the-fly")
            
            cos_sims = []
            for e, enc in self.ent_encs.items():
                if e == self.mc:        # skip the main character
                    continue
                if enc is None:         # skip entities with no encoding
                    continue
                cos_sim = np.dot(mc_enc, enc) / (np.linalg.norm(mc_enc) * np.linalg.norm(enc))
                cos_sims.append(cos_sim)

                if internal_debug:
                    print(f"\t- MC Ent: {self.mc} | Fic Ent: {e} | Cosine Sim: {float(cos_sim):.4f}")
            ent_score = float(np.mean(cos_sims)) if cos_sims else 0.0    # between 0? and 1
        if debug:
            print(f"- Ent Score: {ent_score:.4f}")

        # VERB SIMILARITY METRIC
        # get encodings for verbs
        og_verbs = list(af_story.verb_set.values())
        fic_verbs = list(self.verbs.values())
        og_verb_vecs = [af_verb_enc_dict[v[1]] for v in og_verbs]
        #fic_verb_vecs = [st_model.encode(v) for v in fic_verbs]
        fic_verb_vecs = []
        for v in fic_verbs:
            verb_enc = pre_verb_enc.get(v)
            if verb_enc is None:
                # Encode on-the-fly if not found in pre-encoded data
                verb_enc = st_model.encode(v)
                if debug:
                    print(f"  Warning: Verb '{v}' not in pre-encoded data, encoding on-the-fly")
            fic_verb_vecs.append(verb_enc)

        # get cosine similarity between verb sets
        cos_sims = []
        min_len = min(len(og_verb_vecs), len(fic_verb_vecs))
        for i in range(min_len):
            if fic_verb_vecs[i] is None or og_verb_vecs[i] is None:
                continue

            cos_sim = np.dot(og_verb_vecs[i], fic_verb_vecs[i]) / (np.linalg.norm(og_verb_vecs[i]) * np.linalg.norm(fic_verb_vecs[i]))
            cos_sims.append(cos_sim)

            if internal_debug:
                print(f"\t- OG Verb: {og_verbs[i][1]} | Fic Verb: {fic_verbs[i]} | Cosine Sim: {float(cos_sim):.4f}")

        verb_score = float(np.mean(cos_sims)) if cos_sims else 0.0 # between 0? and 1
        if debug:
            print(f"- Verb Score: {verb_score:.4f}")

        # set the fitness
        # self.fitness = (intra_cohesion + inter_sentence_cohesion_score + ent_score + verb_score) / 4.0
        # self.fitness = (inter_sentence_cohesion_score + ent_score + verb_score) / 3.0

        # self.fitness = (intra_cohesion * 0.4) + (inter_sentence_cohesion_score * 0.4) + (ent_score * 0.1) + (verb_score * 0.1)
        self.fitness = (inter_sentence_cohesion_score * 0.6) + (ent_score * 0.1) + (verb_score * 0.3)


        self.fit_set = {
            # 'intra': intra_cohesion,
            'inter': inter_sentence_cohesion_score,
            'ent': ent_score,
            'verb': verb_score
        }

        return self.fitness

    def make_genome(self):
        """Creates a representation of the genome (ents+verbs) 
        Uses a sentence embedding model from sentence-transformers to convert the genome to a vector
        for comparison with other genomes.
        """
        # all_words = list(self.ent.values()) + list(self.verbs.values())
        all_words = list(self.ent.values())
        all_words = ' '.join(all_words)
        genome = st_model.encode(all_words)
        return genome

    # ------ FILE I/O ------ #
    def generate_story(self, af_story, out_file: str = None):
        """Creates a story log based on the genome"""
        new_story = []
        for i, og_line in enumerate(af_story.og_text):
            new_line = og_line
            
            # Replace entities in the original line with their representations
            for ent_id, fic_rep in self.ent.items():
                new_line = new_line.replace(ent_id, f"[{fic_rep}]")

            # Replace verbs in the original line with their representations
            if i in self.verbs:
                af_story_verb = af_story.verb_set[i]
                fic_verb = self.verbs[i]
                new_line = new_line.replace(af_story_verb[1], fic_verb)

            new_story.append(new_line)

        # Write the modified line to the output file
        if out_file is not None:
            with open(out_file, 'w') as f:
                for line in new_story:
                    f.write(line + '\n')

        return new_story

    def export_fic(self, af_story, out_file: str = None):
        """Exports the data as a JSON file to reimport later"""
        fic_data = {
            'mc': self.mc,
            'ent': self.ent,
            'verbs': self.verbs,
            'fitness': self.fitness,
            'fit_set': self.fit_set,
            'story_file': self.story_file,
            'new_story': '\n'.join(self.generate_story(af_story)) if af_story is not None else None
        }
        if out_file is not None:
            with open(out_file, 'w') as f:
                json.dump(fic_data, f, indent=3)
        return fic_data

    def import_fic(self, dat):
        """Imports the data from a JSON file"""
        self.mc = dat['mc']
        self.ent = dat['ent']
        self.verbs = dat['verbs']
        self.fitness = dat['fitness']
        self.fit_set = dat['fit_set']
        self.story_file = dat['story_file']
        self.genome = self.make_genome()


# ===== ALGORITHM FUNCTIONS ===== #
def calculate_elite_count(pop_size, elite_percentage=0.05):
    """Calculate number of elites based on population size"""
    return max(1, int(pop_size * elite_percentage))


def init_population(size, story, main_char='random', others='random'):
    """Initializes a population of FicGenome objects based on the given AF_Story object 
    
    Args:
        size: population size
        story: AF_Story object
        main_char: 'random' | (specific entity representation)
        others: 'random' | 'assoc' (associated to mc)
    """
    population = []

    for _ in range(size):
        # choose a random MC from the entities in the story
        if main_char != "random" and main_char not in ALL_SUBJS:
            print(f"\t!!!    WARNING    !!!! Main character [{main_char}] not a possible subject in the graph. Defaulting to random choice.")

        mc = random.choice(ALL_SUBJS) if main_char == 'random' else main_char
        fic = FicGenome(story.log_file, mc)

        fic.assign_new_ents(story, form=others)      # assign new entities associated with the MC
        fic.assign_new_verbs(story, form=others)     # assign new verbs associated

        population.append(fic)

    return population


def is_novel(x, archive, threshold=0.5, debug=False):
    """Determines if a FicGenome object is novel compared to an archive of FicGenome objects"""
    if len(archive) == 0:       # nothing in the archive yet, so it's novel!
        return True

    # Get the minimum distance to any genome in the archive
    min_distance = float('inf')
    distances = []
    for a in archive:
        distance = np.linalg.norm(x.genome - a.genome)
        distances.append(distance)
        if distance < min_distance:
            min_distance = distance

    if debug:
        print(f"Distances: {distances}")

    # If the minimum distance is greater than the threshold, the genome is novel
    return min_distance >= threshold


def export_ns_archive(arx, out_file: str, story=None, output_dir='', sub_dir=None):
    """Exports the archive of FicGenome objects to a JSON file"""
    archive_data = [x.export_fic(story) for x in arx]
    with open(output_dir + out_file, 'w') as f:
        json.dump(archive_data, f, indent=3)


def novelty_search(af_log, params={}):
    """Main novelty search algorithm
    
    Args:
        af_log: path to the AF story log file
        params: dictionary of parameters for the algorithm
        
    Returns:
        tuple: (archive, best_fic, story)
    """
    # get parameters and set defaults
    init_main_char = params.get('main_char', 'random')
    init_other_ents = params.get('other_ents', 'random')

    mut_chance = params.get('mut_chance', 0.25)
    mut_main_char = params.get('mut_main_char', 'random')
    mut_other_ents = params.get('mut_other_ents', 'random')
    mut_verbs = params.get('mut_verbs', 'random')

    fit_threshold = params.get('fit_threshold', 0.5)
    novel_threshold = params.get('novel_threshold', 0.5)
    rand_perc = params.get('rand_perc', 0.2)
    elite_perc = params.get('elite_perc', 0.05)  # Default 5% elitism

    num_generations = params.get('num_generations', NUM_GENERATIONS)
    pop_size = params.get('pop_size', POP_SIZE)
    elite_count = calculate_elite_count(pop_size, elite_perc)

    # 0. Initialize story representation
    story = AF_Story(af_log)
    
    # 1. Initialize population and archive
    population = init_population(pop_size, story, main_char=init_main_char, others=init_other_ents)
    archive = []
    fitness_values = []

    best_fitness = 0
    archive_size = []
    best_fic = None

    for gen in range(num_generations):
        print(f"Generation {gen+1} / {num_generations} -- [Overall Best Fitness: {best_fitness:.3f} | Archive Size: {len(archive)}]")

        # 8. Repeat 2-7 for NUM_GENERATIONS
        for indiv in population:

            # 2. Evaluate fitness
            indiv.eval(story)

            # 3+4. Evaluate novelty against archive and add if novel and fit enough
            if is_novel(indiv, archive, novel_threshold) and indiv.fitness > fit_threshold:
                archive.append(indiv.clone())

        # print some stats
        population.sort(key=lambda x: x.fitness, reverse=True)
        fit_scores = [indiv.fitness for indiv in population]
        print(f"  Pop Fitness: max {max(fit_scores):.3f}, min {min(fit_scores):.3f}, avg {sum(fit_scores)/len(fit_scores):.3f}")

        if gen % max(1, num_generations // 20) == 0:
            print("   FicGenome of best population individual:")
            print(f"     - Best MC: {population[0].mc}")
            print(f"     - Best Ents: {list(population[0].ent.values())}")
            print(f"     - Best Verbs: {set(population[0].verbs.values())}")

        if population[0].fitness > best_fitness:
            best_fitness = population[0].fitness
            best_fic = population[0].clone()
            print(f"  New best fitness: {best_fitness:.3f}")

        # Extract elites before creating new population
        elites = [indiv.clone() for indiv in population[:elite_count]]

        # 5. Select new parents from novelty archive
        # Adjust parent count to account for elites
        parent_count = int((pop_size - elite_count) * (1 - rand_perc))
        if len(archive) > 0:
            parents = random.choices(archive, k=parent_count)
        else:
            parents = random.choices(population, k=parent_count)

        # 6. Mutate children from parents
        new_pop = elites[:]  # Start with elites
        for parent in parents:
            child = parent.clone()
            child.mutate(story, mut_chance=mut_chance, ent_form=mut_other_ents, verb_form=mut_verbs, debug=False)
            new_pop.append(child)

        # 7. Add random individuals
        random_count = pop_size - len(new_pop)
        if random_count > 0:
            randos = init_population(random_count, story, main_char=init_main_char, others=init_other_ents)
            new_pop.extend(randos)

        fitness_values.append(f"{population[0].fitness:.3f}")
        archive_size.append(len(archive))

        # update population
        population = new_pop
        

    return archive, best_fic, story, fitness_values, archive_size


def export_me_archive(arx, out_file: str, story=None, output_dir=''):
    """Exports the archive of FicGenome objects (from MAP-Elites experiment) to a JSON file"""
    archive_data = {}
    for k, v in arx.items():
        archive_data[k] = [x.export_fic(story) for x in v]
    with open(output_dir + out_file, 'w') as f:
        json.dump(archive_data, f, indent=3)


def map_elites(af_log, params={}):
    """Main MAP-Elites algorithm
    
    Args:
        af_log: path to the AF story log file
        params: dictionary of parameters for the algorithm
        
    Returns:
        tuple: (archive, best_fic, story)
    """
    # get parameters and set defaults
    init_main_char = params.get('main_char', 'random')
    init_other_ents = params.get('other_ents', 'random')

    mut_chance = params.get('mut_chance', 0.25)
    mut_main_char = params.get('mut_main_char', 'random')
    mut_other_ents = params.get('mut_other_ents', 'random')
    mut_verbs = params.get('mut_verbs', 'random')

    rand_perc = params.get('rand_perc', 0.2)
    elite_perc = params.get('elite_perc', 0.05)  # Default 5% elitism
    arx_cell_size = params.get('arx_cell_size', 5)

    num_generations = params.get('num_generations', NUM_GENERATIONS)
    pop_size = params.get('pop_size', POP_SIZE)
    elite_count = calculate_elite_count(pop_size, elite_perc)

    # 0. Initialize story representation
    story = AF_Story(af_log)
    
    # 1. Initialize population and archive
    population = init_population(pop_size, story, main_char=init_main_char, others=init_other_ents)
    archive = {}        # based on best fit_set (inter, intra, noun, verb cohesions)

    best_fitness = 0
    best_fic = None
    fitness_values = []

    for gen in range(num_generations):
        arx_fit = {f: f"{s[0].fit_set[f]:.3f} [fit={s[0].fitness:.3f}]" for f, s in archive.items()} if len(archive) > 0 else {}
        print(f"Generation {gen+1} / {num_generations} \n-- [Overall Best Fitness: {best_fitness:.3f} | Archive: {arx_fit}]\n")

        # 8. Repeat 2-7 for NUM_GENERATIONS
        for indiv in population:

            # 2. Evaluate fitness
            indiv.eval(story)

            # 3+4. Evaluate fitness set scores and assign to archive
            fit_set = indiv.fit_set
            for f, v in fit_set.items():
                if f not in archive:            # initialize archive cell
                    archive[f] = []
                if len(archive[f]) == 0 or v > archive[f][-1].fit_set[f]:       # add if better than last element in the list
                    archive[f].append(indiv.clone())

                # sort and remove the lowest fitness
                archive[f] = sorted(archive[f], key=lambda x: x.fit_set[f], reverse=True)[:arx_cell_size]

        # print some stats
        population.sort(key=lambda x: x.fitness, reverse=True)
        fit_scores = [indiv.fitness for indiv in population]
        print(f"  Pop Fitness: max {max(fit_scores):.3f}, min {min(fit_scores):.3f}, avg {sum(fit_scores)/len(fit_scores):.3f}")

        if gen % max(1, num_generations // 20) == 0:
            print("   FicGenome of best population individual:")
            print(f"     - Best MC: {population[0].mc}")
            print(f"     - Best Ents: {list(population[0].ent.values())}")
            print(f"     - Best Verbs: {set(population[0].verbs.values())}")

        if population[0].fitness > best_fitness:
            best_fitness = population[0].fitness
            best_fic = population[0].clone()
            print(f"  New best fitness: {best_fitness:.3f}")

        # Extract elites before creating new population
        elites = [indiv.clone() for indiv in population[:elite_count]]

        # 5. Select new parents from novelty archive
        # Adjust parent count to account for elites
        parent_count = int((pop_size - elite_count) * (1 - rand_perc))
        if len(archive) > 0:
            arx_stories = [s for sublist in archive.values() for s in sublist]
            parents = random.choices(arx_stories, k=parent_count)
        else:
            parents = random.choices(population, k=parent_count)

        # 6. Mutate children from parents
        new_pop = elites[:]  # Start with elites
        for parent in parents:
            child = parent.clone()
            child.mutate(story, mut_chance=mut_chance, ent_form=mut_other_ents, verb_form=mut_verbs)
            new_pop.append(child)

        # 7. Add random individuals
        random_count = pop_size - len(new_pop)
        if random_count > 0:
            randos = init_population(random_count, story, main_char=init_main_char, others=init_other_ents)
            new_pop.extend(randos)


        fitness_values.append(f"{population[0].fitness:.3f}")
        # update population
        population = new_pop

    return archive, best_fic, story, fitness_values, None

def run_algorithm(algorithm, story_file, CONFIG_FILE=None, export=True, experiment_name=None, set_mc=None):
    if CONFIG_FILE:
        try:
            with open(CONFIG_FILE, 'r') as f:
                NOV_PARAMS = yaml.safe_load(f)
        except Exception as e:
            print("Unable to load Config File")
            print(e)

    if set_mc:
        NOV_PARAMS['main_char'] = set_mc
        print(f"Setting main character to {set_mc}")
        
    story_name = story_file.split('/')[-1].replace('.txt', '')
    
    if algorithm == "novelty_search":
        arc, best_fic, story, fitness_values, archive_size = novelty_search(story_file, params=NOV_PARAMS)
    
    elif algorithm == "map_elites":
         arc, best_fic, story, fitness_values, archive_size = map_elites(story_file, params=NOV_PARAMS)

    if export:
        timestamp = datetime.datetime.now().strftime("%m-%d-%Y_%H%M")
        # save the best fic story
        folder_name = f"{story_name}_{timestamp}_{NOV_PARAMS['pop_size']}_{NOV_PARAMS['num_generations']}"
        if experiment_name:
            folder_name = f"{experiment_name}_{folder_name}"


        os.makedirs(f'experiments/{algorithm}/{folder_name}', exist_ok=True)
        best_fic.export_fic(story, out_file=f'experiments/{algorithm}/{folder_name}/best_genome.json')
        if algorithm == "novelty_search":
            export_ns_archive(arc, out_file=f'experiments/{algorithm}/{folder_name}/archive.json', story=story)
        elif algorithm == "map_elites":
            export_me_archive(arc, out_file=f'experiments/{algorithm}/{folder_name}/archive.json', story=story)
        bf_story = best_fic.generate_story(story, out_file=f'experiments/{algorithm}/{folder_name}/best_story.txt')

        plot_graph(fitness_values, "Generation", "Fitness", file_path=f'experiments/{algorithm}/{folder_name}/fitness_plot.png')
        if archive_size:
            plot_graph(archive_size, "Generation", "Archive Size", file_path=f'experiments/{algorithm}/{folder_name}/archive_size_plot.png')

if __name__ == "__main__":
    # Example of how to use the module
    print("Setting up models and data...")
    setup_models_and_data(data_path='bank_files')

    print("Pre-encoding the entities and verbs...")
    pre_encode_data(use_file=True)
    CONFIG_FILE = sys.argv[1] if len(sys.argv) > 1 else 'exp_config/fixed_mc_assoc_experiment.yaml'

    run_algorithm("map_elites", 'sifted_logs/drunk_sokoban.txt', CONFIG_FILE=CONFIG_FILE, export=True, set_mc='person')