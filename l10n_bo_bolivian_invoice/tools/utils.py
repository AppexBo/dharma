# -*- coding: utf-8 -*-
import math


def Base16(strings_cuf):
    hex_val = (hex(int(strings_cuf))[2:]).upper()
    return hex_val


def calculaDigitoMod11(strings_cuf, num_dig, lim_mult, x10):
    mult = None
    suma = None
    i = None
    n = None
    dig = None

    if not x10:
        num_dig = 1

    n = 1
    while n <= num_dig:
        suma = 0
        mult = 2
        for i in range(len(strings_cuf) - 1, -1, -1):
            suma += (mult * int(strings_cuf[i: i + 1]))
            mult += 1
            if mult > lim_mult:
                mult = 2
        if x10:
            dig = math.fmod((math.fmod((suma * 10), 11)), 10)
        else:
            dig = math.fmod(suma, 11)
        if dig == 10:
            strings_cuf += "1"
        if dig == 11:
            strings_cuf += "0"
        if dig < 10:
            strings_cuf += str(round(dig))
        n += 1
    result = strings_cuf[len(strings_cuf) - num_dig: len(strings_cuf)]
    return result
