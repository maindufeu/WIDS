# -*- coding: utf-8 -*-
"""Lgbm_Dathaton

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1uR9soy958we2Azo0HxBXe7saXh6lumgT
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import RepeatedKFold
from sklearn.model_selection import KFold
import lightgbm as lgb
import numpy as np
from sklearn.metrics import mean_squared_error

#lectura de archivos
df_train = pd.read_csv('new_train.csv')
df_test = pd.read_csv('new_test.csv') 

#separar caracteristicas categoricas de numericas
categorical_features = ['State_Factor', 'building_class', 'facility_type']
numerical_features = df_train.select_dtypes('number').columns

#separacion de la variable target
target = df_train["site_eui"]
train = df_train.drop(["site_eui","id"],axis =1)
test = df_test.drop(["id"],axis =1)

import pandas as pd
from sklearn import preprocessing
import numpy as np
import lightgbm as lgb
import gc
from sklearn.model_selection import StratifiedKFold
from sklearn.model_selection import KFold
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_error
from bayes_opt import BayesianOptimization
from skopt  import BayesSearchCV



df_train=pd.read_csv('train.csv')

df_test=pd.read_csv('test.csv')

#df_train = df_train.drop('Unnamed: 0',axis=1)

no_usar=['site_eui','id','Year_Factor','direction_max_wind_speed','direction_peak_wind_speed','max_wind_speed' ,'days_with_fog'  ,'id' ]

target='site_eui'

categorical=['Year_Factor','State_Factor','building_class','facility_type']

features=[x for x in df_train.columns if x not in no_usar]

y=df_train[target]
X=df_train.drop(columns=no_usar,axis=1)

df_train = df_train.dropna()

pip install bayesian-optimization

pip install scikit-optimize

le = LabelEncoder()
X['State_Factor']= le.fit_transform(X['State_Factor']).astype("uint8")
X['building_class']= le.fit_transform(X['building_class']).astype("uint8")
X['facility_type']= le.fit_transform(X['facility_type']).astype("uint8")

def bayes_parameter_opt_lgb(X, y, init_round=15, opt_round=25, n_folds=5, random_seed=0, n_estimators=10000, learning_rate=0.05, output_process=False):
    # prepare data
    train_data = lgb.Dataset(data=X, label=y, categorical_feature = list(X.columns),free_raw_data=False)
    # parameters

    def lgb_eval(num_leaves, feature_fraction, max_depth , min_split_gain, min_child_weight,max_bin,bagging_freq,bagging_fraction,min_child_samples,min_data_per_group,scale_pos_weight,lambda_l1,lambda_l2):
        params = {
            "objective" : "regression",
            "boosting": "gbdt","lambda_l1":5,
            "lambda_l2":5,
            "learning_rate" : 0.08, "verbosity": -1, "metric" : 'rmse'
        }
        params['feature_fraction'] = max(min(feature_fraction, 1), 0)
        params['max_depth'] = int(round(max_depth))
        params['max_bin'] = int(round(max_bin))
        params['num_leaves'] = int(round(num_leaves))
        params['bagging_fraction'] = max(min(bagging_fraction, 1), 0)
        params['bagging_freq'] = int(round(bagging_freq))
        params['min_child_samples'] = int(round(min_child_samples))
        params['scale_pos_weight'] = int(round(scale_pos_weight))
        params['min_data_per_group'] = int(round(min_data_per_group))
        params['lambda_l1'] = int(round(lambda_l1))
        params['lambda_l2'] = int(round(lambda_l2))
        params['min_split_gain'] = min_split_gain
        params['min_child_weight'] = min_child_weight
        cv_result = lgb.cv(params, train_data, nfold=n_folds, seed=random_seed, verbose_eval =200,stratified=False)
        return (-1.0 * np.array(cv_result['rmse-mean'])).max()
    
        # range 
    lgbBO = BayesianOptimization(lgb_eval, {'feature_fraction': (0.7, 0.9),
                                            'max_depth': (15, 50),
                                            'max_bin':(4300,6500),
                                            'num_leaves' : (100,400),
                                            "bagging_freq":(4,9),
                                            'bagging_fraction': (0.7,.9),
                                            "lambda_l1":(0,10),
                                            "lambda_l2":(0,13),
                                            'min_split_gain': (0.001, 0.01),
                                             "min_child_samples": (150,300),
                                            "scale_pos_weight":(100,350),
                                            'min_data_per_group':(300,600),
                                            'min_child_weight': (50, 150)}, random_state=0)
        # optimize
    lgbBO.maximize(init_points=init_round, n_iter=opt_round,acq='ei')

        # output optimization process
    if output_process==True: lgbBO.points_to_csv("bayes_opt_result.csv")

        # return best parameters
    model_auc=[]
    for model in range(len( lgbBO.res)):
        model_auc.append(lgbBO.res[model]['target'])
    
    # return best parameters
    return lgbBO.res[pd.Series(model_auc).idxmax()]['target'],lgbBO.res[pd.Series(model_auc).idxmax()]['params']

opt_params = bayes_parameter_opt_lgb(X, y, init_round=15, opt_round=30, n_folds=6, random_seed=0, n_estimators=1000)

opt_params

def entrena_lgb(data,test,features,categorical,target):

    kfold=GroupKFold(n_splits=6)


    i=1
    model = []
    r=[]
    
    pred_test=np.zeros(len(test))

    importancias=pd.DataFrame()

    importancias['variable']=features
    
    
    cat_ind=[features.index(x) for x in categorical if x in features]
    
    dict_cat={}
    
    categorical_numerical = data[categorical].dropna().select_dtypes(include=np.number).columns.tolist()
    
    categorical_transform=[x for x in categorical if x not in categorical_numerical]
    
    for l in categorical_transform:
        le = preprocessing.LabelEncoder()
        le.fit(list(data[l].dropna())+list(test[l].dropna()))

        dict_cat[l]=le

        data.loc[~data[l].isnull(),l]=le.transform(data.loc[~data[l].isnull(),l])
        test.loc[~test[l].isnull(),l]=le.transform(test.loc[~test[l].isnull(),l])
        
        

    for train_index,test_index in kfold.split(data,data[target],data['Year_Factor']):

        lgb_data_train = lgb.Dataset(data.loc[train_index,features].values,data.loc[train_index,target].values)
        lgb_data_eval = lgb.Dataset(data.loc[test_index,features].values,data.loc[test_index,target].values, reference=lgb_data_train)


        params = {
        #     'task': 'train',
        #     'boosting_type': 'gbdt',
        #     'objective': 'regression',
        #     'metric': { 'rmse'},
        #     'num_iterations':5000,
        #     'max_bin':5395,
        #     "max_depth":12,
        #     "num_leaves":52,
        #     'learning_rate': 0.873791759,
        # "min_child_samples": 100,
        #     'feature_fraction': 0.9,
        #  "bagging_freq":1,
        #     'bagging_fraction': 0.9,
        #     "lambda_l1":10,
        #     "lambda_l2":10,
        #    "scale_pos_weight":30,
        #     'min_data_per_group':500,

        #     'verbose': 1   
            'task': 'train',
            'boosting_type': 'gbdt',
            'objective': 'regression',
            'metric': { 'rmse'},
            'num_iterations':15000,
            'learning_rate': 0.0873791759,
            'bagging_fraction': 0.8852,
            "lambda_l1":1,
            "lambda_l2":10,
            'bagging_fraction': 0.8851971746199973,
  'bagging_freq': 7,
  'feature_fraction': 0.8521290333663841,
  'max_bin': 4844,
  'max_depth': 33,
  'min_child_samples': 173,
  'min_child_weight': 146.216673714379,
  'min_data_per_group': 332,
  'min_split_gain': 0.004934052122171649,
  'num_leaves': 301,
  'scale_pos_weight': 329.13629995365216,

            'verbose': 1    
        }




        modelo = lgb.train(params,
                           lgb_data_train,
                           num_boost_round=95100,
                           valid_sets=lgb_data_eval,
                           early_stopping_rounds=1500,
                           verbose_eval=25,
                           categorical_feature=cat_ind
                          )

        importancias['gain_'+str(i)]=modelo.feature_importance(importance_type="gain")


        data.loc[test_index,'estimator']=modelo.predict(data.loc[test_index,features].values, num_iteration=modelo.best_iteration)

        model.append(modelo)

        pred_test=pred_test+modelo.predict(test[features].values, num_iteration=modelo.best_iteration)

        print ("Fold_"+str(i))
        a= (mean_squared_error(data.loc[test_index,target],data.loc[test_index,'estimator']))**0.5
        r.append(a)
        print (a)
        print ("")

        i=i+1
        
    for l in categorical_transform:

            data.loc[~data[l].isnull(),l]=dict_cat[l].inverse_transform(data.loc[~data[l].isnull(),l].astype(int))
            
            test.loc[~test[l].isnull(),l]=dict_cat[l].inverse_transform(test.loc[~test[l].isnull(),l].astype(int))
            
    importancias["gain_avg"]=importancias[["gain_1","gain_2","gain_3","gain_4","gain_5"]].mean(axis=1)
    importancias=importancias.sort_values("gain_avg",ascending=False).reset_index(drop=True)
    
    pred_test=(pred_test/6)
    
    
    oof=(mean_squared_error(data[target],data['estimator']))**0.5
    
    print (oof)
    print ("mean: "+str(np.mean(np.array(r))))
    print ("std: "+str(np.std(np.array(r))))
    
    dict_resultados={}
    
    dict_resultados['importancias']=importancias
    
    dict_resultados['predicciones']=pred_test
    
    
    
    return dict_resultados,model

model = []
dict_resultados,_=entrena_lgb(data=df_train,test=df_test,features=features,categorical=categorical,target=target)

temp=dict_resultados['importancias']
features_selected=temp['variable'].tolist()[0:4]

model = []
dict_resultados_2,model=entrena_lgb(data=df_train,test=df_test,features=features_selected,categorical=categorical,target=target)

features_selected_2=list(features_selected)

features_selected_2.extend(['State_Factor'])

model_2 = []
dict_resultados_3,model_2=entrena_lgb(data=df_train,test=df_test,features=features_selected_2,categorical=categorical,target=target)

categorical_numerical = df_train[categorical].dropna().select_dtypes(include=np.number).columns.tolist()
    
categorical_transform=[x for x in categorical if x not in categorical_numerical]

for l in categorical_transform:
    le = preprocessing.LabelEncoder()
    le.fit(list(df_train[l].dropna())+list(df_test[l].dropna()))

    
    
    df_test.loc[~df_test[l].isnull(),l]=le.transform(df_test.loc[~df_test[l].isnull(),l])

pred_test = 0
for i in [2,3]:
  pred_test =pred_test + model[i].predict(df_test[features_selected].values,num_iteration=model[i].best_iteration)
  pred_test = pred_test + model_2[i].predict(df_test[features_selected_2].values,num_iteration=model_2[i].best_iteration)
  
pred_test = pred_test/4

pred_test = 0
for i in [2,3]:
  #pred_test =pred_test + model[2].predict(df_test[features_selected].values,num_iteration=model[2].best_iteration)
  pred_test = pred_test + model_2[i].predict(df_test[features_selected_2].values,num_iteration=model_2[i].best_iteration)

pred_test = pred_test /2

df_test['site_eui']=(dict_resultados_2['predicciones'].copy()+dict_resultados_3['predicciones'].copy())/2

df_test['site_eui']=pred_test

df_test[['id','site_eui']].to_csv('submission_tune_11.csv',index=False)

features_selected_2

