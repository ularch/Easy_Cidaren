import en_core_web_sm
import spacy

from api.basic_api import use_api_get_prototype
from log.log import Log

nlp = en_core_web_sm.load()


def word_revert(word: str) -> str:
    """
    优先使用模型转原型
    :param word: 目标单词
    :return: 原型
    """

    nlp = spacy.load("en_core_web_sm")
    module = Log("word_revert")
    module.logger.info(f"{word}优先使用模型转原型")
    doc = nlp(word)
    for token in doc:
        # 失败
        if token.lemma_ == word:
            module.logger.info("模型转原型失败")
            # 单词就是原型，直接返回（或许）
            # return word
            return use_api_get_prototype(word)
        # 成功
        return token.lemma_


if __name__ == '__main__':
    print(word_revert('done'))