from classes import *
import json
from nltk.corpus import wordnet as wn
import copy
from pathlib import Path


def sorting(filename: str, print_out: bool = False) -> dict:
    path = Path(__file__).parent / filename

    # Carica dati da organizzare
    with open(path) as in_file:
        data_set = in_file.read()
    data_set = json.loads(data_set)

    sorted_data = {}

    for item in data_set:
        category = item["Category"]
        lemma = item["Lemma"]
        verb = item["Verb"]

        # Categoria già presente
        if category != "Other":
            if category in sorted_data:
                # Verifica lemma
                if lemma in sorted_data[category]["Lemmas"]:
                    # Lemma già presente, aggiungi il verbo alla lista se non presente
                    if verb not in sorted_data[category]["Lemmas"][lemma]:
                        sorted_data[category]["Lemmas"][lemma].append(verb)
                        sorted_data[category]["Lemmas"][lemma].sort()  # Sort
                else:
                    # Lemma nuovo, aggiungi una lista per i verbi
                    sorted_data[category]["Lemmas"][lemma] = [verb]
                    sorted_data[category]["Lemmas"] = dict(sorted(sorted_data[category]["Lemmas"].items()))  # Sort

                # Verifica verbo
                if verb in sorted_data[category]["Verbs"]:
                    # Verbo già presente, aggiungi il lemma alla lista se non presente
                    if lemma not in sorted_data[category]["Verbs"][verb]:
                        sorted_data[category]["Verbs"][verb].append(lemma)
                        sorted_data[category]["Verbs"][verb].sort()  # Sort
                else:
                    # Verbo nuovo, aggiungi una lista per i lemmi
                    sorted_data[category]["Verbs"][verb] = [lemma]
                    sorted_data[category]["Verbs"] = dict(sorted(sorted_data[category]["Verbs"].items()))  # Sort

            else:
                # Categoria da aggiungere
                sorted_data[category] = {                   # Aggiungi nuova categoria
                    "Lemmas": {lemma: [verb]},              # Aggiungi primo lemma e verbo associato
                    "Verbs": {verb: [lemma]}                # Aggiungi primo verbo e lemma associato
                }

    sorted_data = dict(sorted(sorted_data.items()))  # Sort

    if print_out:
        items = ["Lemmas", "Verbs"]
        for item in items:
            output_name = f"Data/Sort_by_{item}.json"
            path = Path(__file__).parent / output_name

            output_dict = {}
            for key in sorted_data:
                output_dict[key] = dict(sorted_data[key][item])

            output_json = json.dumps(output_dict)
            output_json = output_json.replace(": {", ": {\n\t")
            output_json = output_json.replace("}, ", "\n},\n")
            output_json = output_json.replace("], ", "],\n\t")

            with open(path, "w") as out_file:
                out_file.write(output_json)

    return sorted_data


