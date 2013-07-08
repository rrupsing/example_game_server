import operator

BIT_MASK_LOWER_31 = 2147483647
BIT_MASK_UPPER_33 = 8589934591 << 31
MAX_UINT_64 = 18446744073709551615

# Lower 31 bit xor mask is:
# 1000110111010110111101000011000 (int 1189837336)
XOR_MASK_LOWER_31 = 1189837336

def obfuscate_id(id):
    """
    Obfuscate an id
    # Note: Supports maxint of 64 bit system.
    """
    if id < 0:
        raise Exception("Cannot obfuscate negative values")
    if id > MAX_UINT_64:
        raise Exception("Can only obfuscate values less than unsigned max int")

    # Bit shift rotate 31 bits left by 11 and xor mask
    # Because python doesn't have rotate, we must shift in both directions, mask out higher bits and add
    lower_range_encoded = operator.xor(((id << 20) & BIT_MASK_LOWER_31) + ((id & BIT_MASK_LOWER_31) >> 11), XOR_MASK_LOWER_31)
    upper_range = id & BIT_MASK_UPPER_33
    return upper_range | lower_range_encoded