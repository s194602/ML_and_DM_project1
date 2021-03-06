import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.pyplot import (figure, plot, title, xlabel, ylabel, show,
                               legend, subplot, xticks, yticks, boxplot, hist,
                               ylim)
from matplotlib.pylab import (figure, semilogx, loglog, xlabel, ylabel, legend, 
                           title, subplot, show, grid)
from sklearn import model_selection
from toolbox_02450 import rlr_validate
import torch
from toolbox_02450 import train_neural_net, draw_neural_net
from scipy import stats
import scipy.stats as st

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


############ Regression ##################
###### Part A
Ysbp = Xall[:,0] #Sbp
Xreg = Xall[:,1:10]
Xdt = Xall[:,1:10]

# Normalize data for ANN
Xdt = stats.zscore(Xdt)


# Add offset attribute
Xreg = np.concatenate((np.ones((Xreg.shape[0],1)),Xreg),1)
attributeNamesNoOff = attributeNames
attributeNames = [u'Offset']+attributeNames #Why does this add Offset to all atributes?
M = M+1


## Crossvalidation
# Create crossvalidation partition for evaluation
K = 5
CV = model_selection.KFold(K, shuffle=True,random_state=42069)

# Values of lambda
lambdas = np.array([0.01,0.50,1.00,15.00,20.00,50.00,100.00,140.00,150.00,160.00,200.00,300.00,400.00,500.00])
#lambdas = np.logspace(-2, 8, 10)

# Initialize variables
#T = len(lambdas)
Error_train = np.empty((K,1))
Error_test = np.empty((K,1))
Error_train_rlr = np.empty((K,1))
Error_test_rlr = np.empty((K,1))
Error_train_nofeatures = np.empty((K,1))
Error_test_nofeatures = np.empty((K,1))
w_rlr = np.empty((M,K))
mu = np.empty((K, M-1))
sigma = np.empty((K, M-1))
w_noreg = np.empty((M,K))
all_lamdas = np.empty((K))

Z_lr = []
Z_base = []
zann = []


yhat_lr = []
yhat_lr_base = []
yhat_ANN = []


### part A using algo 5
opt_val_err, opt_lambda, mean_w_vs_lambda, train_err_vs_lambda, test_err_vs_lambda = rlr_validate(Xreg, Ysbp, lambdas, 10)
figure(1, figsize=(17,8))
subplot(1,2,1)
semilogx(lambdas,mean_w_vs_lambda.T[:,1:],'.-') # Don't plot the bias term
xlabel('Regularization factor')
ylabel('Mean Coefficient Values')
grid()
# You can choose to display the legend, but it's omitted for a cleaner 
# plot, since there are many attributes
#legend(attributeNames[1:], loc='best')
subplot(1,2,2)
title('Optimal lambda: {0}'.format((opt_lambda)))
loglog(lambdas,train_err_vs_lambda.T,'b.-',lambdas,test_err_vs_lambda.T,'r.-')
xlabel('Regularization factor')
ylabel('Squared error (crossvalidation)')
legend(['Train error','test error'])
grid()


Xty = Xreg.T @ Ysbp
XtX = Xreg.T @ Xreg

# Estimate weights for the optimal value of lambda, on entire training set
lambdaI = opt_lambda * np.eye(M)
lambdaI[0,0] = 0 # Do no regularize the bias term
md_lr_algo5 = np.linalg.solve(XtX+lambdaI,Xty).squeeze()




