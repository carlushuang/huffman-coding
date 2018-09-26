from __future__ import print_function
import argparse

def parse_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', dest='in_file', action='store', type=str, help='get input from file')
    parser.add_argument('-i', dest='in_stream', action='store', type=str, help='get input from stdin')
    parser.add_argument('-o', dest='out_file', action='store', type=str, help='output to a file')
    return parser.parse_args()

class tree_node(object):
    def __init__(self, value):
        self.left = None
        self.right = None
        self.value = value  # need be a str
    def insert_left(self, new_value):
        new_node = tree_node(new_value)
        new_node.left = self.left
        self.left = new_node
        return new_node
    def insert_right(self, new_value):
        new_node = tree_node(new_value)
        new_node.right = self.right
        self.right = new_node
        return new_node
    def traverse_pre(self):
        print(self.value)
        if(self.left):
            self.left.traverse_pre()
        else:
            print('\0')
        if(self.right):
            self.right.traverse_pre()
        else:
            print('\0')

LEAF_CHAR = '\0'

def serialize_node(node):
    # traverse pre-order
    s = []
    s += node.value
    if(node.left):
        s += serialize_node(node.left)
    else:
        s += LEAF_CHAR
    if(node.right):
        s += serialize_node(node.right)
    else:
        s += LEAF_CHAR
    return s

def deserialize_node(stream):
    #
    if(len(stream) == 0):
        return None
    val = stream[0]
    stream.pop(0)
    if(val==LEAF_CHAR):
        return None
    node = tree_node(val)
    node.left = deserialize_node(stream)
    node.right = deserialize_node(stream)
    return node

def test_tree_node():
    node = tree_node('A')
    node.insert_left('B')
    node.insert_right('C')
    node.left.insert_right('D')
    node.left.insert_left('E')
    #node.traverse_in()
    s = serialize_node(node)
    print(s)
    new_tree = deserialize_node(s)
    new_tree.traverse_pre()

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
