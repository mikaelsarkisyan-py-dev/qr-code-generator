# Team project; co-written by Mikael

import reedsolo as rs

# determine the encoding mode for the input data
def _encodingMode(data):
    try:
        data.encode('iso-8859-1')
        return "0100" # only byte mode is supported
    except UnicodeEncodeError:
        raise Exception("Invalid characters for QR code encoding!")

# calculate the length of the input data in bits based on the encoding mode
def _stringLength(data):
    length = len(data)
    # gives length of the input string for byte mode
    return format(length, '008b') # 8 bits

# encode data in byte mode for QR code
def _modeEncode(data):
    # each character is converted to its 8-bit binary representation using ISO-8859-1 encoding
    # concatenate all bit segments to form final bitstream

    bitstream = ""
    for char in data:
        byte_val = char.encode('iso-8859-1')
        bitstream += format(byte_val[0], '08b')
    return bitstream

# determine QR code version based on bitstream length
def _qrVersion(bitstream, qr_version, ecl_override):
    length = len(bitstream)
    if qr_version in [0, 1] and length <= 152: # version 1
        ecl = _correctionLevel(bitstream, 1, ecl_override)
        return 1, length, ecl
    elif qr_version in [0, 2] and length <= 272: #version 2
        ecl = _correctionLevel(bitstream, 2, ecl_override)
        return 2, length, ecl
    else:
        if qr_version == 0:
            raise Exception("Data too long for QR code versions 1 or 2!") # if length exceeds version 2 capacity, return error
        else:
            raise Exception("Unable to generate QR code with specified QR version!")

# find minimum error correction level for given bitstream and version
def _correctionLevel(bitsream, version, ecl_override):
    length = len(bitsream)
    if version == 1:
        if ecl_override in [0, 'H'] and length <= 72:
            return 'H'
        elif ecl_override in [0, 'Q'] and length <= 104:
            return 'Q'
        elif ecl_override in [0, 'M'] and length <= 128:
            return 'M'
        elif ecl_override in [0, 'L'] and length <= 152:
            return 'L'
        else:
            raise Exception("Unable to generate QR code with specified error correction level!")
    elif version == 2:
        if ecl_override in [0, 'H'] and length <= 128:
            return 'H'
        elif ecl_override in [0, 'Q'] and length <= 176:
            return 'Q'
        elif ecl_override in [0, 'M'] and length <= 224:
            return 'M'
        elif ecl_override in [0, 'L'] and length <= 272:
            return 'L'
        else:
            raise Exception("Unable to generate QR code with specified error correction level!")
    else:
        raise Exception("Unsupported QR code version!")

# get maximum bit length for given version and error correction level
def _eclToBitLen(version, ecl):
    if version == 1:
        if ecl == 'L':
            return 152
        elif ecl == 'M':
            return 128
        elif ecl == 'Q':
            return 104
        elif ecl == 'H':
            return 72
    elif version == 2:
        if ecl == 'L':
            return 272
        elif ecl == 'M':
            return 224
        elif ecl == 'Q':
            return 176
        elif ecl == 'H':
            return 128
    else:
        raise Exception("Unsupported QR code version!")

# add terminator to bitstream
def _addTerminator(version, bit_length, ecl):
    if version == 1:
        max_bits = _eclToBitLen(version, ecl)
    elif version == 2:
        max_bits = _eclToBitLen(version, ecl)
    else:
        raise Exception("Unsupported QR code version!")
    terminator_length = min(4, max_bits - bit_length) # add a maximum of 4 bits or until max capacity is reached
    terminator = "0" * terminator_length
    return terminator

# pad bitstream to byte boundary
def _pad8(bitstream):
    # pad the bitstream to make its length a multiple of 8
    while len(bitstream) % 8 != 0:
        bitstream += "0"
    return bitstream

# add pad bytes to reach maximum capacity
def _padBytes(bitstream, version, ecl):
    if version == 1:
        if ecl == 'L':
            max_bytes = 19
        elif ecl == 'M':
            max_bytes = 16
        elif ecl == 'Q':
            max_bytes = 13
        elif ecl == 'H':
            max_bytes = 9
        else:
            raise Exception("Unsupported error correction level!")
    elif version == 2:
        if ecl == 'L':
            max_bytes = 34
        elif ecl == 'M':
            max_bytes = 28
        elif ecl == 'Q':
            max_bytes = 22
        elif ecl == 'H':
            max_bytes = 16
        else:
            raise Exception("Unsupported error correction level!")
    else:
        raise Exception("Unsupported QR code version!")

    # calculate current number of bytes in the bitstream
    current_bytes = len(bitstream) // 8
    pad_bytes = []
    pad_patterns = ["11101100", "00010001"]

    # add pad bytes until max capacity reached
    i = 0
    while current_bytes < max_bytes:
        pad_bytes.append(pad_patterns[i % 2])
        i += 1
        current_bytes += 1

    return bitstream + ''.join(pad_bytes)

def _reedsolomonEncode(bitstream, version, ecl):
    # convert bitstream to byte array
    byte_array = []
    for i in range(0, len(bitstream), 8):
        byte = bitstream[i:i+8]
        byte_array.append(int(byte, 2))

    # determine number of ecc based on version
    if version == 1:
        if ecl == 'L':
            nsym = 7
        elif ecl == 'M':
            nsym = 10
        elif ecl == 'Q':
            nsym = 13
        elif ecl == 'H':
            nsym = 17
        else:
            raise Exception("Unsupported error correction level!")
    elif version == 2:
        if ecl == 'L':
            nsym = 10
        elif ecl == 'M':
            nsym = 16
        elif ecl == 'Q':
            nsym = 22
        elif ecl == 'H':
            nsym = 28
        else:
            raise Exception("Unsupported error correction level!")
    else:
        raise Exception("Unsupported QR code version!")

    # create Reed-Solomon codec (number of ecc bytes)
    rsc = rs.RSCodec(nsym)

    # encode data
    encoded = rsc.encode(bytearray(byte_array))

    # convert encoded byte array back to bitstream
    encoded_bitstream = ''
    for byte in encoded:
        encoded_bitstream += format(byte, '08b')

    return encoded_bitstream

def _versionPad(bitstream, version):
    if version == 1:
        return bitstream
    elif version == 2:
        return bitstream + "0000000"
    else:
        raise Exception("Unsupported QR code version!")
    
# build the complete bitstream for the QR code
def makeBitstream(data, qr_version, ecl):
    bitstream = "" # initialise empty bitstream
    bitstream += _encodingMode(data) # mode indicator
    bitstream += _stringLength(data) # length indicator
    bitstream += _modeEncode(data) # encoded message

    if qr_version == 0 and ecl == 0:
        qr_version, bit_length, ecl = _qrVersion(bitstream, qr_version, ecl) # find QR code version based on current bitstream length
    elif qr_version != 0 and ecl == 0:
        _, bit_length, ecl = _qrVersion(bitstream, qr_version, ecl)
    elif qr_version == 0 and ecl != 0:
        qr_version, bit_length, _ = _qrVersion(bitstream, qr_version, ecl)
    else:
        _, bit_length, _ = _qrVersion(bitstream, qr_version, ecl)
    
    bitstream += _addTerminator(qr_version, bit_length, ecl)
    bitstream = _pad8(bitstream) # pad to byte boundary
    bitstream = _padBytes(bitstream, qr_version, ecl) # pad to max capacity
    bitstream = _reedsolomonEncode(bitstream, qr_version, ecl)
    bitstream = _versionPad(bitstream, qr_version)

    return bitstream, qr_version, ecl
