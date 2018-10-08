# https://www.cs.duke.edu/csed/poop/huff/info/
#
#

from __future__ import print_function
import argparse

VERBOSE = False

def parse_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', dest='encode', action='store_true', help='encode message')
    parser.add_argument('-d', dest='decode', action='store_true', help='decode message')
    parser.add_argument('-f', dest='in_file', action='store', type=str, help='get input from file')
    parser.add_argument('-i', dest='in_stream', action='store', type=str, help='get input from stdin')
    parser.add_argument('-o', dest='out_file', action='store', type=str, help='output to a file')
    return parser.parse_args()

def is_print(ch):
    # https://en.cppreference.com/w/c/string/byte/isprint
    return ch <=126 and ch>=32

class bit_array(object):
    # big-endian bit stream
    def __init__(self):
        self.cache_byte = 0
        self.cache_bit_cnt = 0
        self.byte_array = []
        self.eof = 0
        self.eof_bits = 0

    @staticmethod
    def str_to_bytes(_str):
        byte_array = map(ord, _str)
        return byte_array
    
    @staticmethod
    def bytes_to_str_bin(byte_array):
        # return a string, only 1&0
        return ' '.join("{:08b}".format(b) for b in byte_array)
    
    def _eof_bits(self, eof):
        bits = 0
        while eof:
            bits += 1
            eof = eof >> 1
        return bits

    def set_bytes(self, byte_array, eof = 0):
        self.eof = eof
        self.eof_bits = self._eof_bits(eof)
        if type(byte_array) is str:
            self.byte_array = list(self.str_to_bytes(byte_array))
        elif type(byte_array) is list:
            self.byte_array = list(byte_array)
        else:
            assert False, "input byte_array type not supported!"

    # this will pad 0 to get byte
    def get_bytes(self):
        eof = 0
        while self.cache_bit_cnt != 0:
            self.write(0)
            eof = eof << 1
            eof |= 1
        return self.byte_array, eof

    def write(self, bit):
        self.cache_byte = self.cache_byte << 1
        self.cache_byte |= (bit & 1)
        self.cache_bit_cnt += 1
        if(self.cache_bit_cnt >= 8):
            self.byte_array.append(self.cache_byte)
            self.cache_byte = 0
            self.cache_bit_cnt = 0
    
    def write_ch(self, ch):
        self.write_8(ord(ch))

    def write_8(self, v):
        # v should be 8 bit
        self.write_n(v, 8)
    
    def write_n(self, v, n):
        # v should be n bit
        cnt = n
        while cnt:
            bit = 1 if v & 0x80 else 0
            v = v<<1
            v &= 0xff
            self.write(bit)
            cnt -=1

    # if eof, return -1
    def read(self):
        if not self.byte_array and self.cache_bit_cnt <= self.eof_bits:
            return -1
        if self.cache_bit_cnt == 0:
            self.cache_bit_cnt = 8
            self.cache_byte = self.byte_array.pop(0)
        bit = 1 if (self.cache_byte & 0x80) else 0
        #print("byte:{}, cache_byte:{}, cnt:{}, bit:{}".format(self.byte_array, self.cache_byte, self.cache_bit_cnt, bit))
        self.cache_bit_cnt -= 1
        self.cache_byte = self.cache_byte << 1
        self.cache_byte &= 0xff
        return bit
    
    def read_8(self):
        cnt = 8
        byte = 0
        while cnt:
            bit = self.read()
            if bit == -1:
                break
            byte = byte << 1
            byte |= bit
            cnt -= 1
        return byte

class tree_node(object):
    def __init__(self, value=0):
        self.left = None
        self.right = None
        self.value = value  # need be a value contain byte, 8bit
    def insert_left(self, new_value=0):
        new_v = 0
        if type(new_value) is str:
            new_v = ord(new_value)
        else:
            new_v = new_value
        new_node = tree_node(new_v)
        new_node.left = self.left
        self.left = new_node
        return new_node
    def insert_right(self, new_value=0):
        new_v = 0
        if type(new_value) is str:
            new_v = ord(new_value)
        else:
            new_v = new_value
        new_node = tree_node(new_v)
        new_node.right = self.right
        self.right = new_node
        return new_node
    def traverse_pre(self):
        # only debug use
        if is_print(self.value):
            print("\'{}\'({})".format(chr(self.value), self.value))
        else:
            print(self.value)
        if(self.left):
            self.left.traverse_pre()
        else:
            print(-1)
        if(self.right):
            self.right.traverse_pre()
        else:
            print(-1)

    def is_leaf(self):
        return self.left == None and self.right == None
    def is_internal(self):
        return self.left and self.right

