import os
import struct
import json

class TomodachiLifeLtdSaveReader:
    
    def readWchar(self, p, l):
        self.reader.seek(p)
        raw = self.reader.read(l * 2)
        for i in range(0, len(raw), 2):
            if raw[i:i+2] == b"\x00\x00":
                raw = raw[:i]
                break
        return raw.decode("utf-16le")
    def readAscii(self, p, l):
        self.reader.seek(p)
        raw = self.reader.read(l)
        for i in range(len(raw)):
            if raw[i] == 0:
                raw = raw[:i]
                break
        return raw.decode("utf-8")
    def readAsciiArray(self, p, l):
        array = []
        self.reader.seek(p)
        numstring = int.from_bytes(self.reader.read(4), byteorder = "little")
        index = (p + 4)
        for i in range(numstring):
            array.append(self.readAscii(index, l))
            index += l
        return array
    def readWcharArray(self, p, l):
        array = []
        self.reader.seek(p)
        numstring = int.from_bytes(self.reader.read(4), byteorder="little")
        index = p + 4
        for i in range(numstring):
            array.append(self.readWchar(index, l))
            index += l * 2
        return array
    
    def readIntArray(self, p, l, signed = False):
        array = []
        self.reader.seek(p)
        numvalue = int.from_bytes(self.reader.read(4), byteorder = "little")
        index = (p + 4)
        for i in range(numvalue):
            array.append(int.from_bytes(self.reader.read(l), byteorder = "little", signed = signed))
            index += l
        return array

    def readBlobArray(self, p):
        array = []
        self.reader.seek(p)
        numblob = int.from_bytes(self.reader.read(4), byteorder = "little")
        for i in range(numblob):
            blobsize = int.from_bytes(self.reader.read(4), byteorder = "little")
            if (blobsize == 0):
                array.append(None)
            else:
                array.append(self.reader.read(blobsize))
        return array
    def readBoolArray(self, p):
        self.reader.seek(p)
        numbool = int.from_bytes(self.reader.read(4), byteorder = "little")
        array = []
        bytes_to_read = (numbool // 8)
        if (numbool % 8 != 0):
            bytes_to_read += 1
        #alignement
        while bytes_to_read % 4 != 0:
            bytes_to_read += 1
        data = self.reader.read(bytes_to_read)
        for byte in data:
            array.extend([b == '1' for b in format(byte, '08b')[::-1]])
        return array[:numbool]
    
    def readFloatArray(self, p):
        self.reader.seek(p)
        numfloat = int.from_bytes(self.reader.read(0x4), byteorder = "little")
        array = []
        for i in range(numfloat):
            array.append(struct.unpack('<f', self.reader.read(0x4))[0])
        return array
    
    def readDoubleArray(self, p):
        self.reader.seek(p)
        numdouble = int.from_bytes(self.reader.read(0x4), byteorder = "little")
        array = []
        for i in range(numdouble):
            array.append(struct.unpack('<d', self.reader.read(0x8))[0])
        return array
    def readVector3f(self, p):
        self.reader.seek(p)
        v1, v2, v3 = struct.unpack('<fff', self.reader.read(0xc))
        return {"x":v1, "y":v2, "z":v3} #idk if it's xyz but i name them like this for now
    def readVector3fArray(self, p):
        self.reader.seek(p)
        numvector = int.from_bytes(self.reader.read(0x4), byteorder = "little")
        array = []
        index = p + 0x4
        for i in range(numvector):
            array.append(self.readVector3f(index))
            index += 0xc
        return array
            
        
    def parseValue(self):
        #inline values are directly stored inside item["offset"]
        self.value = {}
        for key, value in self.table.items():
            for item in value:
                match key:
                    case "0":
                        #inline | bool
                        if (item["offset"] == 0):
                             self.value[item["hash"]] = False
                        elif (item["offset"] == 1):
                            self.value[item["hash"]] = True
                    case "1":
                        # bool array
                        self.value[item["hash"]] = self.readBoolArray(item["offset"])
                    case "2":
                        # inline | int32
                        self.value[item["hash"]] = item["offset"]
                    case "3":
                        # int32 array
                        self.value[item["hash"]] = self.readIntArray(item["offset"], 4, signed = True)
                    case "4":
                        # inline | float
                        self.value[item["hash"]] = struct.unpack('<f', struct.pack('<I', item["offset"]))[0]
                    case "5":
                        # float array
                        self.value[item["hash"]] = self.readFloatArray(item["offset"])

                    case "6":
                        # inline | idk
                        self.value[item["hash"]] = item["offset"]
                    case "7":
                        # idk array
                        self.value[item["hash"]] = self.readIntArray(item["offset"], 4, signed = False)


                    case "8":
                        # double
                        self.reader.seek(item["offset"])
                        self.value[item["hash"]] = struct.unpack('<d', self.reader.read(8))[0]
                    case "9":
                        # double array
                        self.value[item["hash"]] = self.readDoubleArray(item["offset"])
                    case "10":
                        # vec3f
                        self.value[item["hash"]] = self.readVector3f(item["offset"])
                    case "11":
                        # vec3f array
                        self.value[item["hash"]] = self.readVector3fArray(item["offset"])
                    case "12":
                        # string16
                        self.value[item["hash"]] = self.readAscii(item["offset"], 16)
                    case "13":
                        # string16 array
                        self.value[item["hash"]] = self.readAsciiArray(item["offset"], 16)
                    case "14":
                        # string32
                        self.value[item["hash"]] = self.readAscii(item["offset"], 32)
                    case "15":
                        # string32 array
                        self.value[item["hash"]] = self.readAsciiArray(item["offset"], 32)
                    case "16":
                        # string64
                        self.value[item["hash"]] = self.readAscii(item["offset"], 64)
                    case "17":
                        # string64 array
                        self.value[item["hash"]] = self.readAsciiArray(item["offset"], 64)
                    case "18":
                        # binary
                        self.reader.seek(item["offset"])
                        blobsize = int.from_bytes(self.reader.read(4), byteorder = "little")
                        if (blobsize == 0):
                            self.value[item["hash"]] = None
                        else:
                            self.value[item["hash"]] = self.reader.read(blobsize)
                    case "19":
                        # binary array
                        self.value[item["hash"]] = self.readBlobArray(item["offset"])
                    case "20":
                        # inline uint32
                        self.value[item["hash"]] = item["offset"]
                    case "21":
                        # uint32 array
                        self.value[item["hash"]] = self.readIntArray(item["offset"], 4, signed = True)
                    case "22":
                        # int64
                        self.reader.seek(item["offset"])
                        self.value[item["hash"]] = int.from_bytes(self.reader.read(8), byteorder = "little", signed = True)
                    case "23":
                        # int64 array
                        self.value[item["hash"]] = self.readIntArray(item["offset"], 8, signed = True)
                    case "24":
                        # int64
                        self.reader.seek(item["offset"])
                        self.value[item["hash"]] = int.from_bytes(self.reader.read(8), byteorder = "little", signed = False)
                    case "25":
                        # int64 array
                        self.value[item["hash"]] = self.readIntArray(item["offset"], 8)
                    case "26":
                        # wchar16,
                        self.value[item["hash"]] = self.readWchar(item["offset"], 16)
                    case "27":
                        # wchar16 array
                        self.value[item["hash"]] = self.readWcharArray(item["offset"], 16)
                    case "28":
                        # wchar32
                        self.value[item["hash"]] = self.readWchar(item["offset"], 32)
                    case "29":
                        # wchar32 array
                        self.value[item["hash"]] = self.readWcharArray(item["offset"], 32)
                        if (self.value[item["hash"]][0] != ""):
                            print(self.value[item["hash"]])
                            print(len(self.value[item["hash"]]))
                    case "30":
                        # wchar64
                        self.value[item["hash"]] = self.readWchar(item["offset"], 64)
                    case "31":
                        # wchar64 array
                        self.value[item["hash"]] = self.readWcharArray(item["offset"], 64)
                    case "32":
                        # EOF, inline | idk
                        self.value[item["hash"]] = item["offset"]
                    case _:
                        pass
        
    def read(self, file):
        self.reader = open(file, "rb")
        
        self.value = None
        
        magic = int.from_bytes(self.reader.read(4), byteorder = "little")
        assert magic == 0x01020304
        version = int.from_bytes(self.reader.read(4), byteorder = "little")
        data_start = int.from_bytes(self.reader.read(4), byteorder = "little")
        self.reader.read(0x14) #padding ?
        
        
        value_type = None
        # the value_type seem to define how handle the hash table entry (different type/using of data)
        
    
        hashs = {}
        while (self.reader.tell() < data_start): #maybe a hash table
            param1 = int.from_bytes(self.reader.read(4), byteorder = "little")
            param2 = int.from_bytes(self.reader.read(4), byteorder = "little")
            
            if param1 == 0:
                value_type = param2
                hashs[str(value_type)] = []
                continue
            #idk if it's a hash or just an id
            maybe_hash = param1
            offset = param2
            hashs[str(value_type)].append({"hash":maybe_hash, "offset":offset})
        self.table = hashs
        with open('test.json', "w") as f:
            json.dump(hashs, f, indent = 4)
            
        self.parseValue()
TomodachiLifeLtdSaveReader().read(r"C:\Users\celes\AppData\Roaming\Ryujinx\bis\user\save\0000000000000001\0\Mii.sav")