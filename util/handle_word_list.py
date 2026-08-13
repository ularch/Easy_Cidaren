from decryptencrypt.debase64 import debase64

def handle_word_result(public_info) -> None:
    word_list = []
    word_dict = {}
    try:
        for word in public_info.get_word_list_result['data']['word_list']:
            word_list.append(word['word'])
            word_dict[word['word_zh']] = word['word']
    except:
        for word in debase64(public_info.get_word_list_result['data'], public_info.get_word_list_result['jv'])['word_list']:
            word_list.append(word['word'])
            word_dict[word['word_zh']] = word['word']
    public_info.word_list = word_list
    public_info.word_dict = word_dict