k=0
for train_index_lr, test_index_lr in CV.split(Xreg,Ysbp):
    
    # extract training and test set for current CV fold
    X_train_lr = Xreg[train_index_lr]
    y_train_lr = Ysbp[train_index_lr]
    X_test_lr = Xreg[test_index_lr]
    y_test_lr = Ysbp[test_index_lr]
    internal_cross_validation = 5    
    
    opt_val_err, opt_lambda, mean_w_vs_lambda, train_err_vs_lambda, test_err_vs_lambda = rlr_validate(X_train_lr, y_train_lr, lambdas, internal_cross_validation)
    
    all_lamdas[k] = opt_lambda
    
    # Standardize outer fold based on training set, and save the mean and standard
    # deviations since they're part of the model (they would be needed for
    # making new predictions) - for brevity we won't always store these in the scripts
    mu[k, :] = np.mean(X_train_lr[:, 1:], 0)
    sigma[k, :] = np.std(X_train_lr[:, 1:], 0)
    
    X_train_lr[:, 1:] = (X_train_lr[:, 1:] - mu[k, :] ) / sigma[k, :] 
    X_test_lr[:, 1:] = (X_test_lr[:, 1:] - mu[k, :] ) / sigma[k, :] 
    
    Xty = X_train_lr.T @ y_train_lr
    XtX = X_train_lr.T @ X_train_lr
    
    # Compute mean squared error without using the input data at all
    Error_train_nofeatures[k] = np.square(y_train_lr-y_train_lr.mean()).sum(axis=0)/y_train_lr.shape[0]
    Error_test_nofeatures[k] = np.square(y_test_lr-y_test_lr.mean()).sum(axis=0)/y_test_lr.shape[0]

    # Estimate weights for the optimal value of lambda, on entire training set
    lambdaI = opt_lambda * np.eye(M)
    lambdaI[0,0] = 0 # Do no regularize the bias term
    w_rlr[:,k] = np.linalg.solve(XtX+lambdaI,Xty).squeeze()
    # Compute mean squared error with regularization with optimal lambda
    Error_train_rlr[k] = np.square(y_train_lr-X_train_lr @ w_rlr[:,k]).sum(axis=0)/y_train_lr.shape[0]
    Error_test_rlr[k] = np.square(y_test_lr-X_test_lr @ w_rlr[:,k]).sum(axis=0)/y_test_lr.shape[0]
    
    Z_lr.append(np.abs(y_test_lr - (X_test_lr @ w_rlr[:,k]) ) ** 2)
    
    # Estimate weights for unregularized linear regression, on entire training set
    w_noreg[:,k] = np.linalg.solve(XtX,Xty).squeeze()
    
    Z_base.append(np.abs(y_test_lr - (X_test_lr @ w_noreg[:,k]) ) ** 2)
    
    # Compute mean squared error without regularization
    Error_train[k] = np.square(y_train_lr-X_train_lr @ w_noreg[:,k]).sum(axis=0)/y_train_lr.shape[0]
    Error_test[k] = np.square(y_test_lr-X_test_lr @ w_noreg[:,k]).sum(axis=0)/y_test_lr.shape[0]
    # OR ALTERNATIVELY: you can use sklearn.linear_model module for linear regression:
    #m = lm.LinearRegression().fit(X_train_lr, y_train_lr)
    #Error_train[k] = np.square(y_train_lr-m.predict(X_train_lr)).sum()/y_train_lr.shape[0]
    #Error_test[k] = np.square(y_test_lr-m.predict(X_test_lr)).sum()/y_test_lr.shape[0]

    # Display the results for the last cross-validation fold
    if k == K-1:
        figure(k, figsize=(17,8))
        subplot(1,2,1)
        semilogx(lambdas,mean_w_vs_lambda.T[:,1:],'.-') # Don't plot the bias term
        xlabel('Regularization factor')
        ylabel('Mean Coefficient Values')
        grid()
        # You can choose to display the legend, but it's omitted for a cleaner 
        # plot, since there are many attributes
        #legend(attributeNames[1:], loc='best')
        
        subplot(1,2,2)
        title('Optimal lambda: {0}'.format((opt_lambda)))
        loglog(lambdas,train_err_vs_lambda.T,'b.-',lambdas,test_err_vs_lambda.T,'r.-')
        xlabel('Regularization factor')
        ylabel('Squared error (crossvalidation)')
        legend(['Train error','Validation error'])
        grid()
    
    # To inspect the used indices, use these print statements
    #print('Cross validation fold {0}/{1}:'.format(k+1,K))
    #print('Train indices: {0}'.format(train_index_lr))
    #print('Test indices: {0}\n'.format(test_index_lr))

    k+=1

show()
# Display results
print('Linear regression without feature selection:')
print('- Training error: {0}'.format(Error_train.mean()))
print('- Test error:     {0}'.format(Error_test.mean()))
print('- R^2 train:     {0}'.format((Error_train_nofeatures.sum()-Error_train.sum())/Error_train_nofeatures.sum()))
print('- R^2 test:     {0}\n'.format((Error_test_nofeatures.sum()-Error_test.sum())/Error_test_nofeatures.sum()))
print('Regularized linear regression:')
print('- Training error: {0}'.format(Error_train_rlr.mean()))
print('- Test error:     {0}'.format(Error_test_rlr.mean()))
print('- R^2 train:     {0}'.format((Error_train_nofeatures.sum()-Error_train_rlr.sum())/Error_train_nofeatures.sum()))
print('- R^2 test:     {0}\n'.format((Error_test_nofeatures.sum()-Error_test_rlr.sum())/Error_test_nofeatures.sum()))


