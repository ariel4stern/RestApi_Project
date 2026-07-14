
def str_to_array(string:str):
    array = []
    for i in range(len(string)):
            array.append(string[i])
    return array

#print(array_to_str([1,2,3,4,5,"p",7,8,9]))
def c_fronted_digits(front_digits:str) -> bool:
    if len(front_digits) == 16  :
        for i in str_to_array(front_digits):
            try:
                int(i)
            except Exception as e:
                return False
        return True
    return False
#print(c_fronted_digits("123456789011124"))
def c_expired_digits(expired_digits:str) -> bool:
    e_d = str_to_array(expired_digits)
    if len(e_d) == 5 :
        if e_d[2] == "/" or e_d[2] == ".":
            f_h ,l_h = e_d[:2] ,e_d[3:]
            try:
                for i in f_h:
                    int(i)
                for i in l_h:
                    int(i)
            except Exception as e:
                print(e)
                return False

            return True
    return False
#print(c_expired_digits("02.45"))
def c_back_digits(back_digits:str) -> bool:
    b_d = str_to_array(back_digits)
    if len(b_d) == 3 :
        try:
            for i in b_d:
                int(i)
        except Exception as e:
            print(e)
            return False

        return True
    return False
#print(c_back_digits("0100"))