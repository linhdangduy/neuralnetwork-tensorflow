import tensorflow as tf
import numpy as np
#from tensorflow.python.ops import rnn
from tensorflow.contrib.rnn import BasicRNNCell, BasicLSTMCell
import codecs
import sys
dir1 = "/home/linhdang/rnn/neuralnetwork-tensorflow/dataset/NonTag4type.tag"
dir2 = "/home/linhdang/rnn/neuralnetwork-tensorflow/dataset/SubDict_vc.txt"

# is it better to eliminate from data (!?)
# weak_stop_token = [',',';','...','"','(',')','[',']','{','}','<','>','/','*','@',
 #                  '#','$','%','^','&','-','_','+','=','|','~','`','“','”','-DOCSTART-']

# end of one sequence. Is it better to eliminate from data (!?)
strong_stop_token = ['.','\n',':','?','!']

# word classification: 11 classes
named_entity = ['O', 'I-PER', 'I-LOC', 'I-TOUR', 'I-ORG', 'I-PRO',
                     'B-PER', 'B-LOC', 'B-TOUR', 'B-ORG', 'B-PRO']

class dataset:

    # return @dict[word: listValueOfFloatTypeVector]
    def makeDictFromDataset(self):
        # count = 0
        dictionary = {}
        with open(dir2) as f:
            #    num = tf.cast(float(split[1]), tf.float32)
            #    print(sess.run(num))
            for line in f:
                # count += 1
                split = line.rstrip().lstrip().split(" ")
                word = split.pop(0).lower()

                # map string type vector to float type vector
                split = list(map(float, split))
                dictionary[word] = split
                # if count < 20:
                #     print(split)
                #     print(dictionary[word])
                #     print(word)
                #     print("-------")
        return dictionary

    # wasted resource
    def getEntity(self, entity):
        list = [0] * 11
        list[named_entity.index(entity)] = 1
        # if entity != "O":
        #     print(entity+" "+str(list))
        return list

    def getData(self, dict):
        inputSequence = [] # list of word in inputSequence
        outputSequence = [] # list of word in outputSequence
        inputBatch = [] # list of sequence in inputBatch
        outputBatch = [] # list of sequence in outputBatch
        flag = False
        count = []
        with codecs.open(dir1, "r", encoding='utf-8', errors='ignore') as f:
        #with open(dir1) as f:
            for line in f:
                split = line.rstrip().lstrip().split(" ")
                if line.__contains__("DOCSTART"):
                    # print("good")
                    continue
                if len(split) >= 2:
                    flag = True
                    wordVector = dict.get(split[0].lower())
                    if wordVector == None:
                        wordVector = np.random.uniform(-1,1,200) # generate word vector if not exist
                        wordVector = list(wordVector)
                #    if len(wordVector) == 200:

                    if len(split) == 2:
                        if (split[0] != "CH"):
                            outputSequence.append(self.getEntity('O'))
                        else:
                            continue
                    else:
                        outputSequence.append(self.getEntity((split[2])))
                    inputSequence.append(wordVector)
                    if split[0] in strong_stop_token:
                        inputBatch.append(inputSequence)
                        outputBatch.append(outputSequence)
                        # if len(outputSequence) != 179:
                        count.append(len(outputSequence))
                        inputSequence = []
                        outputSequence = []
                        flag = False
                if line.rstrip().lstrip() == "" and flag == True:
                    inputBatch.append(inputSequence)
                    outputBatch.append(outputSequence)
                    inputSequence = []
                    outputSequence = []
                    flag = False
        # each word represented by float type vector
        return inputBatch, outputBatch

    def enummerate(self, inputBatch):
        listOfLength = [0]*180
        for string in inputBatch:
            listOfLength[len(string)]+=1
        print(listOfLength)

    def length(self, input):
        used = tf.sign(tf.reduce_max(tf.abs(input), reduction_indices=2))
        length = tf.reduce_sum(used, reduction_indices=1)
        length = tf.cast(length, tf.int32)
        return length

