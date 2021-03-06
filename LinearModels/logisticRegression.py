#!/usr/bin/python
#
# By: Max Sklar
# @maxsklar
# https://github.com/maxsklar

# Copyright 2013 Max Sklar

import math
import logging
import random
import scipy.special as mathExtra
import numpy.random as R

# dataPoints: a list of data points. Each data point is a map from a feature name (a string) to a number
# if a feature doesn't exist in the map, it is assumed to be zero
# labels: same length as dataPoints. Each label is a boolean
# L1: a positive float representing the L1 regression term
# params: the parameters for each feature (a map). The parameters are doubles, and assumed to be zero 
#  if they are not in the map
# convergence: a small number to detect convergence
def batchCompute(dataPoints, labels, L1, convergence, maxIters, allowLogging = True):
  params = {}
  for i in range(0, maxIters):
    (params, maxDist) = batchStep(dataPoints, labels, L1, params)
    if (allowLogging): logging.debug("Iteration " + str(i) + ", Dist: " + str(maxDist))
    if (maxDist < convergence):
      if (allowLogging): logging.debug("Converge criteria met.")
      return params

  if (allowLogging): logging.debug("Convergence did not occur in " + str(maxIters) + " iterations")
  return params

# dataPoints: a list of data points. Each data point is a map from a feature name (a string) to a number
# if a feature doesn't exist in the map, it is assumed to be zero
# labels: same length as dataPoints. Each label is a boolean
# L1: a positive float representing the L1 regression term
# params: the parameters for each feature (a map). The parameters are doubles, and assumed to be zero 
#  if they are not in the map
#
# Returns: (newParams, distance)
# distance: maximum distance between new and old params
def batchStep(dataPoints, labels, L1, params):
  featureDerivs = {}
  feature2ndDerivs = {}

  for dataPoint, label in zip(dataPoints, labels):
    currentEnergy = energy(dataPoint, params)
    expEnergy = math.exp(currentEnergy)
    for feature in dataPoint:
      value = dataPoint[feature]
      d1 = derivativeForFeature(label, value, expEnergy)
      currentFeatureD = featureDerivs.get(feature, 0)
      featureDerivs[feature] = currentFeatureD + d1
      
      d2 = secondDerivativeForFeature(value, expEnergy)
      currentFeatureD2 = feature2ndDerivs.get(feature, 0)
      feature2ndDerivs[feature] = currentFeatureD2 + d2
  
  featuresToLeaveAtZero = set()
  
  maxDistance = 0
  newParams = {}
  for feature in featureDerivs:
    deriv = featureDerivs[feature]
    currentValue = params.get(feature, 0)
    deriv2 = feature2ndDerivs.get(feature, 0)
    if (currentValue > 0):
      diff =  (deriv + L1) / deriv2
      maxDistance = max(abs(diff), maxDistance)
      newValue = currentValue - diff
      if (sameSign(newValue, currentValue)): newParams[feature] = newValue
    if (currentValue < 0):
      diff = (deriv - L1) / deriv2
      maxDistance = max(abs(diff), maxDistance)
      newValue = currentValue - diff
      if (sameSign(newValue, currentValue)): newParams[feature] = newValue
    if (currentValue == 0):
      if (deriv > L1):
        diff = (deriv - L1) / deriv2
        maxDistance = max(abs(diff), maxDistance)
        newParams[feature] = currentValue - diff
      if (deriv < -L1):
        diff = (deriv + L1) / deriv2
        maxDistance = max(abs(diff), maxDistance)
        newParams[feature] = currentValue - diff
  return (newParams, maxDistance)

def sameSign(a, b): return (a > 0) == (b > 0)

def derivativeForFeature(label, featureParam, expEnergy):
  term1 = -1 * labelToInt(label) * featureParam
  term2 = featureParam * expEnergy / (expEnergy + 1)
  return term1 + term2

def secondDerivativeForFeature(featureParam, expEnergy):
  return (featureParam ** 2) * expEnergy / (expEnergy ** 2)

def energy(dataPoint, params):
  total = 0.0
  for feature in dataPoint:
    param = params.get(feature, 0)
    total += dataPoint[feature] * param
  return total

def labelToInt(label):
  if (label): return 1
  return 0

# Parameter Tuning
# Needs logLevel to turn logging off for each run
def findOptimalL1Regulizer(trainingSet, trainingLabels, testSet, testLabels, conv, maxIter):
  logL1 = 0
  currentLoss = float("inf")
  for i in range(0, 40):
    newLogL1 = logL1 + R.normal()
    L1 = math.exp(newLogL1)
    
    params = batchCompute(trainingSet, trainingLabels, L1, conv, maxIter, False)
    avgLoss = computeLossForDataset(testSet, testLabels, params)
    
    accept = avgLoss < currentLoss
    logging.debug("Tried L1: " + str(L1) + ", loss: " + str(avgLoss) + ", accepted? " + str(accept))
    if (accept):
      currentLoss = avgLoss
      logL1 = newLogL1
  return math.exp(logL1)

def computeLossForDataset(dataPoints, labels, params):
  totalLoss = 0
  totalDataPoints = 0
  for dataPoint, label in zip(dataPoints, labels):
    totalLoss += computeLossForDatapoint(dataPoint, label, params)
    totalDataPoints += 1
  return totalLoss / totalDataPoints

def computeLossForDatapoint(dataPoint, label, params):
  E = energy(dataPoint, params)
  expEnergy = math.exp(E)
  if (label): return math.log(expEnergy + 1) - E
  return math.log(expEnergy + 1)