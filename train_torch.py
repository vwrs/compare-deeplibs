# -*- coding: utf-8 -*-
import os
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-b', '--batch-size', type=int, default=128, metavar='N',
                    help='input batch size for training (default: 128)')
parser.add_argument('-e', '--epochs', type=int, default=20, metavar='E',
                    help='# of epochs to train (default: 20)')
parser.add_argument('-g', '--gpu', type=str, default='0', metavar='GPU',
                    help='set CUDA_VISIBLE_DEVICES (default: 0)')

opt = parser.parse_args()

os.environ["CUDA_VISIBLE_DEVICES"] = opt.gpu


import sys
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import transforms
from torchvision.datasets import CIFAR10
from torch.utils.data import DataLoader
from torch.autograd import Variable
from utils import show_progress

class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 64, 5, 1, 2),
            nn.BatchNorm2d(64),
            nn.ReLU(True),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(64, 128, 5, 1, 2),
            nn.BatchNorm2d(128),
            nn.ReLU(True),
            nn.MaxPool2d(2, 2)
        )
        self.classifier = nn.Sequential(
            nn.Linear(128*8*8, 10)
        )

    def forward(self, x):
        x = self.features(x)
        x = x.view(-1, 128*8*8)
        x = self.classifier(x)
        return x

def load_CIFAR10():
    transform = transforms.Compose(
        [transforms.ToTensor(),
         transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])

    trainset = CIFAR10(root='./CIFAR10', train=True,
                                            download=True, transform=transform)
    trainloader = DataLoader(trainset, batch_size=opt.batch_size,
                                              shuffle=True, num_workers=1, pin_memory=True)
    testset = CIFAR10(root='./CIFAR10', train=False,
                                           download=True, transform=transform)
    testloader = DataLoader(testset, batch_size=opt.batch_size,
                                         shuffle=False, num_workers=1, pin_memory=True)
    return (trainloader, testloader)

def train():
    # load dataset
    # ==========================
    trainloader, _ = load_CIFAR10()
    N = len(trainloader)
    print('# of trainset: ', N)

    cnn = CNN()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(cnn.parameters())
    cnn.cuda()
    criterion.cuda()

    # train
    # ==========================
    loss_history = []
    acc_history = []
    time_history = []
    for epoch in range(opt.epochs):
        loss_cum = 0.0
        acc_cum = 0.0
        time_cum = 0.0
        for i, (imgs, labels) in enumerate(trainloader):
            imgs, labels = Variable(imgs.cuda()), Variable(labels.cuda())
            cnn.zero_grad()

            start = time.time()
            outputs = cnn(imgs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            time_cum += time.time() - start

            loss_cum += loss.data[0]
            # calc accuracy
            _, pred= torch.max(outputs.data, 1)
            total = labels.size(0)
            correct = (pred == labels.data).sum()
            acc_cum += correct/total
            show_progress(epoch+1, i+1, N, loss.data[0], correct/total)

        print('\t mean acc: %f' % (acc_cum/N))
        loss_history.append(loss_cum/N)
        acc_history.append(acc_cum/N)
        time_history.append(time_cum)

    # save histories
    # with open('./loss_pytorch.csv', 'w') as f:
    #     f.write('pytorch')
    #     for l in loss_history:
    #         f.write(',' + str(l))
    #     f.write('\n')
    # print('saved loss history')
    # with open('./acc_pytorch.csv', 'w') as f:
    #     f.write('pytorch')
    #     for l in acc_history:
    #         f.write(',' + str(l))
    #     f.write('\n')
    # print('saved acc history')
    with open('./lap_record.csv', 'a') as f:
        f.write('pytorch')
        for t in time_history:
            f.write(',' + str(t))
        f.write('\n')

if __name__ == '__main__':
    train()