### ANN
Ysbp = Ysbp.reshape(462,1)

n_hidden_units_all = [1,2,3,4,5,7,9,12,16]
n_replicates = 1          # number of networks trained in each k-fold
max_iter = 50000


# K-fold crossvalidation
K_internal = K


# Setup figure for display of learning curves and error rates in fold
summaries, summaries_axes = plt.subplots(1,2, figsize=(10,5))
# Make a list for storing assigned color of learning curve for up to K=10
color_list = ['tab:orange', 'tab:green', 'tab:purple', 'tab:brown', 'tab:pink',
              'tab:gray', 'tab:olive', 'tab:cyan', 'tab:red', 'tab:blue']
loss_fn = torch.nn.MSELoss() # notice how this is now a mean-squared-error loss
# Define the model
allmodels = []
numberOfHiddenUnits = []

CV = model_selection.KFold(K, shuffle=True)

errors = [] # make a list for storing generalizaition error in each loop
k=0
for (k, (train_index, test_index)) in enumerate(CV.split(Xdt,Ysbp)): 
    print('\nCrossvalidation fold: {0}/{1}'.format(k+1,K))    
    
    # Extract training and test set for current CV fold, convert to tensors
    X_train = torch.Tensor(Xdt[train_index,:])
    y_train = torch.Tensor(Ysbp[train_index])
    X_test = torch.Tensor(Xdt[test_index,:])
    y_test = torch.Tensor(Ysbp[test_index])
    
    
    Internalerrors = np.empty((len(n_hidden_units_all),K_internal))
    
    Egen = np.empty((len(n_hidden_units_all)))
    
    ##### internal cross validation #########
    # Should this be a new CV fold?
    for (k2, (train_index_internal, test_index_internal)) in enumerate(CV.split(X_train,y_train)):
        
        X_train_internal = torch.Tensor(Xdt[train_index_internal,:])
        y_train_internal = torch.Tensor(Ysbp[train_index_internal])
        X_test_internal = torch.Tensor(Xdt[test_index_internal,:])
        y_test_internal = torch.Tensor(Ysbp[test_index_internal])
        
        Internalmodel = []
        count = 0
        for h in n_hidden_units_all: 
            model = lambda: torch.nn.Sequential(
                        torch.nn.Linear(M-1, h), #M features to n_hidden_units
                        torch.nn.Tanh(),   # 1st transfer function,
                        torch.nn.Linear(h, 1), # n_hidden_units to 1 output neuron
                        # no final tranfer function, i.e. "linear output"
                        )
            print('Training model of type:\n\n{}\n'.format(str(model())))
        
        
            # Train the net on training data
            net, final_loss, learning_curve = train_neural_net(model,
                                                       loss_fn,
                                                       X=X_train_internal,
                                                       y=y_train_internal,
                                                       n_replicates=n_replicates,
                                                       max_iter=max_iter)
    
            print('\n\tBest loss: {}\n'.format(final_loss))
        
            # Determine estimated class labels for test set
            y_test_est_internal = net(X_test_internal)
        
            # Determine mean squared errors
            se = (y_test_est_internal.float()-y_test_internal.float())**2 # squared error
            mse = (sum(se).type(torch.float)/len(y_test_internal)).data.numpy() #mean
        
            Internalerrors[count][k2] = (mse)
            Internalmodel.append(model)
        
            count += 1
    
    count = 0
    for errorsmdl in Internalerrors:
        Egen[count] = (sum(errorsmdl))*(len(test_index_internal)/len(train_index))
        count += 1
        
    minIndex = np.argmin(Egen)
    
    hidden_units_from_innerfold = n_hidden_units_all[minIndex]
    
    model = lambda: torch.nn.Sequential(
                        torch.nn.Linear(M-1, hidden_units_from_innerfold), #M features to n_hidden_units
                        torch.nn.Tanh(),   # 1st transfer function,
                        torch.nn.Linear(hidden_units_from_innerfold, 1), # n_hidden_units to 1 output neuron
                        # no final tranfer function, i.e. "linear output"
                        )
    
    allmodels.append(Internalmodel[minIndex])
    
    net_outer, final_loss, learning_curve = train_neural_net(model,
                                                       loss_fn,
                                                       X=X_train,
                                                       y=y_train,
                                                       n_replicates=n_replicates,
                                                       max_iter=max_iter)
    
    
    y_test_est = net_outer(X_test)
    
    zann.append(np.abs(y_test.detach().numpy() - y_test_est.detach().numpy()) ** 2)
    
    # Determine errors and errors
    se = (y_test_est.float()-y_test.float())**2 # squared error
    mse = (sum(se).type(torch.float)/len(y_test)).data.numpy() #mean
    
    errors.append((mse)) # store error rate for current CV fold     

    numberOfHiddenUnits.append(hidden_units_from_innerfold)
    
    
    # Display the learning curve for the best net in the current fold
    h, = summaries_axes[0].plot(learning_curve, color=color_list[k])
    h.set_label('CV fold {0}'.format(k+1))
    summaries_axes[0].set_xlabel('Iterations')
    summaries_axes[0].set_xlim((0, max_iter))
    summaries_axes[0].set_ylabel('Loss')
    summaries_axes[0].set_title('Learning curves')

