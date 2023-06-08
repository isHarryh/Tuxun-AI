# -*- coding: utf-8 -*-
# Copyright (c) 2023, Harry Huang
# @ BSD 3-Clause License
import torch
import torch.nn as nn
import torchvision.models as models


class TuxunAIModelV0(nn.Module):
    '''The classification model for the game Tuxun, aka Geo Guesser.'''

    def __init__(
            self,
            features:nn.Sequential=None,
            avgpool:nn.AdaptiveAvgPool2d=None,
            classifier:nn.Sequential=None
        ):
        super().__init__()
        model = models.mobilenet_v3_large()
        self.features   = features   if features   else model.features
        self.avgpool    = avgpool    if avgpool    else model.avgpool
        self.classifier = classifier if classifier else model.classifier
    
    def forward(self, x):
        x = self.features(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.classifier(x)
        return x

    @staticmethod
    def get_classifier(num_classes:int):
        '''
        Get the prefab classifier sequential.
        :param num_classes: The number of classes in the output layer.
        :returns: The sequential object.
        '''
        return nn.Sequential(
            nn.Linear(960, 1140),
            nn.Hardswish(),
            nn.Dropout(0.38),
            nn.Linear(1140, num_classes)
        )

    def freeze_features_params(self, freeze:bool=True):
        self._freeze_params(self.features, freeze)

    def freeze_avgpool_params(self, freeze:bool=True):
        self._freeze_params(self.avgpool, freeze)

    def freeze_classifier_params(self, freeze:bool=True):
        self._freeze_params(self.classifier, freeze)

    def _freeze_params(self, module:nn.Module, freeze:bool):
        for p in module.parameters():
            p.requires_grad = bool(freeze)