def serialize_int32(i32):
    bout = bit_array()
    cnt = 4
    while cnt:
        i32 = i32 & 0xffffffff
        byte = (i32 & 0xff000000) >> 24
        bout.write_8(byte)
        cnt -= 1
        i32 = i32 << 8
    byte_array, _ =  bout.get_bytes()
    return byte_array

def deserialize_int32(byte_array):
    assert len(byte_array) == 4
    i32 = 0
    b_in = bit_array()
    b_in.set_bytes(byte_array)
    cnt = 4
    while cnt:
        i32 <<= 8
        i32 |= b_in.read_8()
        cnt -=1
    return i32

# node->byte_array, big endian
def serialize_node(node):
    def _serialize(node, ba):
        # traverse pre-order
        if node.is_leaf():
            ba.write(1)
            ba.write_8(node.value)
        elif node.is_internal():
            ba.write(0)
            _serialize(node.left, ba)
            _serialize(node.right, ba)
        else:
            assert False, "this node is neither leaf nor internal, should not happen"

    bit_arr = bit_array()
    _serialize(node, bit_arr)
    return bit_arr.get_bytes()

# byte_array->node
def deserialize_node(byte_array, eof):
    def _deserialize(ba):
        bit = ba.read()
        if(bit == 0):
            # internal node
            node = tree_node()
            node.left = _deserialize(ba)
            node.right = _deserialize(ba)
            return node
        elif(bit == 1):
            node = tree_node()
            node.value = ba.read_8()
            return node
        # maybe the end
        return None
    if not byte_array:
        return None
    bit_arr = bit_array()
    bit_arr.set_bytes(byte_array, eof)
    node = _deserialize(bit_arr)
    return node

class freq_table(object):
    def __init__(self):
        self.freqs = [0]*256
    def _build_nodes_from_table(self, freqs):
        # freqs index is the symbol(0-255)
        # freqs value is frequency itself
        ctor_list = []
        if not freqs:
            return None
        for i, freq in enumerate(freqs):
            if freq == 0:
                continue
            node = tree_node(i)
            ctor_list.append((freq, node))
        if not ctor_list:
            return None

        while True:
            if len(ctor_list) == 1:
                break
            ctor_list.sort(key=lambda tup:tup[0], reverse=True)
            n1 = ctor_list.pop()
            n2 = ctor_list.pop()
            inode = tree_node()
            inode.left = n2[1]
            inode.right = n1[1]
            ctor_list.append( (n1[0]+n2[0], inode) )
        return ctor_list[0][1]

    def to_tree(self, str_array):
        if not str_array:
            return None
        for b in str_array:
            key = 0
            if type(b) is str:
                key = ord(b)
            else:
                key = b
            self.freqs[key] += 1

        return self._build_nodes_from_table(self.freqs)

class huffman_decoder(object):
    def __init__(self):
        self.huffman_tree = None
    @staticmethod
    def decode_msg(huffman_tree, msg, eof=0, decode_as_chr=True):
        ba = bit_array()
        ba.set_bytes(msg, eof)
        str_array = []
        node = huffman_tree
        while True:
            if node.is_leaf():
                v = node.value
                str_array.append( chr(v) if decode_as_chr else v )
                node = huffman_tree
            bit = ba.read()
            if bit == -1:
                break
            if bit == 0:
                node = node.left
            else:
                node = node.right
            #print("str_array:{}".format(str_array))
        return str_array


    def decode(self, byte_array):
        assert type(byte_array) is list
        # magic
        magic = byte_array[:4] 
        #print(magic)
        assert magic[0] == ord('H') and magic[1] == ord('U') and magic[2] == ord('F') and magic[3] == ord('F'), \
                        "magic not valid, please check"
        byte_array = byte_array[4:]

        # TODO: need beter deserialize action
        # huffman tree part
        ht_len = deserialize_int32(byte_array[:4])
        ht_total = byte_array[4 : (ht_len+4)]
        ht_eof = ht_total[0]
        ht_code =  ht_total[1:]
        byte_array = byte_array[(ht_len+4):]
        # msg part
        msg_len = deserialize_int32(byte_array[:4])
        msg_total = byte_array[4 : (msg_len+4)]
        msg_eof = msg_total[0]
        msg_code = msg_total[1:]

        #print("ht_len:{}".format(ht_len))
        #print("ht_eof:{}".format(ht_eof))
        #print("ht_code:{}".format(ht_code))

        #print("msg_len:{}".format(msg_len))
        #print("msg_eof:{}".format(msg_eof))
        #print("msg_code:{}".format(msg_code))

        # rebuild the huffman tree
        self.huffman_tree = deserialize_node(ht_code, ht_eof)

        str_array = self.decode_msg(self.huffman_tree, msg_code, msg_eof, True )
        return ''.join(str_array)



