from bitstring import Bits

import pyximport
import unittest
print("Have Cython")
pyximport.install()
import deduplicator.cyHamDb as hamDb
import dhash
from PIL import Image
import imagehash

class DHash(object):
    @staticmethod
    def calculate_hash(image):
        """
        计算图片的dHash值
        :param image: PIL.Image
        :return: dHash值,string类型
        """
        difference = DHash.__difference(image)
        # 转化为16进制(每个差值为一个bit,每8bit转为一个16进制)
        decimal_value = 0
        hash_string = ""
        for index, value in enumerate(difference):
            if value:  # value为0, 不用计算, 程序优化
                decimal_value += value * (2 ** (index % 2))
            if index % 2 == 1:  # 每8位的结束
                hash_string += str(hex(decimal_value)[2:].rjust(2, "0"))  # 不足2位以0填充。0xf=>0x0f
                decimal_value = 0
        return hash_string

    @staticmethod
    def hamming_distance(first, second):
        """
        计算两张图片的汉明距离(基于dHash算法)
        :param first: Image或者dHash值(str)
        :param second: Image或者dHash值(str)
        :return: hamming distance. 值越大,说明两张图片差别越大,反之,则说明越相似
        """
        # A. dHash值计算汉明距离
        if isinstance(first, str):
            return DHash.__hamming_distance_with_hash(first, second)

        # B. image计算汉明距离
        hamming_distance = 0
        image1_difference = DHash.__difference(first)
        image2_difference = DHash.__difference(second)
        for index, img1_pix in enumerate(image1_difference):
            img2_pix = image2_difference[index]
            if img1_pix != img2_pix:
                hamming_distance += 1
        return hamming_distance

    @staticmethod
    def __difference(image, ):
        """
        *Private method*
        计算image的像素差值
        :param image: PIL.Image
        :return: 差值数组。0、1组成
        """
        resize_width = 9
        resize_height = 8
        # 1. resize to (9,8)
        smaller_image = image.resize((resize_width, resize_height))
        # 2. 灰度化 Grayscale
        grayscale_image = smaller_image.convert("L")
        # 3. 比较相邻像素
        pixels = list(grayscale_image.getdata())
        difference = []
        for row in range(resize_height):
            row_start_index = row * resize_width
            for col in range(resize_width - 1):
                left_pixel_index = row_start_index + col
                difference.append(pixels[left_pixel_index] > pixels[left_pixel_index + 1])
        return difference

    @staticmethod
    def __hamming_distance_with_hash(dhash1, dhash2):
        """
        *Private method*
        根据dHash值计算hamming distance
        :param dhash1: str
        :param dhash2: str
        :return: 汉明距离(int)
        """
        difference = (int(dhash1, 16)) ^ (int(dhash2, 16))
        return bin(difference).count("1")


def b2i(binaryStringIn):
	if len(binaryStringIn) != 64:
		print("ERROR: Passed string not 64 characters. String length = %s" % len(binaryStringIn))
		print("ERROR: String value '%s'" % binaryStringIn)
		raise ValueError("Input strings must be 64 chars long!")
	val = Bits(bin=binaryStringIn)
	return val.int



TEST_DATA = [
    #5810423a45d4cd22d4ad45d23a104058d81040202725d827000d5dd27a1040d8
	"0000000000000000000000000000000000000000000000000000000000000000",  # 0
	"1111111111111111111111111111111111111111111111111111111111111111",  # 1
	"1000000000000000000000000000000000000000000000000000000000000000",  # 2
	"0111111111111111111111111111111111111111111111111111111111111111",  # 3
	"1100000000000000000000000000000000000000000000000000000000000000",  # 4
	"0100000000000000000000000000000000000000000000000000000000000000",  # 5
	"0000000000000000000000000000000000000001111111111111111000000000",  # 6
	"0000000000000000000000000000000000000011111111111111110000000000",  # 7
	"0000000000000000000000000000000000000001111111111111111000000000",
    # 81111111000000000000000000000000000000000000000000000000000000111100000000
	# "0000000000000000000000000001100000000001111111111111111000000000",  # 9
	# "0000000000000000000000000011100000000001111111111111111000000000",  # 10
	# "0000000000000000000000000010100000000001111111111111111000000000",  # 11
	# "0000000000000000000000000011000000000001111111111111111000000000",  # 12
	# "0000000000000000000000000001000000000001111111111111111000000000",  # 13
	# "0000000000000000000000000101000000000001111111111111111000000000",  # 14
	# "0000000000000000000000001101000000000001111111111111111000000000",  # 15
]

def trans(my_hexdata):
    scale = 16  ## equals to hexadecimal
    num_of_bits = 64
    return bin(int(my_hexdata, scale))[2:].zfill(num_of_bits)

tree = hamDb.BkHammingTree()
for nodeId, node_hash in enumerate(TEST_DATA):
    print("Inserting node id: ", nodeId, "hash", node_hash, "value: ", b2i(node_hash))
    node_hash = b2i(node_hash)
    tree.unlocked_insert(node_hash, nodeId)

image = Image.open('data/t1.png')
#row, col = dhash.dhash_row_col(image, size=8)
#hash = dhash.format_hex(row, col)
hash = imagehash.phash(image)
print(str(hash))
hash = trans(str(hash))
print(hash)
tgtHash1 = b2i(hash)
tree.unlocked_insert(tgtHash1, 15764)


image = Image.open('data/t2.png')
hash = imagehash.phash(image)
print(str(hash))
hash = trans(str(hash))
print(hash)
tgtHash2 = b2i(hash)
tree.unlocked_insert(tgtHash2, 15765)

image = Image.open('data/set.png')
hash = imagehash.phash(image)
print(str(hash))
hash = trans(str(hash))
print(hash)
tgtHash3 = b2i(hash)
tree.unlocked_insert(tgtHash3, 15766)

image = Image.open('data/q1.jpeg')
hash = imagehash.phash(image)
print(str(hash))
hash = trans(str(hash))
print(hash)
tgtHash4 = b2i(hash)
tree.unlocked_insert(tgtHash4, 15767)

image = Image.open('data/q2.jpeg')
hash = imagehash.phash(image)
print(str(hash))
hash = trans(str(hash))
print(hash)
tgtHash5 = b2i(hash)
tree.unlocked_insert(tgtHash5, 15768)

image = Image.open('data/w1.jpeg')
hash = imagehash.phash(image)
print(str(hash))
hash = trans(str(hash))
print(hash)
tgtHash6 = b2i(hash)
tree.unlocked_insert(tgtHash6, 15769)

image = Image.open('data/w2.jpeg')
hash = imagehash.phash(image)
print(str(hash))
hash = trans(str(hash))
print(hash)
tgtHash7 = b2i(hash)
tree.unlocked_insert(tgtHash7, 15770)

ret = tree.getWithinDistance(tgtHash6, 5)
print(ret)