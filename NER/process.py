import tensorflow as tf
import numpy as np
from tensorflow.python.ops import rnn, rnn_cell
dir1 = "/home/bkhn/rnn/neuralnetwork-tensorflow/dataset/NonTag4type.tag"
dir2 = "/home/bkhn/rnn/neuralnetwork-tensorflow/dataset/SubDict_vc.txt"

# is it better to eliminate from data (!?)
weak_stop_token = [',',';','...','"','(',')','[',']','{','}','<','>','/','*','@',
                   '#','$','%','^','&','-','_','+','=','|','~','`','“','”','-DOCSTART-']

# end of one sequence. Is it better to eliminate from data (!?)
strong_stop_token = ['.','\n',':','?','!']

# word classification: 11 classes
named_entity = ['O', 'I-PER', 'I-LOC', 'I-TOUR', 'I-ORG', 'I-PRO',
                     'B-PER', 'B-LOC', 'B-TOUR', 'B-ORG', 'B-PRO']

class dataset:
    # return @dict[word: listValueOfFloatTypeVector]
    def makeDictFromDataset(self):
        dictionary = {}
        with open(dir2) as f:
            #    num = tf.cast(float(split[1]), tf.float32)
            #    print(sess.run(num))
            for line in f:
                split = line.rstrip().lstrip().split(" ")
                word = split.pop(0).lower()
                # map string type vector to float type vector
                split = list(map(float, split))
                dictionary[word] = split
        return dictionary

    # wasted resource
    def getEntity(self, entity):
        list = [0] * 11
        list[named_entity.index(entity)] = 1
        return list

    #
    def data(self, dict):
        inputSequence = [] # list of word in inputSequence
        outputSequence = [] # list of word in outputSequence
        inputBatch = [] # list of sequence in inputBatch
        outputBatch = [] # list of sequence in outputBatch

        with open(dir1) as f:
            for line in f:
                split = line.rstrip().lstrip().split(" ")
                if split[0] in strong_stop_token:
                    inputSequence.append(dict.get(split[0].lower()))
                    if len(inputSequence) != 0:
                        inputBatch.append(inputSequence)
                        outputBatch.append(outputSequence)
                    inputSequence = []
                    outputSequence = []
                else:
                    if len(split) == 3:
                        inputSequence.append(dict.get(split[0].lower()))
                        outputSequence.append(self.getEntity((split[2])))
                #    if (split[0] not in weak_stop_token) and (len(split) == 3):
                #        inputSequence.append(dict.get(split[0].lower()))
                #        outputSequence.append(self.getEntity((split[2])))

        # each word represented by float type vector
        return inputBatch, outputBatch

    def getData(self, dict):
        inputSequence = [] # list of word in inputSequence
        outputSequence = [] # list of word in outputSequence
        inputBatch = [] # list of sequence in inputBatch
        outputBatch = [] # list of sequence in outputBatch
        count = 0
        with open(dir1) as f:
            for line in f:
                split = line.rstrip().lstrip().split(" ")
                if len(split) == 3:
                    wordVector = dict.get(split[0].lower())
                    if wordVector == None:
                        wordVector = np.random.uniform(-1,1,200)
                    inputSequence.append(wordVector)
                    outputSequence.append(self.getEntity((split[2])))
                    if split[0] in strong_stop_token:
                        inputBatch.append(inputSequence)
                        outputBatch.append(outputSequence)
                        inputSequence = []
                        outputSequence = []
        print(count)
        # each word represented by float type vector
        return inputBatch, outputBatch

    def length(self, input):
        used = tf.sign(tf.reduce_max(tf.abs(input), reduction_indices=2))
        length = tf.reduce_sum(used, reduction_indices=1)
        length = tf.cast(length, tf.int32)
        return length

