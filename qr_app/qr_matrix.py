# Team project

import numpy as np

# Add finder patterns to the QR matrix
def _finderPattern(matrix):
    pattern = np.array([[1, 1, 1, 1, 1, 1, 1],
                        [1, 0, 0, 0, 0, 0, 1],
                        [1, 0, 1, 1, 1, 0, 1],
                        [1, 0, 1, 1, 1, 0, 1],
                        [1, 0, 1, 1, 1, 0, 1],
                        [1, 0, 0, 0, 0, 0, 1],
                        [1, 1, 1, 1, 1, 1, 1]])
    
    # Top-left
    matrix = _addFinderPattern(matrix, pattern, 0, 0)
    # Top-right
    matrix = _addFinderPattern(matrix, pattern, 0, matrix.shape[0] - 7)
    # Bottom-left
    matrix = _addFinderPattern(matrix, pattern, matrix.shape[0] - 7, 0)

    return matrix

# Helper function to add finder pattern at specified location
def _addFinderPattern(matrix, pattern, row, col):
    pattern_size = pattern.shape[0]
    matrix[row:row+pattern_size, col:col+pattern_size] = pattern

    return matrix

# Add separators around finder patterns
def _addSeparators(matrix):
    size = matrix.shape[0]
    # Top-left
    matrix[7, 0:8] = 0
    matrix[0:8, 7] = 0
    # Top-right
    matrix[7, size-8:size] = 0
    matrix[0:8, size-8] = 0
    # Bottom-left
    matrix[size-8:size, 7] = 0
    matrix[size-8, 0:8] = 0

    return matrix

# Add alignment pattern for version 2
def _addAlignmentPattern(matrix, version):
    if version == 1:
        return matrix  # No alignment pattern needed for version 1

    size = matrix.shape[0]
    center = size - 7 # Position for center of alignment pattern

    pattern = np.array([[1, 1, 1, 1, 1],
                        [1, 0, 0, 0, 1],
                        [1, 0, 1, 0, 1],
                        [1, 0, 0, 0, 1],
                        [1, 1, 1, 1, 1]])

    start_row = center - 2
    start_col = center - 2
    matrix[start_row:start_row+5, start_col:start_col+5] = pattern

    return matrix

# Add timing patterns to the QR matrix
def _addTimingPatterns(matrix):
    size = matrix.shape[0]
    for i in range(8, size - 8):
        # Horizontal timing pattern
        matrix[6, i] = (i + 1) % 2
        # Vertical timing pattern
        matrix[i, 6] = (i + 1) % 2

    return matrix

# Add dark module
def _addDarkModule(matrix):
    size = matrix.shape[0]
    matrix[size - 8, 8] = 1
    return matrix

# Reserve format information areas to prevent data writing
def _reserveFormatInfoAreas(matrix):
    size = matrix.shape[0]

    # Horizontal
    matrix[8, 0:9] = -2
    matrix[8, size-8:size] = -2
    matrix[8, 6] = 1

    # Vertical
    matrix[0:9, 8] = -2
    matrix[size-7:size, 8] = -2
    matrix[6, 8] = 1

    return matrix

# Create data bit placement in the QR matrix
def _addDataBits(matrix, bitstream):
    size = matrix.shape[0]
    data_matrix = np.full((size, size), fill_value=-1, dtype=int) # create unreserved martix for data bits
    direction = -1  # Start moving upwards
    col = size - 1
    row = size - 1
    bit_index = 0

    while col > 0:
        if col == 6:  # Skip vertical timing pattern
            col -= 1
        for i in range(size):
            r = row + (direction * i) # Move row pointer up or down depending on direction
            for c in [col, col - 1]: # Right column then left column
                if matrix[r, c] == -1:  # Only fill in unreserved areas
                    if bit_index < len(bitstream): # Check if there are bits left to place
                        data_matrix[r, c] = int(bitstream[bit_index]) # Place the bit
                        bit_index += 1
        direction *= -1  # Change direction
        # Calculate new row starting point
        if direction == 1: 
            row = 0
        else:
            row = size - 1
        col -= 2

    return data_matrix

# Modify masking patterns
def _applyMask(matrix, maskPattern):
    size = matrix.shape[0]
    masked_matrix = matrix.copy() # Copy data matrix

    for r in range(size):
        for c in range(size):
            if matrix[r, c] >= 0: # Only apply mask to data areas
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
                    masked_matrix[r, c] ^= 1

    return masked_matrix

# Implement the 4 penalty rules
def penalty_rule_1(matrix):
    penalty = 0
    size = matrix.shape[0]
    
    for r in range(size):
        count = 1
        for c in range(1, size):
            if matrix[r, c] == matrix[r, c-1]:
                count += 1
                if count == 5:
                    penalty += 3
                elif count > 5:
                    penalty += 1
            else:
                count = 1
                
    for c in range(size):
        count = 1 
        for r in range(1, size):
            if matrix[r, c] == matrix[r-1, c]:
                count += 1
                if count == 5:
                   penalty += 3
                elif count > 5:
                    penalty += 1
            else:
                count = 1
    return penalty