class huffman_encoder(object):
    def __init__(self):
        self.freq_tbl = freq_table()
        self.huffman_tree = None
        self.symbol_tbl = {}
    @staticmethod
    def construct_symbol_tbl(huffman_tree):
        def _traverse_ctor(node, tbl, code):
            if node.is_leaf():
                tbl[node.value] = code
            elif node.is_internal():
                _traverse_ctor(node.left, tbl, code+'0')
                _traverse_ctor(node.right, tbl, code+'1')
        tbl = {}
        _traverse_ctor(huffman_tree, tbl, '')
        return tbl

    @staticmethod
    def serialize_msg(tbl, str_array):
        bout = bit_array()
        for s in str_array:
            c = ord(s)
            assert c in tbl, "char not in symbol table, should not happen"
            code = tbl[c]
            for c_str in code:
                bit = 1 if c_str == '1' else 0
                bout.write(bit)
        return bout.get_bytes()

    def encode(self, str_array):
        self.huffman_tree = self.freq_tbl.to_tree(str_array)
        assert self.huffman_tree, "fail to construct tree"
        self.symbol_tbl = self.construct_symbol_tbl(self.huffman_tree)
        #print(self.symbol_tbl)
        ht_code, ht_eof = serialize_node(self.huffman_tree)
        ht_len = serialize_int32(len(ht_code) + 1)
        msg_code, msg_eof = self.serialize_msg(self.symbol_tbl, str_array)
        msg_len = serialize_int32(len(msg_code) + 1)
        byte_array = []
        byte_array.extend([ord('H'), ord('U'), ord('F'), ord('F')])
        byte_array.extend(ht_len)
        byte_array.extend([ht_eof])
        byte_array.extend(ht_code)
        byte_array.extend(msg_len)
        byte_array.extend([msg_eof])
        byte_array.extend(msg_code)

        return byte_array

def huffman_encode(str_array):
    encoder = huffman_encoder()
    byte_array = encoder.encode(str_array)
    return byte_array

def huffman_decode(byte_array):
    decoder = huffman_decoder()
    str_array = decoder.decode(byte_array)
    return str_array

def main():
    args = parse_arg()
    content = []
    if(args.in_file):
        with open(args.in_file, mode='rb') as in_file:
            content = in_file.read()
    elif(args.in_stream):
        if args.decode:
            print('decode do not support read from stdin')
            exit(1)
        content = args.in_stream
    else:
        print('nothing to read in')
        exit(1)
    #print(content)
    if args.encode:
        encoded_bytes = huffman_encode(content)
        in_bytes = len(content)
        out_bytes = len(encoded_bytes)
        if args.out_file:
            with open(args.out_file, "wb") as out_file:
                for b in encoded_bytes:
                    out_file.write(chr(b))
        if VERBOSE:
            cmp_rate = float(in_bytes)/float(out_bytes)
            print("compression rate:{:.2f}".format(cmp_rate))

    elif args.decode:
        byte_array = map(ord, content)
        #print(byte_array)
        str_array = huffman_decode(byte_array)
        #print("str:{}".format(str_array))
        if args.out_file:
            with open(args.out_file, "wb") as out_file:
                #for b in str_array:
                out_file.write(str_array)
        else:
            print(str_array)
    else:
        print("you must specify -e or -d")
        return


if __name__ == '__main__':
    main()

