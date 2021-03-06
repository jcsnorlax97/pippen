"""
SCI 2000 Group Project - Image Compression

Name:   Justin M. C. Choi & Mike Winkler
Date:   Dec/03/2019 (Tue) 

Run:    python3 Playground.py <image_path>
"""

import sys
import zlib

file = sys.argv[1] # get file path

(fileName, extName) = file.rsplit('.', maxsplit=1)

contents = ""

# =================================================================================
# Classes and Functions
# =================================================================================

# ---------------------------------------------------------------------------------
# A. PNG Data Stream
#
# - to store all chunks in the image. 
# ---------------------------------------------------------------------------------
class PngDatastream:

    def __init__(self):
        self._signature = None
        self._idhrChunk = None
        self._plteChunk = None
        self._idatChunk = None
        self._iendChunk = None
        pass

    # --- accessors ---
    def get_signature(self):
        return self._signature

    def get_idhr_chunk(self):
        return self._idhrChunk

    def get_plte_chunk(self):
        return self._plteChunk

    def get_idat_chunk(self):
        return self._idatChunk

    def get_iend_chunk(self):
        return self._iendChunk

    # --- mutators ---
    def set_signature(self, signature):
        self._signature = signature

    # interface of chunk setter
    def set_chunk(self, chunk):
        setter = self._get_setter(chunk.get_type())
        setter(chunk)
        
    # factory; reuse _get_chunk_creator()
    def _get_setter(self, chunkType):
        if chunkType == '49484452' or chunkType == 'IHDR' or chunkType == 'ihdr': # IHDR Chunk
            return self._set_idhr_chunk
        elif chunkType == '504C5445' or chunkType == 'PLTE' or chunkType == 'plte': # PLTE Chunk
            return self._set_plte_chunk
        elif chunkType == '49444154' or chunkType == 'IDAT' or chunkType == 'idat': # IDAT Chunk(s)
            return self._set_idat_chunk
        elif chunkType == '49454E44' or chunkType == 'IEND' or chunkType == 'iend': # IEND Chunk
            return self._set_iend_chunk
        else:
            raise ValueError(chunkType)

    def _set_idhr_chunk(self, idhrChunk):
        self._idhrChunk = idhrChunk

    def _set_plte_chunk(self, plteChunk):
        self._plteChunk = plteChunk

    def _set_idat_chunk(self, idatChunk):
        self._idatChunk = [] if (self._idatChunk is None) else (self._idatChunk)
        self._idatChunk.append(idatChunk)

    def _set_iend_chunk(self, iendChunk):
        self._iendChunk = iendChunk

# ---------------------------------------------------------------------------------
# A2. Chunk
# 
# - Factor Pattern for object creation
# - if not having __init__(self) in subclass, super class's __init__(self) is called
# - reference: Understanding Class Inheritance in Python 3
#   https://www.digitalocean.com/community/tutorials/understanding-class-inheritance-in-python-3
# ---------------------------------------------------------------------------------
class Chunk:

    def __init__(self):
        self._length = None         # 4-bytes; unsigned int; for _chunkData; valid values: 0 ~ 2^(31) - 1
        self._chunkType = None      # 4-bytes (8 hex characters); hex string values
        self._chunkData = None      # _length-bytes; dictionary or None
        self._crc = None            # 4-bytes (8 hex characters); hex string values; for _chunkType and _chunkData
        pass

    # Factory Pattern 
    @staticmethod
    def create(chunkType):
        creator = _get_chunk_creator(chunkType)
        return creator()

    # - this is called when child class has no overriding, i.e. no data field.
    # - None is returned
    # - length = data length
    def extract_data(self, length, hexChunkData):
        return None 

    # --- accessors ---
    def get_length(self):
        return self._length

    def get_type(self):
        return self._chunkType

    def get_data(self):
        return self._chunkData

    def get_crc(self):
        return self._crc

    # --- mutators ---
    def set_length(self, length):
        self._length = length
    
    def set_type(self, chunkType):
        self._chunkType = chunkType

    def set_data(self, chunkData):
        self._chunkData = chunkData

    def set_crc(self, crc):
        self._crc = crc