def tree_construct(dataset: dict, out_index: int, print_out: bool = False) -> InfoNode:
    data_archive = []

    tree_root = InfoNode(lemma="Object", index=0)
    data_archive.append(tree_root)

    for category in dataset:
        category_root = InfoNode(lemma=category, father=tree_root)
        data_archive.append(category_root)
        tree_root.add_child(category_root)
        lemmas_list = dataset[category]["Lemmas"]

        for lemma in lemmas_list:
            # Ottieni la lista di categorie del lemma secondo WordNet
            hyper_list = recursive_hypernyms(lemma=lemma, category=category.lower())

            # Ottieni la lista di sinonimi del lemma secondo WordNet
            synonyms = get_synonyms(lemma=lemma, category=category.lower())

            if hyper_list and (hyper_list[0] == category.lower()):
                explored_node = category_root

                # Per ogni elemento della lista iperonimi (ogni elemento è figlio del precedente in lista,
                # e l'elemento con indice zero è la categoria)
                for sub_cat in hyper_list[1:]:
                    # Cerca tra i figli del nodo corrente uno che abbia nome uguale all'elemento in esame
                    child = explored_node.get_child_by_lemma(name=sub_cat)

                    # Se non è stato trovato un nodo, riprova la ricerca
                    # cercando il lemma tra i sinonimi dei singoli nodi
                    if child is None:
                        child = explored_node.get_child_by_synonym(name=sub_cat)

                    # Se è stato trovato un elemento, selezionalo per continuare
                    if child is not None:
                        explored_node = child
                    # Se non è stato trovato un elemento, crea un nuovo nodo, aggiungilo e selezionalo per continuare
                    else:
                        new_node = InfoNode(lemma=sub_cat, father=explored_node)
                        data_archive.append(new_node)
                        explored_node.add_child(new_node)

                        explored_node = new_node

                # Alla fine della categoria, verifica se esiste già un nodo con lo stesso lemma
                new_node = explored_node.get_child_by_lemma(name=lemma)

                # Se non è stato trovato nulla, prova a cercare se il lemma corrente è un sinonimo di uno dei nodi
                if new_node is None:
                    new_node = explored_node.get_child_by_synonym(name=lemma)

                # Se il nodo con nome o sinonimo pari a lemma esiste già,
                # aggiornalo aggiungendo verbi, iperonimi e sinonimi
                if new_node is not None:
                    new_node.set_verbs(lemmas_list[lemma])
                    new_node.set_hypers(hyper_list)
                    new_node.set_synonyms(synonyms)

                # Se il nodo con nome o sinonimo pari al lemma non esiste,
                # crealo da capo
                else:
                    new_node = InfoNode(lemma=lemma, verbs=lemmas_list[lemma], father=explored_node)
                    data_archive.append(new_node)
                    new_node.set_hypers(hyper_list)
                    new_node.set_synonyms(synonyms)

                    explored_node.add_child(new_node)

        recursive_refine_tree(key_node=category_root)
        recursive_clear(key_node=category_root)

    # Index all elements in data_archive
    if len(data_archive) > 1:
        for item in data_archive:
            index = data_archive.index(item)
            item.set_index(index)

    # Verbose out
    if print_out:
        output_name = f"Data/02/Hierarchy_Tree_{out_index}.json"
        path = Path(__file__).parent / output_name

        out_tree_string = recursive_print_out(tree_node=tree_root)

        with open(path, "w") as out_file:
            out_file.write(out_tree_string)

    # Json output
    if data_archive:
        output_name = "Data/Clean_data.json"
        path = Path(__file__).parent / output_name

        with open(path, "w") as out_file:
            out_file.write("[")

            for item in data_archive:
                out_string = "{"
                out_string += "\"Index\": " + str(item.get_index()) + ", "
                out_string += "\"Name\": \"" + item.get_name() + "\", "

                synonyms_string = str(item.get_synonyms()).replace("\'", "\"")
                out_string += "\"Synonyms\": " + synonyms_string + ", "

                hypers_string = str(item.get_hypers()).replace("\'", "\"")
                out_string += "\"Hypers\": " + hypers_string + ", "

                verbs_string = str(item.get_personal_verbs()).replace("\'", "\"")
                out_string += "\"Verbs\": " + verbs_string + ", "

                father = item.get_father()
                if father:
                    father_id = father.get_index()
                else:
                    father_id = -1
                out_string += "\"Father\": " + str(father_id) + ", "

                children = item.get_children()
                if children:
                    counter = 1
                    children_string = "["
                    for child in children:
                        children_string += str(child.get_index())
                        if counter < len(children):
                            children_string += ", "
                            counter += 1
                    children_string += "]"
                else:
                    children_string = "[]"
                out_string += "\"Children\": " + children_string

                out_string += "}"
                if data_archive.index(item) < (len(data_archive) - 1):
                    out_string += ","

                out_file.write(out_string + "\n")

            out_file.write("]")

    return tree_root


def recursive_hypernyms(lemma: str, category: str) -> [str]:
    # Recupera i synset del lemma
    synsets = wn.synsets(lemma, pos=wn.NOUN)

    # Se il lemma è ricondotto a più synset, scegli il primo che sia il più vicino possibile alla categoria
    if len(synsets) > 1:
        chosen_ss = None
        min_depth = 99

        for ss in synsets:
            # Per ogni possibile synset, cerca se nella sua gerarchia è presente la categoria.
            # Se è presente, salva le distanze a cui il synset della categoria si trova.
            distances = [item[1] for item in ss.hypernym_distances()
                         if item[0].name().split(".")[0] == category]

            # Se hai almeno un elemento, ottieni la distanza minima
            if distances:
                minimum = min(distances)

                # Se la minima di questo iperonimo è più bassa di quella salvata, tieni questo.
                if minimum < min_depth:
                    min_depth = minimum
                    chosen_ss = ss

        # Assegna il synset scelto
        if chosen_ss is not None:
            synsets = chosen_ss
        else:
            return []

    elif len(synsets) == 1:
        synsets = synsets[0]
    else:
        return []

    # Recupera gli iperonimi del synset
    hypers = synsets.hypernyms()

    # Se il synset è ricondotto a più iperonimi, scegli il primo che sia il più vicino possibile alla categoria
    if len(hypers) > 1:
        chosen_hn = ""  # supp
        min_depth = 99  # supp

        for hn in hypers:
            # Per ogni possibile iperonimo, cerca se nella sua gerarchia è presente la categoria.
            # Se è presente, salva le distanze a cui il synset della categoria si trova.
            distances = [item[1] for item in hn.hypernym_distances()
                         if item[0].name().split(".")[0] == category]

            # Se hai almeno un elemento, ottieni la distanza minima
            if distances:
                minimum = min(distances)

                # Se la minima di questo iperonimo è più bassa di quella salvata, tieni questo.
                if minimum < min_depth:
                    min_depth = minimum
                    chosen_hn = hn

        # Rendi l'iperonimo scelto l'unico della lista
        hypers = [chosen_hn]

    hypers = hypers[0]
    hyper_name = hypers.name().split(".")[0]

    if hyper_name != category:
        returned_list = recursive_hypernyms(lemma=hyper_name, category=category)
    else:
        returned_list = []

    returned_list.append(hyper_name)
    return returned_list


