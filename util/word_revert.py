import en_core_web_sm
import spacy

from api.basic_api import use_api_get_prototype

nlp = en_core_web_sm.load()


def word_revert(word: str) -> str:
    nlp = spacy.load("en_core_web_sm")

    doc = nlp(word)
    for token in doc:
        # fail
        if token.lemma_ == word:
            return use_api_get_prototype(word)
        # success
        return token.lemma_


if __name__ == '__main__':
    print(word_revert('installed'))