# used by Chunk class
def _get_chunk_creator(chunkType):
    if chunkType == '49484452' or chunkType == 'IHDR' or chunkType == 'ihdr': # IHDR Chunk
        return IdhrChunk
    elif chunkType == '504C5445' or chunkType == 'PLTE' or chunkType == 'plte': # PLTE Chunk
        return PlteChunk
    elif chunkType == '49444154' or chunkType == 'IDAT' or chunkType == 'idat': # IDAT Chunk(s)
        return IdatChunk
    elif chunkType == '49454E44' or chunkType == 'IEND' or chunkType == 'iend': # IEND Chunk
        return IendChunk
    else:
        raise ValueError(chunkType)

class IdhrChunk(Chunk):
    
    # override
    def extract_data(self, length, hexChunkData):
        data = {
            'width': None,              # 4-bytes; unsigned int; 0 is invalid
            'height': None,             # 4-bytes; unsigned int; 0 is invalid
            'bitDepth': None,           # 1-byte; int; number of bits per sample; valid values = 1,2,4,8,16; not all values allowed for all colour types.
            'colourType': None,         # 1-byte; int; PNG image type; valid values = 0,2,3,4,6
            'compressionMethod': None,  # 1-byte; int; method to compress the image data; (#)valid value = 0(#); 
            'filterMethod': None,       # 1-byte; int; preprocessing method applied before compresson; (#)valid value = 0(#); 
            'interlaceMethod': None     # 1-byte; int; transmission order of the image data before compresson; valid value = 0 (no interlace) or 1 (Adam7 interlace).
        }

        assert (data['width'] is None), "Not None!!"
        assert (data['height'] is None), "Not None!!"
        assert (data['bitDepth'] is None), "Not None!!"
        assert (data['colourType'] is None), "Not None!!"
        assert (data['compressionMethod'] is None), "Not None!!"
        assert (data['filterMethod'] is None), "Not None!!"
        assert (data['interlaceMethod'] is None), "Not None!!"

        # data length must be 13 bytes (26 hex) in IHDR
        if len(hexChunkData) == length * 2 and length == 13:
            data['width'] = int(hexChunkData[0:8], 16)
            data['height'] = int(hexChunkData[8:16], 16)
            data['bitDepth'] = int(hexChunkData[16:18], 16)
            data['colourType'] = int(hexChunkData[18:20], 16)
            data['compressionMethod'] = int(hexChunkData[20:22], 16)
            data['filterMethod'] = int(hexChunkData[22:24], 16)
            data['interlaceMethod'] = int(hexChunkData[24:26], 16)
            return data
        else:
            raise ValueError("{0} {1}".format(len(hexChunkData), length))

class PlteChunk(Chunk):
    
    # override
    def extract_data(self, length, hexChunkData):
        data = {
            'red': None,            # 1-byte; unsigned int; 0 is invalid
            'green': None,          # 1-byte; unsigned int; 0 is invalid
            'blue': None,           # 1-byte; int; number of bits per sample; valid values = 1,2,4,8,16; not all values allowed for all colour types.
        }

        assert (data['red'] is None), "Not None!!"
        assert (data['green'] is None), "Not None!!"
        assert (data['blue'] is None), "Not None!!"

        # data length must be 3 bytes (6 hex) in PLTE (must be divisible by 3)
        if len(hexChunkData) == length * 2 and length == 3:
            data['red'] = int(hexChunkData[0:2], 16)
            data['green'] = int(hexChunkData[2:4], 16)
            data['blue'] = int(hexChunkData[4:6], 16)
            return data
        else:
            raise ValueError("{0} {1}".format(len(hexChunkData), length))

class IdatChunk(Chunk):
    pass

# no chunk data, i.e. no need to extract data
class IendChunk(Chunk):
    pass

