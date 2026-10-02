# Team project

from qr_reader_bch import decodeFormatInfo
import numpy as np
import reedsolo as rs

# Strip quiet zone and convert image to binary matrix
def _stripImage(img):
    size = img.shape[0]-8 # get size without quiet zone
    img = img[4:size+4, 4:size+4, :] # remove quiet zone
    img = (img[:,:,0] > 0.5).astype(int) # convert to black and white matrix
    for r in range(size):
        for c in range(size):
            img[r, c] = 1 - img[r, c]  # Invert colors
    return img

# Read format information from QR code
def _readFormatInfo(matrix):
    size = matrix.shape[0]
    formatString = ''
    formatString2 = ''

    # Top-left
    for i in range(0, 6):
        formatString += str(matrix[8, i])
    formatString += str(matrix[8, 7])
    formatString += str(matrix[8, 8])
    formatString += str(matrix[7, 8])
    for i in range(5, -1, -1):
        formatString += str(matrix[i, 8])

    # Bottom-left
    for i in range(0, 7):
        formatString2 += str(matrix[size - 1 - i, 8])

    # Top-right
    for i in range(7, -1, -1):
        formatString2 += str(matrix[8, size - 1 - i])

    formatString = int(formatString, 2)
    formatString2 = int(formatString2, 2)
    version = int(size - 17) // 4

    return formatString, formatString2, version

# Get error correction level, mask pattern, and version from format info
def _getFormatInfo(img):
    format1, format2, version = _readFormatInfo(img)
    try:
        ecl, maskPattern = decodeFormatInfo(format1)
    except ValueError:
        ecl, maskPattern = decodeFormatInfo(format2)
    
    return ecl, maskPattern, version

# Create base matrix with functional patterns so allow data extraction
def _finderPattern(matrix):
    pattern = np.full((7, 7), fill_value=1, dtype=int)
    
    # Top-left
    matrix = _addFinderPattern(matrix, pattern, 0, 0)
    # Top-right
    matrix = _addFinderPattern(matrix, pattern, 0, matrix.shape[0] - 7)
    # Bottom-left
    matrix = _addFinderPattern(matrix, pattern, matrix.shape[0] - 7, 0)

    return matrix

def _addFinderPattern(matrix, pattern, row, col):
    pattern_size = pattern.shape[0]
    matrix[row:row+pattern_size, col:col+pattern_size] = pattern

    return matrix

def _addSeparators(matrix):
    size = matrix.shape[0]
    # Top-left
    matrix[7, 0:8] = 1
    matrix[0:8, 7] = 1
    # Top-right
    matrix[7, size-8:size] = 1
    matrix[0:8, size-8] = 1
    # Bottom-left
    matrix[size-8:size, 7] = 1
    matrix[size-8, 0:8] = 1

    return matrix

def _addAlignmentPattern(matrix, version):
    if version == 1:
        return matrix  # No alignment pattern needed for version 1

    size = matrix.shape[0]
    center = size - 7 # Position for center of alignment pattern

    pattern = np.full((5, 5), fill_value=1, dtype=int)

    start_row = center - 2
    start_col = center - 2
    matrix[start_row:start_row+5, start_col:start_col+5] = pattern

    return matrix

def _addTimingPatterns(matrix):
    size = matrix.shape[0]
    for i in range(8, size - 8):
        # Horizontal timing pattern
        matrix[6, i] = 1
        # Vertical timing pattern
        matrix[i, 6] = 1

    return matrix

def _addDarkModule(matrix):
    size = matrix.shape[0]
    matrix[size - 8, 8] = 1
    return matrix

def _FormatInfoAreas(matrix):
    size = matrix.shape[0]

    # Horizontal
    matrix[8, 0:9] = 1
    matrix[8, size-8:size] = 1
    matrix[8, 6] = 1

    # Vertical
    matrix[0:9, 8] = 1
    matrix[size-7:size, 8] = 1
    matrix[6, 8] = 1

    return matrix

def _createBaseMatrix(version):
    size = 17 + 4 * version
    base_matrix = np.full((size, size), fill_value=0, dtype=int)

    base_matrix = _finderPattern(base_matrix) # Add finder patterns
    base_matrix = _addSeparators(base_matrix) # Add separators
    base_matrix = _addAlignmentPattern(base_matrix, version) # Add alignment pattern if version >=2
    base_matrix = _addTimingPatterns(base_matrix) # Add timing patterns
    base_matrix = _addDarkModule(base_matrix) # Add dark module
    base_matrix = _FormatInfoAreas(base_matrix) # Reserve format info areas

    return base_matrix

# Create data matrix by removing functional patterns from original matrix
def _createDataMatrix(matrix, base_matrix):
    size = matrix.shape[0]
    data_matrix = np.full((size, size), fill_value=2, dtype=int)

    for r in range(size):
        for c in range(size):
            if base_matrix[r, c] == 0:  # Data module
                data_matrix[r, c] = matrix[r, c]
    return data_matrix