# Display the MSE across folds
summaries_axes[1].bar(np.arange(1, K+1), np.squeeze(np.asarray(errors)), color=color_list)
summaries_axes[1].set_xlabel('Fold')
summaries_axes[1].set_xticks(np.arange(1, K+1))
summaries_axes[1].set_ylabel('MSE')
summaries_axes[1].set_title('Test mean-squared-error')
    
print('Diagram of best neural net in last fold:')
weights = [net_outer[i].weight.data.numpy().T for i in [0,2]]
biases = [net_outer[i].bias.data.numpy() for i in [0,2]]
tf =  [str(net_outer[i]) for i in [1,2]]

attributeNames2 = [name[:] for name in attributeNamesNoOff[1:10]]

draw_neural_net(weights, biases, tf, attribute_names=attributeNames2)

# Print the average classification error rate
print('\nEstimated generalization error, RMSE: {0}'.format(round(np.sqrt(np.mean(errors)), 4)))

# When dealing with regression outputs, a simple way of looking at the quality
# of predictions visually is by plotting the estimated value as a function of 
# the true/known value - these values should all be along a straight line "y=x", 
# and if the points are above the line, the model overestimates, whereas if the
# points are below the y=x line, then the model underestimates the value
plt.figure(figsize=(10,10))
y_est = y_test_est.data.numpy().reshape(92,1); y_true = y_test.data.numpy()
axis_range = [np.min([y_est, y_true])-1,np.max([y_est, y_true])+1]
plt.plot(axis_range,axis_range,'k--')
plt.plot(y_true, y_est,'ob',alpha=.25)
plt.legend(['Perfect estimation','Model estimations'])
plt.title('SBP: estimated versus true value (for last CV-fold)')
plt.ylim(axis_range); plt.xlim(axis_range)
plt.xlabel('True value')
plt.ylabel('Estimated value')
plt.grid()

plt.show()


### Make CI and p
alpha = 0.05

#Z_lr_base = Z_lr[np.argmin(Error_test_rlr)] - Z_base[np.argmin(Error_test)]
Z_lr_base = np.concatenate(Z_lr) - np.concatenate(Z_base)
CI_lr_base = st.t.interval(1-alpha, len(Z_lr_base)-1, loc=np.mean(Z_lr_base), scale=st.sem(Z_lr_base))  # Confidence interval
p_lr_base = st.t.cdf( -np.abs( np.mean(Z_lr_base) )/st.sem(Z_lr_base), df=len(Z_lr_base)-1)  # p-value

#Z_lr_ANN = Z_lr[np.argmin(Error_test_rlr)] - Z_ANN[np.argmin(errors)]
Z_lr_ANN = np.concatenate(Z_lr) - np.concatenate(zann).reshape(462,)
CI_lr_ANN = st.t.interval(1-alpha, len(Z_lr_ANN)-1, loc=np.mean(Z_lr_ANN), scale=st.sem(Z_lr_ANN))  # Confidence interval
p_lr_ANN = st.t.cdf( -np.abs( np.mean(Z_lr_ANN) )/st.sem(Z_lr_ANN), df=len(Z_lr_ANN)-1)  # p-value

#Z_base_ANN = Z_base[np.argmin(Error_test)] - Z_ANN[np.argmin(errors)]
Z_base_ANN = np.concatenate(Z_base) - np.concatenate(zann).reshape(462,)
CI_base_ANN = st.t.interval(1-alpha, len(Z_base_ANN)-1, loc=np.mean(Z_base_ANN), scale=st.sem(Z_base_ANN))  # Confidence interval
p_base_ANN = st.t.cdf( -np.abs( np.mean(Z_base_ANN) )/st.sem(Z_base_ANN), df=len(Z_base_ANN)-1)  # p-value


















