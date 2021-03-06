# -*- coding: utf-8 -*-
"""Untitled2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1LKK4Tmh52-oY__WtltEauArvfQAc0trP
"""

from google.colab import drive
drive.mount('/content/drive')

import os
import numpy as np
import nltk
import json
import pandas as pd
import random
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
nltk.download('punkt')

def tokenize():
    sentiment = ['neutral', 'joy', 'sadness', 'fear', 'anger', 'surprise', 'disgust', 'non-neutral']

    sentiment2index = {}
    for voca in sentiment:
        if voca not in sentiment2index.keys():
            sentiment2index[voca] = len(sentiment2index)
    return sentiment2index

def read_dataset(dataset_type):
    max_seq_len = 0
    with open(dataset_type, "r", encoding="utf-8") as file_handler:
        json_2_line = json.load(file_handler)
        labels, sentences = [], []
        for line in json_2_line:
            for i in range(len(line)):
                sentence = line[i]['utterance']
                sentences.append(sentence)

                tok_sentence = nltk.word_tokenize(sentence)
                tok_key = nltk.word_tokenize(line[i]['emotion'])
                labels.append(sentiment2index[tok_key[0]])

                max_seq_len = max(max_seq_len, len(tok_sentence))

    return labels, sentences, max_seq_len

sentiment2index = tokenize()
index2sentiment = {i: e for e, i in sentiment2index.items()}
TRAIN_LABELS, TRAIN_SENTENCES, TRAIN_MAX_SEQ_LEN = read_dataset("/content/drive/My Drive/friends_train.json") #학습데이터 읽기
TEST_LABELS, TEST_SENTENCES, TEST_MAX_SEQ_LEN = read_dataset("/content/drive/My Drive/friends_dev.json") #테스트데이터 읽기
MAX_SEQUENCE_LEN = max(TRAIN_MAX_SEQ_LEN, TEST_MAX_SEQ_LEN) #Train과 Test 전체에서 가장 긴 길이

from keras.utils import to_categorical ##One-Hot-Encoding을 매우 쉽게 해주는 함수

TRAIN_LABELS=to_categorical(TRAIN_LABELS) #One-Hot-Encoding
TEST_LABELS=to_categorical(TEST_LABELS) #One-Hot-Encoding

print("Train : ", len(TRAIN_SENTENCES))
for train_label, train_sent in zip(TRAIN_LABELS, TRAIN_SENTENCES[0:30]):
  print(train_label, ':' ,train_sent)

print("Test : ", len(TEST_SENTENCES))
for test_label, test_sent in zip(TEST_LABELS, TEST_SENTENCES[0:10]):
  print(test_label, ':' ,test_sent)

print("MAX_SEQUENCE_LEN", MAX_SEQUENCE_LEN)

tokenizer = Tokenizer(num_words=None,filters='!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n' , lower=True, char_level=False) #토크나이저 생성
tokenizer.fit_on_texts(TRAIN_SENTENCES) #토큰나이즈 진행
TRAIN_SEQUENCES = tokenizer.texts_to_sequences(TRAIN_SENTENCES)#id로 변경
TEST_SEQUENCES = tokenizer.texts_to_sequences(TEST_SENTENCES)#id로 변경
VOCAB_SIZE = len(tokenizer.word_index) + 1

print(TRAIN_SENTENCES[0])
print(TRAIN_SEQUENCES[0])

X_train = pad_sequences(TRAIN_SEQUENCES, padding='post', maxlen=MAX_SEQUENCE_LEN) #패딩진행
X_test = pad_sequences(TEST_SEQUENCES, padding='post', maxlen=MAX_SEQUENCE_LEN) #패딩진행
print("PAD_SEQUENCES COMPLETES")

def create_embedding_matrix(filepath, word_index, embedding_dim):
    vocab_size = len(word_index) + 1  # Adding again 1 because of reserved 0 index
    embedding_matrix = np.zeros((vocab_size, embedding_dim))

    with open(filepath) as f:
        for line in f:
            word, *vector = line.split()
            if word in word_index:
                idx = word_index[word] 
                embedding_matrix[idx] = np.array(
                    vector, dtype=np.float32)[:embedding_dim]

    return embedding_matrix

