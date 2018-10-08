huffman coding
--------------

simple python script for haffman encode/decode. 
this is also the assignment of https://www.cs.duke.edu/csed/poop/huff/info/

the encoded file has the following structure:

```
+---------+
|  HUFF   | magic, 4 byte, "HUFF"
+---------+
| ht_len  | huffman tree length in byte, 4 byte
| ht_eof  | huffman tree eof
| ht      | huffman tree structure
+---------+
| msg_len | encoded message length in byte, 4 byte
| msg_eof | encoded message eof
| msg_code| encoded message huffman code
+---------+
```

usage:
```
# encode from stdin
python huffman.py -e -i "test message to be encode" -o msg.huff

# encode from <file>
python huffman.py -e -f <file> -o msg.huff

# decode from msg.huff, result in msg.raw
python huffman.py -d -f msg.huff -o msg.raw

```