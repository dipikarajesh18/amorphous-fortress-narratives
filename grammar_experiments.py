#from nltk.corpus import wordnet as wn
import spacy
import requests

# key: Key: E -- entity (symbol.id),  N -- same entity (symbol.new id), O -- other entity, P - position (x,y), Q -- other position
log_set = [
        "[E_] moved to (P_)",   
        "[E_] died",
        "[E_] cloned to [N_] at (Q_)",
        "[E_] took [O_]",
        "[E_] moved to (P_) [target: (Q_)]",
        "[E_] pushed [O_]",
        "[E_] added [O_] at (Q_)",
        "[E_] transformed into [O_] at (P_)",
        "[E_] blocked by wall [O_]"
    ]



#print(wn.synsets('moved', pos=wn.VERB))


# set up spacy with concepcy
nlp = spacy.load("en_core_web_sm")
noun_rel = ["RelatedTo", "PartOf", "IsA", "HasA", "MadeOf", "Synonym", "Antonym"]
verb_rel = ["UsedFor", "CapableOf"]

def get_conceptnet(word,rel):
    obj = requests.get(f"https://api.conceptnet.io/c/en/{word}?limit=100/r/{rel}").json()
    return obj

def get_nouns(word):
    noun_set = []
    obj = get_conceptnet(word)
    for edge in obj['edges']:
        # skip non-English edges
        if 'language' in edge['end'] and edge['end']['language'] != 'en':
            continue
        if edge['rel']['label'] in noun_rel:
            noun_set.append(edge['end']['label'])
    return list(set(noun_set))

def get_verbs(word):
    verb_set = []
    obj = get_conceptnet(word)
    for edge in obj['edges']:
        # skip non-English edges
        if 'language' in edge['end'] and edge['end']['language'] != 'en':
            continue
        #print(edge['rel']['label'])
        if edge['rel']['label'] in verb_rel:
            verb_set.append(edge['end']['label'])
    return list(set(verb_set))

#print(get_verbs("book"))
#print(get_nouns("book"))


get_conceptnet("book","UsedFor")