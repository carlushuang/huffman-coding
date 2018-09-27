# https://www.cs.duke.edu/csed/poop/huff/info/
#
#

from __future__ import print_function
import argparse

def parse_arg():
    parser = argparse.ArgumentParser()
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
        bytes = map(ord, _str)
        return bytes
    
    @staticmethod
    def bytes_to_str_bin(bytes):
        # return a string, only 1&0
        return ' '.join("{:08b}".format(b) for b in bytes)
    
    def _eof_bits(self, eof):
        bits = 0
        while eof:
            bits += 1
            eof = eof >> 1

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
    bytes, _ =  bout.get_bytes()
    return bytes

def deserialize_int32(bytes):
    assert len(bytes) == 4
    i32 = 0
    b_in = bit_array()
    b_in.set_bytes(bytes)
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
def deserialize_node(bytes, eof):
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
    if not bytes:
        return None
    bit_arr = bit_array()
    bit_arr.set_bytes(bytes, eof)
    node = _deserialize(bit_arr)
    return node

def test_tree_node():
    node = tree_node()
    node.insert_left()
    node.insert_right('C')
    node.left.insert_right('D')
    node.left.insert_left('E')
    #node.traverse_in()
    s, eof = serialize_node(node)
    print(" ".join("0x{:x}".format(_s) for _s in s))
    print("eof:0x{:x}".format(eof))
    print(bit_array.bytes_to_str_bin(s))
    new_tree = deserialize_node(s, eof)
    new_tree.traverse_pre()

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
        self.symbol_tbl = self.construct_symbol_tbl(self.huffman_tree)
        #print(self.symbol_tbl)
        ht_code, ht_eof = serialize_node(self.huffman_tree)
        ht_len = serialize_int32(len(ht_code) + 1)
        msg_code, msg_eof = self.serialize_msg(self.symbol_tbl, str_array)
        msg_len = serialize_int32(len(msg_code) + 1)
        bytes = []
        bytes.extend([ord('H'), ord('U'), ord('F'), ord('F')])
        bytes.extend(ht_len)
        bytes.extend([ht_eof])
        bytes.extend(ht_code)
        bytes.extend(msg_len)
        bytes.extend([msg_eof])
        bytes.extend(msg_code)

        return bytes

def huffman_encode(str_array):

    ft = freq_table()
    h_nodes = ft.to_tree(str_array)
    assert h_nodes, "can't construct tree from inputs"
    h_nodes.traverse_pre()
    #ht_code, ht_eof = serialize_node(h_nodes)
    encoder = huffman_encoder()
    bytes = encoder.encode(str_array)
    #print(bytes)


def main():
    args = parse_arg()
    content = []
    if(args.in_file):
        with open(args.in_file, mode='rb') as in_file:
            content = in_file.read()
    elif(args.in_stream):
        content = args.in_stream
    else:
        print('nonthing to read in')
        exit(1)
    print(content)
    huffman_encode(content)


if __name__ == '__main__':
    main()
    #test_tree_node()

