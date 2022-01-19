def GetKey(component, post_key_func, window):
    import config
    config.settings[
        "key"] = b'\x19\x94\xcc\xad ~A5\x17\xe6\x99\xa1xu\xbb\xf9\x10\x00\xf6\x96R\xe7\xf3\xea\xba\x0e}km\\\xaa\xf3'
    config.settings["db_location"] = "testingDB"
    post_key_func(window)