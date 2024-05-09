import en_core_web_sm
import spacy

from api.basic_api import use_api_get_prototype


def word_revert(word: str) -> str:
    """
    使用spacy模型获取单词原型
    """
    nlp = spacy.load("en_core_web_sm")

    doc = nlp(word)
    for token in doc:
        # 转换失败，调用官方接口获取
        if token.lemma_ == word:
            return use_api_get_prototype(word)
        # 转换成功
        return token.lemma_
