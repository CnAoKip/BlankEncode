import sys, os, chardet


# 默认字典
default_charset = [chr(ch) for ch in range(0x2000, 0x2010)] # 这些字符全为不可见的，有的是特殊空格，有的是 Unicode 操纵字符
encode_suffix = ""
decode_suffix = ""


is_valid_charset = lambda charset: len(set(charset)) == len(charset)

def encode(input: bytes, charset: list) -> str:
    encoded_str = ""
    for b in input:
        encoded_str += charset[b>>4]  # 先转码二进制的高四位，对应2位16进制数的第一位
        encoded_str += charset[b&0xf] # 再转码二进制的低四位，对应2位16进制数的第二位

    return encoded_str


def decode(input: str, charset: list) -> bytes:
    decoded_bytes = bytes() // b''
    try:
        for i in range(0, len(input), 2):
            h = charset.index(input[i])
            l = charset.index(input[i+1])  # 从字典查找并且拼凑出原先的字节
            decoded_bytes += bytes([(h<<4)|l])
    except ValueError:
        print("字典与加密内容不匹配！")
        return bytes()
    return decoded_bytes


def transcode_file(dictPath:str, encodePath:str, decodePath:str):
    dicto = list()
    mode = -1  # 0=Encode 1=Decode
    dicto_encoding = "utf-8" # 默认为 UTF-8
    try:
        if(len(dictPath) == 0): dicto = default_charset # 未指定字典时采用默认的“空白字符”字典
        else:
            with open(dictPath, "rb") as dictFile:
                dictBytes = dictFile.read(16)
                dicto_encoding = chardet.detect(dictBytes)["encoding"] # 判断字典编码
                dicto = list(str(dictBytes, encoding=dicto_encoding))

        if(len(encodePath) == 0):
            mode = 0
            encodePath = "result.enc."+encode_suffix
        if(len(decodePath) == 0):
            if(mode == 0): sys.exit(4)
            mode = 1
            decodePath = "result.dec."+decode_suffix

        if(os.path.exists(decodePath)):
            mode = 0
        if(os.path.exists(encodePath)):
            if(mode == 0): sys.exit(4) # 不覆写
            mode = 1

        if(mode == 0):
            with open(decodePath, "rb") as decodedFile:
                decodedBytes = decodedFile.read()
                decodedFile.close()
                encoded = encode(decodedBytes,dicto)
            with open(encodePath, "w", encoding=dicto_encoding) as encodedFile: # “加密”后文件应与字典编码一致
                encodedFile.write(encoded)
                encodedFile.close()
                sys.exit(0)

        if(mode == 1):
            with open(encodePath, "rb") as encodedFile:
                encodedBytes = encodedFile.read()
                encodedFile.close()
                encoded_encoding = chardet.detect(encodedBytes)["encoding"]
                decoded = decode(str(encodedBytes, encoding = encoded_encoding), dicto)

            with open(decodePath, "wb") as decodedFile:
                decodedFile.write(decoded)
                decodedFile.close()
                sys.exit(0)
    except IOError:
        print("文件读写错误！")


# 为了方便操作，待操作文件名（或扩展名）中需要一个修饰符。
# 规则是文件名中含有.enc为待编码文件，.dec为待解码文件，.dict为字典文件。
if __name__ == "__main__":
    dictPath = ""
    encodePath = ""
    decodePath = ""
    argv = sys.argv
    argc = len(argv)
    if(argc < 2): # 打印帮助
        print("用法：BlankCode.py input [dict][output]\n\
其中，输入与两个可选参数文件名（或扩展名）中需要一个修饰符。规则是文件名中含有.enc为待解码文件，.dec为待编码文件，.dict为字典文件。\n\
.enc 或 .dec 前（相邻）可以指定转码后默认文件扩展名，如 1.mp4.dec.html 编码后默认输出 result.enc.mp4。\n\
字典内容应为无重复字符且长度为 16 的字符串。如果字典未指定，采用默认空白字典。")
        os._exit(1)
    for i in range(1, argc):
        splited = ['']+argv[i].split('.') # 防止上来就是 .enc 这类导致问题的情况
        if(splited.count("enc")):
            encodePath = argv[i]
            decode_suffix = splited[splited.index("enc") - 1]
        if(argv[i].split('.').count("dec")):
            decodePath = argv[i]
            encode_suffix = splited[splited.index("dec") - 1]
        if(argv[i].split('.').count("dict")): dictPath = argv[i]

    transcode_file(dictPath, encodePath, decodePath)