import spacy
import os

from api.basic_api import use_api_get_prototype
from log.log import Log

# 使用本地目录的模型，便于打包
current_dir = os.path.dirname(os.path.abspath(__file__))
# 上一级目录
parent_dir = os.path.dirname(current_dir)
model_path = os.path.join(parent_dir, 'en_core_web_sm')
module = Log("word_revert")

if not os.path.exists(model_path):
    module.logger.error(f"模型文件夹不存在: {model_path}")
elif not os.listdir(model_path):
    module.logger.error(f"模型文件夹为空: {model_path}")
else:
    module.logger.info(f"模型加载成功{model_path}")


def word_revert(word: str) -> str:
    """
    优先使用模型转原型
    :param word: 目标单词
    :return: 原型
    """
    try:
        nlp = spacy.load(model_path)
        module.logger.info(f"{word}优先使用模型转原型")
        doc = nlp(word)
        for token in doc:
            # 失败
            if token.lemma_ == word:
                module.logger.error("模型转原型失败")
                # 单词就是原型，直接返回（或许）
                # return word
                return use_api_get_prototype(word)
            # 成功
            return token.lemma_
    except Exception as e:
        module.logger.error(f"模型加载失败")
        module.logger.error(e)
        return use_api_get_prototype(word)


if __name__ == '__main__':
    print(word_revert('done'))