# ---------------------------------------------------------------------------------
# B. Zlib Data Stream
#
# - after concatenating chunk data from all IDAT chunks, it will be the Zlib data
#   stream. This class is used to store that.
# - [!] naming may need to be improved.
#   (nov/26): update naming convensions based
# - ZLIB Compressed Data Format Specification: https://www.ietf.org/rfc/rfc1950.txt
# - (ignore - _flags - nov/26): for now, ignore validation checking for on _flags.
# - (ignore - _checkValue - nov/26): for now, ignore Adler32 checksum
# - DEFLATE Compressed Data Format Specification v1.3: https://tools.ietf.org/html/rfc1951
# - max. size of a zlib datastream  = size of concatenation result of all IDAT chunks 
#                                   = 32k bits 
#                                   => 32768 bytes 
# ---------------------------------------------------------------------------------
class ZlibDatastream:
    
    def __init__(self):
        self._compressionDetails = None # 1-byte; 2 hex chars; right hex (bits 0-3) = Compression method (CM=8 => "deflate" CM with a window size up to 32K, used by gzip and PNG), left hex (bits 4-7) = Compression info (only defined when CM=8; when CM=8, CINFO is the base-2 log of the LZ77 window size; CINFO <= 7; CINFO=7 => 32K window size).
        self._flags = None              # 1-byte; 2 hex chars; bits 0-4 = FCHECK, bit 5 = FDICT, bit 6-7 = FLEVEL
        self._compressedData = None     # n-bytes; 2*n hex chars; CM=8 => "deflate compressed data format"
        self._checkValue = None         # 4-bytes; 8 hex chars; ADLER-32 Checksum
        pass

    # --- mutators ---
    def get_compression_details(self):
        return self._compressionDetails

    def get_flags(self):
        return self._flags

    def get_compressed_data(self):
        return self._compressedData

    def get_check_value(self):
        return self._checkValue

    # --- mutators ---
    def set_compression_details(self, details):
        self._compressionDetails = details

    def set_flags(self, flags):
        self._flags = flags

    def set_compressed_data(self, data):
        self._compressedData = data

    def set_check_value(self, value):
        self._checkValue = value

# ---------------------------------------------------------------------------------
# Y. Bits
# ---------------------------------------------------------------------------------
# assume it is a hex value
def get_bit(target, n, bitRange=4):
    if (
        (target is not None) and (n in range(0,bitRange)) and (type(target) == str) and 
        (target.isdigit() or (target.upper() >= 'A' and target.upper() <= 'F'))
    ):
        return (1) if (int(target, 16) & (1 << n) > 0) else (0)
    else:
        return None

# =================================================================================
# Main
# =================================================================================

# ---------------------------------------------------------------------------------
# Step 1 : Read PNG image file, and store all the chunks
# ---------------------------------------------------------------------------------
print("\n[*] Execute Step 1...") 
pngDatastream = PngDatastream()