def get_synonyms(lemma: str, category: str) -> [str]:
    synsets = wn.synsets(lemma, pos=wn.NOUN)
    synonyms = []

    # Per ogni synset restituito da wordnet
    for ss in synsets:
        # Se il synset ha nella gerarchia d'iperonimi la categoria
        hypers = [item[0].name().split(".")[0] for item in ss.hypernym_distances()]
        if category in hypers:

            # Estrai tutti i sinonimi e aggiungili alla lista
            supp = ss.lemma_names()
            for syn in supp:
                if syn not in synonyms:
                    synonyms.append(syn)

    synonyms.sort()
    return synonyms


def recursive_refine_tree(key_node: InfoNode) -> None:
    children_list = key_node.get_children()
    if children_list:
        for child in children_list:
            recursive_refine_tree(key_node=child)

        # Se il nodo ha solo un figlio, nessun sinonimo e nessun verbo personale,
        # allora è solo un riempitivo aggiunto alla costruzione dell'albero, ma mai realmente utile.
        # Rendi il figlio uno dei figli del padre di questo nodo (e viceversa), poi elimina questo nodo
        if (len(children_list) == 1) and (not key_node.get_synonyms()) and (not key_node.get_personal_verbs()):
            child = children_list[0]
            father = key_node.get_father()

            father.add_child(child)
            father.remove_child(key_node)
            child.set_father(father)
            key_node.set_father(None)

        # Se il nodo ha almeno due figli:
        elif len(children_list) >= 2:

            # Prendi i verbi del primo, verifica che siano in tutti gli altri figli,
            # e poi aggiungi i restanti alla lista del nodo.
            possible_verbs = copy.deepcopy(children_list[0].get_personal_verbs())

            for child in children_list[1:]:
                child_verb_list = child.get_personal_verbs()

                index = 0
                while index < len(possible_verbs):
                    verb = possible_verbs[index]
                    if verb not in child_verb_list:
                        possible_verbs.remove(verb)
                    else:
                        index += 1

            if possible_verbs:
                key_node.set_verbs(possible_verbs)


def recursive_clear(key_node: InfoNode) -> None:
    # Se il nodo non ha sinonimi, cercali e aggiungili.
    if not key_node.get_synonyms():
        category = key_node.get_hypers()
        if category:
            category = category[-1]
        else:
            category = key_node.get_name()

        supp = get_synonyms(lemma=key_node.get_name(), category=category)
        key_node.set_synonyms(synonyms=supp)

    # Aggiorna la lista degli hypers dopo tutti i cambiamenti precedenti
    key_node.update_hypers()

    # Recupera la lista di verbi da rimuovere dai figli
    key_verbs = key_node.get_all_verbs()

    # Passo ricorsivo: esegui l'aggiornamento in ciascun figlio
    for child in key_node.get_children():
        child.remove_verbs(key_verbs)
        recursive_clear(key_node=child)


def recursive_print_out(tree_node: InfoNode, tabs: int = 0) -> str:
    tabs_str = "\t"*tabs

    composed_string = tabs_str + "{"
    composed_string += "\"Name\": \"" + tree_node.get_name() + "\",\n"

    synonyms_string = str(tree_node.get_synonyms()).replace("\'", "\"")
    composed_string += tabs_str + " \"Synonyms\": " + synonyms_string + ",\n"

    hypers_string = str(tree_node.get_hypers()).replace("\'", "\"")
    composed_string += tabs_str + " \"Hypers\": " + hypers_string + ",\n"

    verbs_string = str(tree_node.get_personal_verbs()).replace("\'", "\"")
    composed_string += tabs_str + " \"Verbs\": " + verbs_string + ",\n"

    father = tree_node.get_father()
    if father:
        father_name = father.get_name()
    else:
        father_name = "ROOT"
    composed_string += tabs_str + " \"Father\": \"" + father_name + "\",\n"

    children = tree_node.get_children()
    if children:
        index = 1
        children_string = "[\n"
        for child in children:
            children_string += recursive_print_out(tree_node=child, tabs=tabs+1)
            if index < len(children):
                children_string += ",\n"
                index += 1
            else:
                children_string += "\n"
        children_string += tabs_str + "]"
    else:
        children_string = "[]"
    composed_string += tabs_str + " \"Children\": " + children_string + "\n"

    composed_string += tabs_str + "}"

    return composed_string