class NER:
    def __init__(self, data, target, num_hidden = 200, num_layers = 1):
        self.data = data
        self.target = target # batch size * timesteps(input sequence length) * features (word vector length)
        self.num_hidden = num_hidden # bactch size * timesteps * output size (classes size)
        self.num_layers = num_layers
        self.prediction
        self.error
        self.optimize

    def prediction(self):
        output, _ = rnn.dynamic_rnn(
            rnn_cell.BasicLSTMCell(
                self.num_hidden),
            self.data,
            sequence_length=179,
            dtype = tf.float32
        )
        # softmax layer
        max_length = int(self.target.get_shape()[1]) # timesteps
        num_classes = int(self.target.get_shape()[2]) # output size
        # weight [num_hidden, output size] bias [output size]
        weight, bias = self.weight_and_bias(self.num_hidden, num_classes)
        # Flatten to apply same weights to all time steps
        # nhưng nếu tổng số phần tử không chia hết cho số các ẩn số thì sao?
        output = tf.reshape(output, [-1, self.num_hidden])
        prediction = tf.nn.softmax(tf.matmul(output, weight)+bias)
        prediction = tf.reshape(prediction, [-1, max_length, num_classes])
        return prediction

    def cost(self):
        # compute cross entropy for each frame
        cross_entropy = self.target*tf.log(self.prediction())
        # do you understand reduce_s
        cross_entropy = -tf.reduce_sum(cross_entropy, reduction_indices=1)
        return cross_entropy

    def optimize(self):
        learning_rate = 0.03
        optimizer = tf.train.RMSPropOptimizer(learning_rate)
        return optimizer.minimize(self.cost())

    def error(self):
        mistakes = tf.not_equal(
            tf.argmax(self.target, 2), tf.argmax(self.prediction, 2))
        return tf.reduce_mean(tf.cast(mistakes, tf.float32))
    #
    def weight_and_bias(self, in_size, out_size):
        weight = tf.truncated_normal([in_size, out_size], stddev=0.01)
        bias = tf.constant(0.1, shape=[out_size])
        return tf.Variable(weight), tf.Variable(bias)


process = dataset()
dict = process.makeDictFromDataset()
print("kich co tu dien", len(dict))
x, y = process.getData(dict)

# batch size x, y = 22151, 22151
print("do dai cua batch input", len(x))
print("do dai cua batch output", len(y))
# x, y max_length of sequence = 179
print("do dai lon nhat cua moi xau", max(len(z) for z in x))
print("do dai nho nhat cua moi xau", min(len(z) for z in x[:100]))

# padding for input

for string in x[:1000]:
    pad = []
    if len(string) < 179:
        for word in range(179-len(string)):
            pad.append([0]*200)
        string += pad

for string in x[:1000]:
    if len(string) != 179:
        print("la")
    for word in string:
        if len(word) != 200:
            print("la")

print("do dai nho nhat cua moi xau", min(len(z) for z in x[:100]))

convert = x[:1]
for i in convert:
    print(len(i))
    for j in i:
        print(len(j))

va = tf.convert_to_tensor(convert)

"""
data = tf.placeholder(tf.float32, [None, 179, 200])
target = tf.placeholder(tf.float32, [None, 179, 11])

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
#x = tf.Variable(x)
#y = tf.Variable(y)


"""
max_length = 153
frame_size = 200
n_classes = 11
n_hidden = 250

# training input, output
input = tf.placeholder(tf.float32, [None, max_length, frame_size])
output = tf.placeholder(tf.float32, [None, max_length, n_classes])

# Define weights
weights = tf.Variable(tf.random_normal([n_hidden, n_classes]))
biases = tf.Variable(tf.random_normal([n_classes]))

gru_cell = rnn_cell.GRUCell(n_hidden)

output, state = tf.nn.dynamic_rnn(
    gru_cell,
    input,
    dtype=tf.float32
)

output = tf.reshape(output, [-1, n_hidden])
prediction = tf.nn.softmax(tf.matmul(output, weights) + biases)
prediction = tf.reshape(prediction, [-1, max_length, n_classes])

cross_entropy = -tf.reduce_sum(output * tf.log(prediction), reduction_indices=1)
cross_entropy = tf.reduce_mean(cross_entropy)

optimizer = tf.train.RMSPropOptimizer(0.003)
optimizer = optimizer.minimize(cross_entropy)

with tf.Session() as sess:
    for epoch in 10000:
        sess.run(optimizer, {input:x, output:y})
"""