class SequenceLabelling:

    def __init__(self, data, target, num_hidden = 200, num_layers = 1, learning_rate = 0.1):
        self.data = data
        self.target = target # batch size * timesteps(input sequence length) * features (word vector length)
        self.num_hidden = num_hidden # bactch size * timesteps * output size (classes size)
        self.num_layers = num_layers
        self.predict = self.prediction()
        self.er = self.error()
        self.loss = self.cost()
        self.opt = self.optimize()
        self.learning_rate = learning_rate

    def prediction(self):
        numu = int(self.data.get_shape()[2])
        print(int(self.data.get_shape()[2]))
        print(int(self.data.get_shape()[1]))
        print(int(self.data.get_shape()[0]))
        cell = BasicRNNCell(numu)
        state = tf.zeros([10, cell.state_size])
        output, state = cell(
            #cell,
            self.data,
            state
            #dtype = tf.float32
        )
        # softmax layer
        max_length = int(self.target.get_shape()[1]) # timesteps
        num_classes = int(self.target.get_shape()[2]) # output size
        # weight [num_hidden, output size] bias [output size]
        weight, bias = self.weight_and_bias(numu, num_classes)
        # Flatten to apply same weights to all time steps
        # nhưng nếu tổng số phần tử không chia hết cho số các ẩn số thì sao?
        output = tf.reshape(output, [-1, numu])
        predictionn = tf.nn.softmax(tf.matmul(output, weight)+bias)
        predictionn = tf.reshape(predictionn, [-1, max_length, num_classes])
        return predictionn

    def cost(self):
        cross_entropy = -tf.reduce_sum(
            self.target * tf.log(self.predict), reduction_indices=2)
        cross_entropy = tf.reduce_mean(cross_entropy)
        return cross_entropy


    def optimize(self):
        # learning_rate = 0.005
        optimizer = tf.train.RMSPropOptimizer(self.learning_rate)
        return optimizer.minimize(self.loss)

    def error(self):
        mistakes = tf.not_equal(
            tf.argmax(self.target, 2), tf.argmax(self.predict, 2))
        return tf.reduce_mean(tf.cast(mistakes, tf.float32))
    #
    def weight_and_bias(self, in_size, out_size):
        weight = tf.truncated_normal([in_size, out_size], stddev=0.01)
        bias = tf.constant(0.1, shape=[out_size])
        return tf.Variable(weight), tf.Variable(bias)

    def pr(self):
        var = tf.Variable(tf.truncated_normal([2,3,4],stddev = 0.1))
        print("linhlinhlinh")
        return var


process = dataset()
dict = process.makeDictFromDataset()
print("kich co tu dien", len(dict))
x, y = process.getData(dict)
#process.enummerate(x)
# batch size x, y = 23304, 23304
print("do dai cua batch input", len(x))
print("do dai cua batch output", len(y))
# x, y max_length of sequence = 179
print("do dai lon nhat cua moi xau", max(len(z) for z in x))
print("do dai nho nhat cua moi xau", min(len(z) for z in x))

# check for length
def check_length_afer_padding(x, l):
    for string in x:
        if len(string) != 179:
            print("la1")
        for word in string:
            if len(word) != l:#11
                print("la2")
# padding for input
def padding(x,type):
    #feature_length = 0
    if type == "in":
        feature_length = 200
    else: feature_length = 11
    for string in x:
        pad = []
        if len(string) < 179:
            for word in range(179 - len(string)):
                pad.append([0] * feature_length)
            string += pad
    return x

num_start = 0
num_immediate = 21000
num_end = 21000
x_train = x[:num_immediate]
y_train = y[:num_immediate]
x_test = x[21000:]
y_test = y[21000:]
#print(type(x_test))

x_test = padding(x_test, "in")
y_test = padding(y_test, "out")
check_length_afer_padding(x_test,200)
check_length_afer_padding(y_test,11)

#x_test = tf.convert_to_tensor(x_test)
#y_test = tf.convert_to_tensor(y_test)

"""
data = tf.placeholder(tf.float32, [None, 179, 200])
print(type(x_test))

with tf.Session() as sess:
    #sess.run(tf.initialize_all_variables())
    #print("shape of x_placeholder", sess.run(tf.shape(data), feed_dict={data:x_train}))
    print("shape of x_test", sess.run(tf.shape(x_test)))
    print("shape of y_test", sess.run(tf.shape(y_test)))
    print(sess.run(x_test[0][0][0]))
"""
print("start")

#print(len(x_train[110]))

data = tf.placeholder(tf.float32, [10, 179, 200])
target = tf.placeholder(tf.float32, [10, 179, 11])
model = SequenceLabelling(data, target)
sess = tf.Session()
sess.run(tf.initialize_all_variables())
for epoch in range(50):
    if (epoch > 25):
        model.learning_rate = 0.005
    for index in range(2100):
        x_feed = x_train[index*10:(index+1)*10]
        y_feed = y_train[index*10:(index+1)*10]
        x_feed = padding(x_feed, "in")
        y_feed = padding(y_feed, "out")
        sess.run(model.opt,
                feed_dict = {data: x_feed, target: y_feed})
    error = sess.run(model.er,
                feed_dict = { data: x_test, target: y_test})
    print('Epoch {:2d} error {:f}%'.format(epoch + 1, 100*error))

"""
convert = x[:1]
for i in convert:
    print(len(i))
    for j in i:
        print(len(j))

va = tf.convert_to_tensor(convert)
"""
"""

#x = tf.Variable(x)
#y = tf.Variable(y)

model = NER(data, target)
sess = tf.Session()
sess.run(tf.initialize_all_variables())
for epoch in range(10):
    for _ in range(100):
        sess.run(model.optimize, {
            data: x, target: y})
    error = sess.run(model.error, {
        data: x, target: y})
    print('Epoch {:2d} error {:3.1f}%'.format(epoch + 1, 100 * error))

#x = tf.Variable(x)
#with tf.Session() as sess:
#    print(sess.run(tf.shape(x)))

 length_of input each word = 200, output each word = 11
    x_input (batch_size, sequence_size, word_size)
    y_output (batch_size, sequence_size, class_size)
 => batchsize*time steps*features = data shape

 one word is putted into one cell - GRUCell or LSTMCell
 a sequence is putted into n-timesteps - dynamic_rnn or rnn(cell, data)
 - which return outputActivations and lastHiddenState as tensors.
"""