def penalty_rule_2(matrix):
    penalty = 0
    size = matrix.shape[0] 
    
    for r in range(size - 1):
        for c in range(size - 1):
            block = matrix[r:r+2, c:c+2]
            if np.all(block == block[0, 0]):
                penalty += 3
    return penalty 

def penalty_rule_3(matrix):
    penalty = 0
    size = matrix.shape[0]
    pattern1 = [1,0,1,1,1,0,1,0,0,0,0]
    pattern2 = [0,0,0,0,1,0,1,1,1,0,1]
    
    for r in range(size):
        for c in range(size - 10):
            row = list(matrix[r, c:c+11])
            if row == pattern1 or row == pattern2:
                penalty += 40
                
    for c in range(size):
        for r in range(size - 10):
            col = list(matrix[r:r+11, c])
            if col == pattern1 or col == pattern2:
                penalty += 40
    return penalty 

def penalty_rule_4(matrix):
    total = matrix.size 
    dark = np.count_nonzero(matrix == 1)
    percent = (dark * 100) // total
    deviation = abs(percent - 50)
    return (deviation // 5) * 10

# Choose the best masking pattern
def _evaluateMasks(baseMatrix, bitstream, ecl):
    results = {}
    
    for mask in range(8):
        data = _addDataBits(baseMatrix, bitstream)
        masked = _applyMask(data, mask)
        combined = _combineMatrices(baseMatrix, masked)
        format_string = _generateFormatString(ecl, mask)
        final = _addFormatInfo(combined, format_string)
        
        p1 = penalty_rule_1(final)
        p2 = penalty_rule_2(final)
        p3 = penalty_rule_3(final)
        p4 = penalty_rule_4(final)
        
        results[mask] = {
            "P1": p1,
            "P2": p2,
            "P3": p3,
            "P4": p4,
            "total": p1 + p2 + p3 + p4,
            "matrix": final 
        }    
        
    best_mask = min(results, key = lambda m: results[m]["total"])
    return best_mask, results 
    
# Combine base matric with data matrix
def _combineMatrices(baseMatrix, dataMatrix):
    size = baseMatrix.shape[0]
    combined = baseMatrix.copy()

    for r in range(size):
        for c in range(size):
            if baseMatrix[r, c] == -1: # Only fill unreserved areas in base matrix
                combined[r, c] = dataMatrix[r, c]

    return combined


def _generateFormatString(ecl, maskPattern):
    ecl_dict = {'L': 0b01, 'M': 0b00, 'Q': 0b11, 'H': 0b10}
    format_info = (ecl_dict[ecl] << 3) | (maskPattern & 0b111)

    g = 0b10100110111
    data = format_info << 10

    for i in range(4, -1, -1):
        if (data >> (i+10)) & 1:
            data ^= g << i

    remainder = data & 0x3FF
    format_info = (format_info << 10) | remainder
    
    mask = 0b101010000010010
    format_info = format_info ^ mask
    
    return format_info

# Add format information to the QR matrix while avoiding timing patterns
def _addFormatInfo(matrix, formatString):
    size = matrix.shape[0]

    # Top-left
    for i in range(0, 6):
        matrix[8, i] = (formatString >> (14 - i)) & 1
    matrix[8, 7] = (formatString >> 8) & 1
    matrix[8, 8] = (formatString >> 7) & 1
    matrix[7, 8] = (formatString >> 6) & 1
    for i in range(5, -1, -1):
        matrix[i, 8] = (formatString >> i) & 1

    # Bottom-left
    for i in range(0, 7):
        matrix[size - 1 - i, 8] = (formatString >> (14 - i)) & 1

    # Top-right
    for i in range(7, -1, -1):
        matrix[8, (size - 1) - i] = (formatString >> i) & 1

    return matrix

# Main function to generate QR matrix modified
def generateQRMatrix(version, bitstream, ecl):
    size = 21 + (version - 1) * 4  # QR code size formula
    base_matrix = np.full((size, size), fill_value=-1, dtype=int) # Initialize empty unreserved matrix
    
    base_matrix = _finderPattern(base_matrix) # Add finder patterns
    base_matrix = _addSeparators(base_matrix) # Add separators
    base_matrix = _addAlignmentPattern(base_matrix, version) # Add alignment pattern if version >=2
    base_matrix = _addTimingPatterns(base_matrix) # Add timing patterns
    base_matrix = _addDarkModule(base_matrix) # Add dark module
    base_matrix = _reserveFormatInfoAreas(base_matrix) # Reserve format info areas
    
    best_mask, results = _evaluateMasks(base_matrix, bitstream, ecl) # mask evaluation
    final_matrix = results[best_mask]["matrix"]

    return final_matrix, best_mask