# 1 byte = 8 bits = 2 * 4 bits = 2 * 1 hex digit = 2 hex digits 
with open(file, "rb") as f:
    hexLine = "".join([line.hex() for line in f.readlines()]).upper()  # convert bytes to hex (no need to strip line: each singel byte matters when parsing PNG format)
    
    if hexLine[0:16] == "89504E470D0A1A0A": # png must begin with this eight bytes
        
        # (optional) set png signature to the PngDatastream object
        pngDatastream.set_signature("89504E470D0A1A0A")
        
        chunkStartIdx = 16
        while chunkStartIdx != len(hexLine):
            print("[*] chunkStartIdx: {0}".format(chunkStartIdx))
            
            # parse chunks
            length = int(hexLine[chunkStartIdx : chunkStartIdx+8], 16)                  # get Length
            hexChunkType = hexLine[chunkStartIdx+8 : chunkStartIdx+16]                  # get Chunk Type
            hexChunkData = hexLine[chunkStartIdx+16 : chunkStartIdx+16+length*2]        # get Chunk Data (note: length -> bytes => need *2)
            hexCrc = hexLine[chunkStartIdx+16+length*2 : chunkStartIdx+16+length*2+8]   # get CRC
            assert (length * 2 == len(hexChunkData)), "Inconsistent Data: hex should have a double of length than byte!!"
            assert (len(hexLine[chunkStartIdx : chunkStartIdx+8]) + len(hexChunkType) + len(hexChunkData) + len(hexCrc) == 16+length*2+8), "Inconsistent Data!"
            
            if hexChunkType == '49484452' or hexChunkType == '504C5445' or hexChunkType == '49444154' or hexChunkType == '49454E44': # if not critical chunk type, skip.
                # create new Chunk of corresponding type
                chunk = Chunk.create(hexChunkType)
                assert (chunk.get_length() is None), "Wrong Value!!"
                assert (chunk.get_type() is None), "Wrong Value!!"
                assert (chunk.get_data() is None), "Wrong Value!!"
                assert (chunk.get_crc() is None), "Wrong Value!!"
                
                # extract Chunk Data based on its type (polymorphism)
                # if no corresponding extraction, e.g. IDAT and IEND, use the original hex data.
                chunkData = chunk.extract_data(length, hexChunkData)
                chunkData = (hexChunkData) if (chunkData is None) else (chunkData)

                # store information into Chunk object
                chunk.set_length(length)
                chunk.set_type(hexChunkType)
                chunk.set_data(chunkData)
                chunk.set_crc(hexCrc)
                assert (chunk.get_length() == length), "Wrong Value!!"
                assert (chunk.get_type() == hexChunkType), "Wrong Value!!"
                assert (chunk.get_data() == chunkData), "Wrong Value!!"
                assert (chunk.get_crc() == hexCrc), "Wrong Value!!"

                # store Chunk object into PngDatastream object
                pngDatastream.set_chunk(chunk)

            # update chunk starting index (4 bytes + 4 bytes + length bytes + 4 bytes = 2 * (4 + 4 + length + 4) = 16 + length*2 + 8
            chunkStartIdx += 16 + length*2 + 8
            
    else:
        raise ValueError(hexLine[0:16])

# verify PNG Datastream critique chunks is not None
# PS: PLTE is optional so no checking for that
assert (not (pngDatastream.get_idhr_chunk() is None)), "Is None!!"
assert (not (pngDatastream.get_idat_chunk() is None)), "Is None!!"
assert (not (pngDatastream.get_iend_chunk() is None)), "Is None!!"

# verify chunk data in PNG Datastream critique chunks is not None
# PS: PLTE is optional so no checking for that
assert (not (pngDatastream.get_idhr_chunk().get_data() is None)), "Is None!!"
for idatChunk in pngDatastream.get_idat_chunk():
    assert (not (idatChunk.get_data() is None)), "Is None!!"
assert (not (pngDatastream.get_iend_chunk() is None)), "Is None!!"

# ---------------------------------------------------------------------------------
# Step 2a : Derive Zlib Datastream
# ---------------------------------------------------------------------------------
print("\n[*] Execute Step 2...") 

idatChunks = pngDatastream.get_idat_chunk()
idatChunkData = "".join([idatChunk.get_data() for idatChunk in idatChunks])     # concatenate all chunkData from IDAT chunks

# parse chunk data after concatenating.
compressionMethod = idatChunkData[0:2]         # get zlib compression method 
additionalFlags = idatChunkData[2:4]           # get additional flags
compressedDataBlocks = idatChunkData[4:-8]     # get compressed data blocks
checkValues = idatChunkData[-8:]               # get check value 
assert (len(compressionMethod) == 2), "Wrong Length!!"
assert (len(additionalFlags) == 2), "Wrong Length!!"
assert (len(checkValues) == 8), "Wrong Length!!"
assert (len(compressionMethod) + len(additionalFlags) + len(compressedDataBlocks) + len(checkValues) == len(idatChunkData)), "Inconsistent Length!!"

# create new empty ZlibDatastream
zlibDatastream = ZlibDatastream()
assert (zlibDatastream.get_compression_details() is None), "Wrong Value!!"
assert (zlibDatastream.get_flags() is None), "Wrong Value!!"
assert (zlibDatastream.get_compressed_data() is None), "Wrong Value!!"
assert (zlibDatastream.get_check_value() is None), "Wrong Value!!"

