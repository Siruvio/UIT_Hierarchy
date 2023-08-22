from typing import Optional


class InfoNode:
    def __init__(self, lemma: str = "", synonyms: [str] = None, verbs: [str] = None,
                 father: 'InfoNode' = None, index: int = -1) -> None:
        self.__index = index
        self.__name = lemma.lower()
        self.__synonyms = synonyms if synonyms else []
        self.__hypers = []
        self.__verbs = verbs if verbs else []

        self.__father = father
        self.__children = []

        if self.__father:
            self.update_hypers()

    # --- Instance index
    # Index Setter
    def set_index(self, index: int) -> None:
        self.__index = index

    # Index Getter
    def get_index(self) -> int:
        return self.__index

    # --- Instance name
    # Name Setter
    def set_name(self, lemma: str) -> None:
        self.__name = lemma

    # Name Getter
    def get_name(self) -> str:
        return self.__name

    # --- Synonyms
    # Check if synonyms list is empty
    # True = empty
    def is_synonyms_empty(self) -> bool:
        return not self.__synonyms

    # Synonyms Setter (list of strings)
    def set_synonyms(self, synonyms: [str]) -> None:
        if not self.is_synonyms_empty():
            for item in synonyms:
                if item not in self.__synonyms:
                    self.__synonyms.append(item)
        else:
            self.__synonyms = synonyms

        self.__synonyms.sort()

    # Synonyms Setter (single string)
    def add_synonym(self, synonym: str) -> None:
        if synonym not in self.__synonyms:
            self.__synonyms.append(synonym)
            self.__synonyms.sort()

    # Synonyms Getter
    def get_synonyms(self) -> [str]:
        return self.__synonyms

    # --- Categorization
    # Check if hypers list is empty
    # True = empty
    def is_hypers_empty(self) -> bool:
        return not self.__hypers

    # Hypers Setter (list of strings)
    def set_hypers(self, hypers: [str], force_update: bool = False) -> None:
        if not self.is_hypers_empty() and not force_update:
            for item in hypers:
                if item not in self.__hypers:
                    self.__hypers.append(item)
        else:
            self.__hypers = hypers

    # Update hypers list looking recursively in fathers
    def update_hypers(self) -> None:
        temp_list = []
        explored_node = self.__father
        if explored_node:
            while explored_node is not None:
                temp_list.append(explored_node.get_name())
                explored_node = explored_node.get_father()
            self.set_hypers(hypers=temp_list, force_update=True)

    # Hypers Getter
    def get_hypers(self) -> [str]:
        return self.__hypers

    # --- Verbs
    # Check if verbs list is empty
    # True = empty
    def is_verbs_empty(self) -> bool:
        return not self.__verbs

    # Verbs Setter (list of strings)
    def set_verbs(self, verbs: [str]) -> None:
        if not self.is_verbs_empty():
            for item in verbs:
                if item not in self.__verbs:
                    self.__verbs.append(item)
        else:
            self.__verbs = verbs

        self.__verbs.sort()

    # Verbs Setter (single string)
    def add_verb(self, verb: str) -> None:
        if verb not in self.__verbs:
            self.__verbs.append(verb)
            self.__verbs.sort()

    # Remove a single verb
    def remove_verb(self, verb: str) -> None:
        if verb in self.__verbs:
            self.__verbs.remove(verb)

    # Remove a list of verbs
    def remove_verbs(self, verb_list: [str]) -> None:
        for verb in verb_list:
            if verb in self.__verbs:
                self.__verbs.remove(verb)

    # Verbs Getter (only verbs in node)
    def get_personal_verbs(self) -> [str]:
        return self.__verbs

    # Verbs Getter (all verbs, included those in fathers)
    def get_all_verbs(self) -> [str]:
        returned_list = []
        explored_node = self.__father

        for verb in self.__verbs:
            returned_list.append(verb)

        while explored_node.get_father() is not None:
            for verb in explored_node.get_personal_verbs():
                if verb not in returned_list:
                    returned_list.append(verb)
            explored_node = explored_node.get_father()

        returned_list.sort()
        return returned_list

    # --- Father node
    # Father Setter
    def set_father(self, father: Optional['InfoNode']) -> None:
        self.__father = father
        self.update_hypers()

    # Father Getter
    def get_father(self) -> 'InfoNode':
        return self.__father

    # --- Children
    # Children Setter (single node of class InfoNode)
    def add_child(self, child: 'InfoNode') -> None:
        self.__children.append(child)

    # Children Getter
    def get_children(self) -> ['InfoNode']:
        return self.__children

    # Search in children list by lemma
    def get_child_by_lemma(self, name: str) -> Optional['InfoNode']:
        children = [child for child in self.__children
                    if child.get_name() == name]
        if children:
            return children[0]
        else:
            return None

    # Search in children list by synonyms
    def get_child_by_synonym(self, name: str) -> Optional['InfoNode']:
        children = [child for child in self.__children
                    if name in child.get_synonyms()]

        if children:
            return children[0]
        else:
            return None

    # Remove child passing object
    def remove_child(self, child: 'InfoNode') -> None:
        if child in self.__children:
            self.__children.remove(child)
