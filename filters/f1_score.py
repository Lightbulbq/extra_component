def Precision(TP,FP):
    if (TP + FP) == 0:
        return 0
    else:
        return (TP/(TP + FP))

def Recall(TP,FN):
    if (TP + FN) == 0:
        return 0
    else:
        return (TP/(TP+FN))

def F1_score(precision,recall):
    if (precision + recall) == 0:
        return 0
    else:
        return 2*((precision * recall)/(precision + recall))

def Accuracy(TP,TN,FP,FN):
    if (TP + TN + FP + FN) == 0:
        return 0 
    else:
        return (TP+TN)/ (TP + TN + FP + FN)