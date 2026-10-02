# Team project

# Mapping of ECC bits to levels
ECC_MAP = {
    0b01: "L",
    0b00: "M",
    0b11: "Q",
    0b10: "H",
}

# Compute the BCH remainder of value divided by polynomial
def _bch_remainder(value, poly):

    while value.bit_length() >= poly.bit_length():
        shift = value.bit_length() - poly.bit_length()
        value ^= poly << shift

    return value

# Extract ECC level and mask from codeword
def _extract_format(codeword):
    data = codeword >> 10  # top 5 bits

    ecc_level = ECC_MAP[data >> 3]
    mask = data & 0b111

    return ecc_level, mask

# Decode format information with BCH error correction
def decodeFormatInfo(formatString):
    # Extract error correction level and mask pattern
    g = 0b10100110111
    mask = 0b101010000010010
    formatString ^= mask # unmask

    # check for errors
    syndrome = _bch_remainder(formatString, g)
    if syndrome == 0: # no errors
        return _extract_format(formatString)

    # try all error patterns of weight 1
    for i in range(15):
        corrected = formatString ^ (1 << i)
        if _bch_remainder(corrected, g) == 0:
            return _extract_format(corrected)

    # try all error patterns of weight 2
    for i in range(15):
        for j in range(i + 1, 15):
            corrected = formatString ^ (1 << i) ^ (1 << j)
            if _bch_remainder(corrected, g) == 0:
                return _extract_format(corrected)

    # try all error patterns of weight 3
    for i in range(15):
        for j in range(i + 1, 15):
            for k in range(j + 1, 15):
                corrected = formatString ^ (1 << i) ^ (1 << j) ^ (1 << k)
                if _bch_remainder(corrected, g) == 0:
                    return _extract_format(corrected)

    raise ValueError("Unable to read format information")