EMBEDDING_DIM = 300 #glove 파일 바꾸면 이거 바꿔야
embedding_matrix = create_embedding_matrix(
    '/content/drive/My Drive/glove.6B.300d.txt',
    tokenizer.word_index, EMBEDDING_DIM
    )

import matplotlib.pyplot as plt
plt.style.use('ggplot')

def plot_history(history):
    accu = history.history['accuracy']
    val_acc = history.history['val_accuracy']
    loss = history.history['loss']
    val_loss = history.history['val_loss']
    x = range(1, len(accu) + 1)

    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(x, accu, 'b', label='Training acc')
    plt.plot(x, val_acc, 'r', label='Validation acc')
    plt.title('Training and validation accuracy')
    plt.legend()
    plt.subplot(1, 2, 2)
    plt.plot(x, loss, 'b', label='Training loss')
    plt.plot(x, val_loss, 'r', label='Validation loss')
    plt.title('Training and validation loss')
    plt.legend()

from keras.models import Sequential
from keras import layers
from keras.models import Model
from keras.layers import LeakyReLU
from keras import regularizers
from keras import losses
import tensorflow as tf

seq_input = layers.Input(shape=(MAX_SEQUENCE_LEN,), dtype='int32')

seq_embedded = layers.Embedding(VOCAB_SIZE, 
                           EMBEDDING_DIM, 
                           weights=[embedding_matrix], 
                           input_length=MAX_SEQUENCE_LEN, 
                           trainable=True)(seq_input)

filters = [2,3,4,5]
conv_models = []
for filter in filters:
  conv_feat = layers.Conv1D(filters=128, 
                            kernel_size=filter, 
                            activation='relu',
                            padding='valid'  )(seq_embedded) 
                          
  pooled_feat = layers.GlobalMaxPooling1D()(conv_feat) #MaxPooling
  conv_models.append(pooled_feat)

conv_merged = layers.concatenate(conv_models, axis=1) #filter size가 2,3,4,5인 결과들 Concatenation

model_dropout = layers.Dropout(0.5)(conv_merged)
print((model_dropout.shape))

logits = layers.Dense(8, activation='softmax')(model_dropout)

model = Model(seq_input, logits) #(입력,출력)

model.compile(optimizer='adam',
              loss = losses.CategoricalCrossentropy(),
              metrics=['accuracy'])
model.summary()

#학습 시작
history = model.fit(X_train, TRAIN_LABELS,
                    epochs=50,
                    verbose=True,
                    validation_data=(X_test, TEST_LABELS),
                    batch_size=512)
print(history.history['loss'])
print(history.history['accuracy'])

from keras.models import load_model
model.save('KU_NLP') #모델 저장하기
from google.colab import files


# 결과 시각화
plot_history(history)

from keras.models import load_model
model2 = load_model('KU_NLP') #모델 로딩하기 

from keras.utils.vis_utils import plot_model
plot_model(model2, to_file='model_plot.png', show_shapes=True, show_layer_names=True)

TEST_LABELS, TEST_SENTENCES, TEST_MAX_SEQ_LEN = read_dataset("/content/drive/My Drive/friends_test.json") #테스트데이터 읽기
TEST_LABELS=to_categorical(TEST_LABELS) #One-Hot-Encoding

print("Train : ", len(TEST_SENTENCES))
for train_label, train_sent in zip(TEST_LABELS, TEST_SENTENCES[0:30]):
  print(train_label, ':' ,train_sent)

tokenizer.fit_on_texts(TEST_SENTENCES) #토큰나이즈 진행
TEST_SEQUENCES = tokenizer.texts_to_sequences(TEST_SENTENCES)#id로 변경

X_test = pad_sequences(TEST_SEQUENCES, padding='post', maxlen=MAX_SEQUENCE_LEN) #패딩진행

test_loss,test_acc=model.evaluate(X_test,TEST_LABELS)
print("Test_acc: ",test_acc)

