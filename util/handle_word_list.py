def handle_word_result(public_info) -> None:
    word_list = []
    for word in public_info.get_word_list_result['data']['word_list']:
        word_list.append(word['word'])
    public_info.word_list = word_list
