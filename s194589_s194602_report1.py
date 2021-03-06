# -*- coding: utf-8 -*-
"""
Created on Fri Sep 4 09:47:25 2020

@author: Thor Eric Dueholm (s194589) and Christian Emil Tchernokojev Houmann (s194602)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.linalg import svd
from matplotlib.pyplot import (figure, plot, title, xlabel, ylabel, show,
                               legend, subplot, xticks, yticks, boxplot, hist,
                               ylim)

# read the data into python
df = pd.read_csv("http://www-stat.stanford.edu/~tibs/ElemStatLearn/datasets/SAheart.data",
	encoding='utf-8')

raw_data = df._get_values[:]


cols = range(1, 10)
X = raw_data[:, cols]
y = raw_data[:, 10]

famHistLable = raw_data[:,5] # -1 takes the last column

famHistNames = np.unique(famHistLable)

famHistDict = dict(zip(famHistNames,range(len(famHistNames))))

Xr = X.copy();
Xr[:,4] = np.array([famHistDict[cl] for cl in famHistLable])

attributeNames = np.asarray(df.columns[range(1, 11)])
## a short version of attributenames:
attributeNamesShort = [None] * 10
for i in range(len(attributeNames)):
    attributeNamesShort[i] = (attributeNames[i])[:3]
    
N, M = X.shape

# make array of all atributes
Xall = np.zeros((N,M+1))
Xall[:,0:M] = Xr
Xall[:,M] = y



# boxplots:
figure()
title('Boxplot of attributes')
boxplot(Xall)
xticks(range(1,M+2), attributeNames, rotation=45)

# histogram
figure(figsize=(14,9))
u = np.floor(np.sqrt(M)); v = np.ceil(float(M)/u)
for i in range(M):
    subplot(u,v,i+1)
    hist(X[:,i])
    xlabel(attributeNames[i])
    ylim(0, N) # Make the y-axes equal for improved readability
    if i%v!=0: yticks([])
    if i==0: title('Histogram of attributes')


# We plot scatterplots of all the attributes
# except Famhist (4) and CHD as these are binary
Attributes = [1,2,3,5,6,7,8]
NumAtr = len(Attributes)

figure(figsize=(12,12))
for m1 in range(NumAtr):
    for m2 in range(NumAtr):
        subplot(NumAtr, NumAtr, m1*NumAtr + m2 + 1)
        for c in range(2):
            class_mask = (y==c)
            plot(X[class_mask,Attributes[m2]], X[class_mask,Attributes[m1]], '.')
            if m1==NumAtr-1:
                xlabel(attributeNames[Attributes[m2]])
            else:
                xticks([])
            if m2==0:
                ylabel(attributeNames[Attributes[m1]])
            else:
                yticks([])
            #ylim(0,X.max()*1.1)
            #xlim(0,X.max()*1.1)
legend(["Negative","Positive"])
show()

#Compute correlation matrix
dfXr = pd.DataFrame(Xr.astype(float),columns=attributeNamesShort[:-1])
corrMatrixXr = dfXr.corr()

# We futher look at the following attributes
i = 3
j = 6
figure()
plt.title('correlation between adiposity and BMI')
for c in range(2):
    class_mask = y==c
    plot(Xr[class_mask,i], Xr[class_mask,j], 'o')
legend(["Negative","Positive"])
plt.xlabel(attributeNames[i]);
plt.ylabel(attributeNames[j]);
show()

##TODO plot for some ages too:
fig = plt.figure()
fig.subplots_adjust(hspace=0.4, wspace=0.5)
i2 = 8
Attributes = [1,2,3,5,6,7]
for i in Attributes:
    ax = fig.add_subplot(2, 3, Attributes.index(i)+1)
    for c in range(2):
        class_mask = y==c
        plot(Xr[class_mask,i2], Xr[class_mask,i], '.')
    plt.xlabel(attributeNames[i2]);
    plt.ylabel(attributeNames[i]);
show()


### Basic summary statistics
BasicXall = np.empty((5,M+2),dtype=object)
BasicXall[:,0] = ["","Mean","Median","Range","sd"]
BasicXall[0,1:] = attributeNames
BasicXall[1,1:] = Xall.mean(axis=0)
for index in range(M+1):
    BasicXall[2,index+1] = np.median(Xall[:,index])
    BasicXall[3,index+1] = Xall[:,index].max()-Xall[:,index].min()
    BasicXall[4,index+1] = Xall[:,index].std(ddof=1)
    
    # Uncomment this to see min and max values:
    # print('Min: {1}  ,  Max: {0}', Xall[:,index].max(), Xall[:,index].min() )



#Make standadized values of Xr (subtract mean and devide by standard deviation)
Y = (Xr - np.ones((N,1))*Xr.mean(axis=0))
Y = np.array(Y,dtype=float)
Y = Y*(1/np.std(Y,0))

Yall = (Xall - np.ones((N,1))*Xall.mean(axis=0))
Yall = np.array(Yall,dtype=float)
Yall = Yall*(1/np.std(Yall,0))


figure()
title('Boxplot of standardized attributes')
boxplot(Yall)
xticks(range(1,M+2), attributeNames, rotation=45)


### PCA analysis

# PCA by computing SVD of Y
U,S,Vh = svd(Y,full_matrices=False)

# Compute variance explained by principal components
rho = (S*S) / (S*S).sum()

threshold = 0.9

plt.figure()
plt.plot(range(1,len(rho)+1),rho,'x-')
plt.plot(range(1,len(rho)+1),np.cumsum(rho),'o-')
plt.plot([1,len(rho)],[threshold, threshold],'k--')
plt.title('Variance explained by principal components (standardized)');
plt.xlabel('Principal component');
plt.ylabel('Variance explained');
plt.legend(['Individual','Cumulative','Threshold'])
plt.grid()
plt.show()


#### plot PC with the data
V = Vh.T

Z = Y @ V

# Plot the data projected on the first two principal components
i = 0
j = 1

f = figure()
title('Heart disease data: PCA')
for c in range(2):
    class_mask = y==c
    plot(Z[class_mask,i], Z[class_mask,j], 'o', alpha=.5)
legend(["Negative","Positive"])
xlabel('PC{0}'.format(i+1))
ylabel('PC{0}'.format(j+1))
show()


# Plot the first three principal components coefficients
pcs = [0,1,2]
legendStrs = ['PC'+str(e+1) for e in pcs]
c = ['r','g','b']
bw = .2
r = np.arange(1,M+1)
for i in pcs:    
    plt.bar(r+i*bw, V[:,i], width=bw)
plt.xticks(r+bw, attributeNamesShort)
plt.xlabel('Attributes')
plt.ylabel('Component coefficients')
plt.legend(legendStrs)
plt.grid()
plt.title('PCA components coefficients (standardized)')
plt.show()




