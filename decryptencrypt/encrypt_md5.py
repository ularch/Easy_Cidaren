import hashlib


def encrypt_md5(data: str) -> str:
    md5 = hashlib.md5()
    md5.update(data.encode("utf-8"))
    return md5.hexdigest()


if __name__ == '__main__':
    # {   "CET4_pre:CET4_pre_09": [     "determine",     "negative",     "mass",     "workshop",     "permit"   ] }
    str_='chose_err_item=2&task_id=91611533&timestamp=1703349240915&version=2.6.1.231204&word_map={"CET4_pre:CET4_pre_13":["contact","impact","treat","application","facility","chief","indicate","characteristic","various","explore","conference","regard","royal","straight","admission","additional","electronic","install","invisible","governor","density","spacecraft","experimental","undergo","bitter"]}ajfajfamsnfaflfasakljdlalkflak'
    # print(encrypt_md5(str_))
    str_2 = 'it_font_size=42&it_img_w=804&opt_font_c=#000000&opt_font_size=37&opt_img_w=684&time_spent=25000&timestamp=1710407845296&topic_code=k1ODfJVnV46DfnrEZ5Vol2lbXlrGnaebppqepJjKhmJoko9yaW2Ok2SWXpGSYZONZVyWbGdnbGlvZWiWamhvZJGWYm6RlWxgmZRyZm2XbV1rXm9papuZa2WeYWdrbGtvY2qabmNoaW1sbm2akGaR&version=2.6.2.24031302ajfajfamsnfaflfasakljdlalkflak'
    str_3 = 'it_font_size=42&it_img_w=804&opt_font_c=#000000&opt_font_size=37&opt_img_w=684&time_spent=25000&timestamp=1710407845296&topic_code=k1ODfJVnV46DfnrEZ5Vol2lbXlrGnaebppqepJjKhmJoko9yaW2Ok2SWXpGSYZONZVyWbGdnbGlvZWiWamhvZJGWYm6RlWxgmZRyZm2XbV1rXm9papuZa2WeYWdrbGtvY2qabmNoaW1sbm2akGaR&version=2.6.2.24031302'
    print(encrypt_md5(str_2))
