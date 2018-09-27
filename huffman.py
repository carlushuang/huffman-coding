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
    def build_table(self, str_array):
        if not str_array:
            return None
        for b in str_array:
            key = 0
            if type(b) is str:
                key = ord(b)
            else
                key = b
            self.freqs[key] += 1

        return self.freqs


def haffman_encode(str_array):
    pass

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
    #print(content)


if __name__ == '__main__':
    #main()
    test_tree_node()

