import pytest
from qr_encode import makeBitstream, _encodingMode, _stringLength, _modeEncode

def test_mode_indicator_is_byte_mode():
    assert _encodingMode("hello") == "0100"

def test_rejects_characters_outside_iso_8859_1():
    with pytest.raises(Exception):
        _encodingMode("你好")

def test_length_indicator_is_8_bits():
    assert _stringLength("abc") == "00000011"

def test_mode_encode_single_character():
    assert _modeEncode("A") == "01000001"

def test_short_input_uses_version_1_and_h():
    bitstream, version, ecl = makeBitstream("HELLO", 0, 0)
    assert version == 1
    assert ecl == "H"
    assert len(bitstream) == 208

def test_too_long_input_is_rejected():
    with pytest.raises(Exception):
        makeBitstream("x" * 40, 0, 0)