# Apply mask pattern to data matrix to unmask data
def _applyMask(matrix, maskPattern):
    size = matrix.shape[0]
    unmasked_matrix = matrix.copy()

    for r in range(size):
        for c in range(size):
            if matrix[r, c] <= 1:  # Only apply mask to data modules
                apply = False
                
                if maskPattern == 0:
                    apply = (r + c) % 2 == 0
                elif maskPattern == 1:
                    apply = r % 2 == 0
                elif maskPattern == 2:
                    apply = c % 3 == 0
                elif maskPattern == 3:
                    apply = (r + c) % 3 == 0
                elif maskPattern == 4:
                    apply = ((r // 2) + (c // 3)) % 2 == 0
                elif maskPattern == 5:
                    apply = ((r * c) % 2 + (r * c) % 3) == 0
                elif maskPattern == 6:
                    apply = (((r * c) % 2 + (r * c) % 3) % 2) == 0
                elif maskPattern == 7:
                    apply = (((r + c) % 2 + (r * c) % 3) % 2) == 0
                    
                if apply:
                    unmasked_matrix[r, c] ^= 1
    return unmasked_matrix

# Extract data bits from QR code matrix
def _extractDataBits(matrix, maskPattern, version):
    base_matrix = _createBaseMatrix(version)
    data_matrix = _createDataMatrix(matrix, base_matrix)
    unmasked_matrix = _applyMask(data_matrix, maskPattern)
    return unmasked_matrix

# Read data bits in zig-zag pattern
def _readDataBits(matrix):
    size = matrix.shape[0]
    bitstream = ''
    direction = -1  # Start moving upwards
    col = size - 1
    row = size - 1

    while col > 0:
        if col == 6:  # Skip vertical timing pattern
            col -= 1
        for i in range(size):
            r = row + (direction * i) # Move row pointer up or down depending on direction
            for c in [col, col - 1]: # Right column then left column
                if matrix[r, c] <= 1:  # Only fill in unreserved areas
                    bitstream += str( matrix[r, c])
        direction *= -1  # Change direction
        # Calculate new row starting point
        if direction == 1: 
            row = 0
        else:
            row = size - 1
        col -= 2

    return bitstream

# Strip padding zeros from the end of the bitstream
def _stripPaddingZeros(bitstream, version):
    if version == 1:
        return bitstream  # No padding for version 1
    elif version == 2:
        return bitstream[:-7]  # Remove last 7 padding bits for version 2

# Reed-Solomon error correction decoding
def _reedsolomonDecode(bitstream, version, ecl):
    # Convert bitstream to byte array
    byte_array = []
    for i in range(0, len(bitstream), 8):
        byte = int(bitstream[i:i+8], 2)
        byte_array.append(byte)

    nysm = NSYM_DICT[(version, ecl)]
    rs_decoder = rs.RSCodec(nysm)
    try:
        byte_array, _, _ = rs_decoder.decode(bytearray(byte_array))
    except rs.ReedSolomonError:
        raise Exception("Unable to read data information!")

    decoded_bitstream = ''
    for byte in byte_array:
        decoded_bitstream += format(byte, '08b')

    return decoded_bitstream

# Get encoding mode and data length from bitstream
def _getModeLength(bitstream):
    mode = bitstream[0:4]
    if mode == '0100':
        length_bits = 8
    else:
        raise Exception("Unsupported encoding mode!")

    length = int(bitstream[4:4+length_bits], 2)
    bitstream = bitstream[4+length_bits:]
    return bitstream, mode, length, length_bits

# Strip pad bits from bitstream based on data length
def _stripPadBits(bitstream, length, length_bits):
    total_bits = length * length_bits
    return bitstream[:total_bits]

# Convert bitstream to data string based on encoding mode
def _bitstreamToData(bitstream, mode, length):
    data = ''

    if mode == '0100':
        for i in range(length):
            byte = int(bitstream[0:8], 2)
            data += chr(byte)
            bitstream = bitstream[8:]
    else:
        raise Exception("Unsupported encoding mode!")

    return data

# Number of error correction symbols for each version and error correction level
NSYM_DICT = {
    (1, 'L'): 7,
    (1, 'M'): 10,
    (1, 'Q'): 13,
    (1, 'H'): 17,
    (2, 'L'): 10,
    (2, 'M'): 16,
    (2, 'Q'): 22,
    (2, 'H'): 28
}

# Main function to decode QR code image
def decodeQrCode(img):
    img = _stripImage(img)
    ecl, maskPattern, version = _getFormatInfo(img)
    if version not in [1, 2]:
        raise Exception("Only versions 1 and 2 are supported!")
    unmasked_matrix = _extractDataBits(img, maskPattern, version)
    bitstream = _readDataBits(unmasked_matrix)
    bitstream = _stripPaddingZeros(bitstream, version)
    bitstream = _reedsolomonDecode(bitstream, version, ecl)
    bitstream, mode, length, length_bits = _getModeLength(bitstream)
    bitstream = _stripPadBits(bitstream, length, length_bits)
    data = _bitstreamToData(bitstream, mode, length)

    return data