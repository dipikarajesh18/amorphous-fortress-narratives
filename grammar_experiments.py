from nltk.corpus import wordnet as wn

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

print(wn.synsets('moved', pos=wn.VERB))