# store information into ZlibDatastream object
zlibDatastream.set_compression_details(compressionMethod)
zlibDatastream.set_flags(additionalFlags)
zlibDatastream.set_compressed_data(compressedDataBlocks)
zlibDatastream.set_check_value(checkValues)
assert (zlibDatastream.get_compression_details() == compressionMethod), "Wrong Value!!"
assert (zlibDatastream.get_flags() == additionalFlags), "Wrong Value!!"
assert (zlibDatastream.get_compressed_data() == compressedDataBlocks), "Wrong Value!!"
assert (zlibDatastream.get_check_value() == checkValues), "Wrong Value!!"

print("[*] compression method:                  {0}".format(zlibDatastream.get_compression_details()))
print("[*] additional flags:                    {0}".format(zlibDatastream.get_flags()))
print("[*] length of compressed data blocks:    {0}".format(len(zlibDatastream.get_compressed_data())))
print("[*] BFINAL (is last block?):             {0}".format(get_bit(zlibDatastream.get_compressed_data()[1], 0))) # bit 0 of byte 0 (i.e. bit 0 of right hex)
print("[*] BTYPE - bit 2:                       {0}".format(get_bit(zlibDatastream.get_compressed_data()[1], 1))) # bit 1 of byte 0 (i.e. bit 1 of right hex)
print("[*] BTYPE - bit 3:                       {0}".format(get_bit(zlibDatastream.get_compressed_data()[1], 2))) # bit 2 of byte 0 (i.e. bit 2 of right hex)
print("[*] check value:                         {0}".format(zlibDatastream.get_check_value()))
print("[*] IDHR Chunk Data:                     {0}".format(pngDatastream.get_idhr_chunk().get_data()))

# ---------------------------------------------------------------------------------
# Step 2b : Decompress Zlib Datastream
# ---------------------------------------------------------------------------------
hexZlibDatastream = "".join([zlibDatastream.get_compression_details(),
                                zlibDatastream.get_flags(),
                                zlibDatastream.get_compressed_data(),
                                zlibDatastream.get_check_value()])

bytesZlibDatastream = bytes.fromhex(hexZlibDatastream) # hex string to bytes for decompression.

bytesFilteredScanlines = zlib.decompress(bytesZlibDatastream, 0)

# hexStrFilteredScanlines = bytesFilteredScanlines.hex().upper() # for reconstruction in the future.

# ---------------------------------------------------------------------------------
# Step 3a : Derive Filtered Scanlines
# ---------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------
# Step 4 : Format and Output PPM
# ---------------------------------------------------------------------------------
image = ""

# --- format header ---
header = ""

# atomic elements
imgType = "P3" # P3 = ppm
width = pngDatastream.get_idhr_chunk().get_data()['width']
height = pngDatastream.get_idhr_chunk().get_data()['height']
maxPixelVal = (1 << (pngDatastream.get_idhr_chunk().get_data()['bitDepth'])) - 1 # 0...255 = (1...256) - 1 = (2**8)-1 = (1<<8)-1

# combine lines
lineOne = imgType
lineTwo = " ".join([str(width), str(height)]) 
lineThree = str(maxPixelVal)
header = "\n".join([lineOne, lineTwo, lineThree])

# print(header)

# --- format data (draft) ---
data = ""
dataList = []
for i in range(0, len(bytesFilteredScanlines)):
    # print("{0} {1}".format(i, rawImgData[i]))
    if pngDatastream.get_idhr_chunk().get_data()['colourType'] == 6 or pngDatastream.get_idhr_chunk().get_data()['colourType'] == 4: # with alpha
        if i % ((width*3)+1) != 0 and i % 4 != 0: # 
            dataList.append(bytesFilteredScanlines[i])
        # elif i % ((width*3)+1) != 0:
        #     print(bytesFilteredScanlines[i])
    else: # without alpha
        if i % ((width*3)+1) != 0:
            dataList.append(bytesFilteredScanlines[i])

data = " ".join([str(data) for data in dataList])

# --- combine header and data; output image ---
image = header + "\n" + data

outFileName = ".".join([fileName, "ppm"])

with open(outFileName,'w') as f:
    f.write(image)

print("[*] Program ends...")