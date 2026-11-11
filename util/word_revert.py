import os

from api.basic_api import use_api_get_prototype
from log.log import Log

# 使用本地目录的模型，便于打包
current_dir = os.path.dirname(os.path.abspath(__file__))
# 上一级目录
parent_dir = os.path.dirname(current_dir)
model_path = os.path.join(parent_dir, 'en_core_web_sm')
module = Log("word_revert")

_nlp = None
_model_broken = False

if not os.path.exists(model_path):
    module.logger.error(f"模型文件夹不存在: {model_path}")
elif not os.listdir(model_path):
    module.logger.error(f"模型文件夹为空: {model_path}")
else:
    module.logger.info(f"模型加载成功{model_path}")


def _load_model():
    global _nlp, _model_broken
    if _nlp is not None:
        return _nlp
    if _model_broken:
        raise RuntimeError("spaCy 模型当前不可用")
    try:
        import spacy
        _nlp = spacy.load(model_path)
    except Exception:
        _model_broken = True
        raise
    return _nlp


def word_revert(word: str, sentence: str = None) -> str:
    """
    模型转原型（兜底用；主力是 util.word_form.match_in_list 的规则还原）
    :param word: 目标单词
    :param sentence: 可选，包含该词的整句（实测对本模型帮助有限：decreed 仍返回 decreed）
    :return: 原型；模型不可用时退回原词
    """
    if _model_broken:
        return word
    try:
        nlp = _load_model()
        module.logger.info(f"{word}优先使用模型转原型")
        # 有上下文时按整句分词，取目标词那一个 token 的原型
        if sentence:
            doc = nlp(sentence.replace('*', ''))
            key = word.strip().lower()
            for token in doc:
                if token.text.lower() == key and token.lemma_:
                    return token.lemma_
        doc = nlp(word)
        for token in doc:
            # 单词已是原型，直接返回
            if token.lemma_ == word:
                return word
            # 成功
            return token.lemma_
    except Exception as e:
        module.logger.error(f"模型转原型失败: {e}")
        try:
            return use_api_get_prototype(word)
        except Exception as api_error:
            module.logger.warning(f"api 转原型也失败({api_error})，退回原词 {word}")
            return word
    return word


if __name__ == '__main__':
    print(word_revert('done'))
