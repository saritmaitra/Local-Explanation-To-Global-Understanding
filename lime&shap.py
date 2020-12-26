# -*- coding: utf-8 -*-
"""Lime&Shap.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1h7EkMpxMHwI0FgENu3UVSFOD_9SANpFP
"""

# Commented out IPython magic to ensure Python compatibility.
!pip install pyforest
from pyforest import *
import datetime, pickle, copy
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 150)
import matplotlib.pyplot as plt
# %matplotlib inline  
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

'''Data Prep'''
from sklearn import preprocessing as pp
from scipy.stats import pearsonr
from sklearn.model_selection import train_test_split
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import log_loss
from sklearn.metrics import precision_recall_curve, average_precision_score
from sklearn.metrics import roc_curve, auc, roc_auc_score
from sklearn.metrics import confusion_matrix, classification_report

'''Algos'''
from sklearn import model_selection
import lightgbm as lgb 
from lightgbm import LGBMClassifier
from time import time
from lightgbm import *

from google.colab import files
uploaded = files.upload()

# Import data 
df = pd.read_csv("insurance_claims.csv")
df.head()

ax = sns.countplot(x='fraud_reported', data=df, hue='fraud_reported')

df['fraud_reported'].value_counts() # Count number of frauds vs non-frauds

data = df.copy()
data['fraud_reported'].replace(to_replace='Y', value=1, inplace=True)
data['fraud_reported'].replace(to_replace='N',  value=0, inplace=True)
data['csl_per_person'] = data.policy_csl.str.split('/', expand=True)[0]
data['csl_per_accident'] = data.policy_csl.str.split('/', expand=True)[1]
data['vehicle_age'] = 2020 - data['auto_year'] # Deriving the age of the vehicle based on the year value 
bins = [-1, 3, 6, 9, 12, 17, 20, 24]  # Factorize according to the time period of the day.
names = ["past_midnight", "early_morning", "morning", 'fore-noon', 'afternoon', 'evening', 'night']
data['incident_period_of_day'] = pd.cut(data.incident_hour_of_the_day, bins, labels=names).astype(object)
# dropping unimportant columns

data = data.drop(columns = [
    'policy_number', 
    'policy_csl',
    'insured_zip',
    'policy_bind_date', 
    'incident_date', 
    'incident_location', 
    '_c39', 
    'auto_year', 
    'incident_hour_of_the_day'], axis=1)

data.head(2)

data.info()

# turning object columns type to categorical for easing the transformation process
categorical = data.select_dtypes(include= ['object']).columns
for col in categorical:
   data[col] = data[col].astype('category')
# categorical values ==> numeric values
data[categorical] = data[categorical].apply(lambda x: x.cat.codes)
data.head()

data._get_numeric_data().columns

# Checking Correlation of "fraud_reported" with other variables on a different plot
sns.set(style='darkgrid', context='talk', palette='Dark2')
plt.figure(figsize=(15,5))
data.corr()['fraud_reported'].sort_values(ascending = False).plot(kind='bar')

X = data.drop(columns = ['fraud_reported'], axis=1)  # predictor variables
y = data['fraud_reported']  # target variable
#y = pd.DataFrame(data['fraud_reported'])  # target variable

X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=0.8, random_state=7)
print('length of X_train and X_test: ', len(X_train), len(X_test))
print('length of y_train and y_test: ', len(y_train), len(y_test))

from sklearn.pipeline import make_pipeline
from xgboost import XGBClassifier
from sklearn.model_selection import cross_val_score

print("Training XGB Classifier...")
tic = time()
model = XGBClassifier(early_stopping=True)

model.fit(X_train, y_train.values)
print("done in {:.3f}s".format(time() - tic))
print('Model trained')
AccuracyScore = cross_val_score(model, X_train, y_train, cv=10)
print('Accuracy score:', format(round(AccuracyScore.mean(),2)))
BalancedScore = cross_val_score(model, X_train, y_train, cv=10,scoring="balanced_accuracy")
print('Accuracy balance:', format(round(BalancedScore.mean(),2)))
print("done in {:.3f}s".format(time() - tic))

from xgboost import plot_importance
plt.style.use('ggplot')
# Feature importance
plt.rcParams['figure.figsize'] = [8,10]
plot_importance(model)

# I"m creating one big dataframe that includes both train and test
# to plot them on same plot using seaborn's boxplot
train_expl_df.rename(columns={'weight': 'contribution'}, inplace=True)
test_expl_df.rename(columns={'weight': 'contribution'}, inplace=True)
train_expl_df['data'] = 'train'
test_expl_df['data'] = 'test'
train_test_expl_df = pd.concat([train_expl_df, test_expl_df])
sns.boxplot(x='feature', y='contribution', hue='data', order=features,
            data=train_test_expl_df.loc[train_test_expl_df.feature!=''],
            palette={'train': 'salmon', 
                     'test':'deepskyblue'})
plt.legend(loc=9)
plt.title('Distributions of Feature Contributions');

!pip install eli5
from eli5.sklearn import PermutationImportance

import eli5
# let's check the importance of each attributes
perm = PermutationImportance(model, random_state = 0).fit(X_test, y_test)
eli5.show_weights(perm, feature_names = X_test.columns.tolist())

perm_train = PermutationImportance(model, scoring='accuracy',
                                   n_iter=100, random_state=1)
# fit and see the permuation importances
perm_train.fit(X_train, y_train)
eli5.explain_weights_df(perm_train, feature_names=X_train.columns.tolist()).head()

# figure size in inches
from matplotlib import rcParams
rcParams['figure.figsize'] = 25,5

perm_train_df = pd.DataFrame(data=perm.results_,
                                      columns=X.columns)
(sns.boxplot(data=perm_train_df)
        .set(title='Permutation Importance Distributions (training data)',
             ylabel='Importance'));
plt.xticks(rotation=90)
plt.show()

!pip install pdpbox
from pdpbox import pdp, get_dataset, info_plots

data.head(1)

from sklearn.ensemble.partial_dependence import partial_dependence, plot_partial_dependence
from sklearn.ensemble import GradientBoostingClassifier

clf = GradientBoostingClassifier()
clf.fit(X=X_train, y=y_train)

# Here we make the plot
plots = plot_partial_dependence(clf ,       
                                   features=[0,1, 2,3,4], # column numbers of plots we want to show
                                   X=X_train,            # raw predictors data.
                                   feature_names=['incident_severity','incident_hobbies', 
                                                  'insured_education_level','policy_annual_premium','witnesses'], # labels on graphs
                                   grid_resolution=10) # number of values to plot on x axis
plt.tight_layout()
plt.show()

base_features = X_train.columns.values.tolist()
feature_name = 'incident_severity'
pdp = pdp.pdp_isolate(model=model, dataset=X_test, 
                      model_features = base_features, 
                      feature = feature_name)
pdp.pdp_plot(pdp, feature_name)
plt.show()

fig, axes, summary_df = info_plots.target_plot(\
                                               df=data, feature='capital-gains', 
                                               feature_name='capital-gains', target='fraud_reported', 
                                               show_percentile=True)

fig, axes, summary_df = info_plots.actual_plot(\
                                               model, X_test, feature='capital-gains', 
                                               feature_name='capital-gains',predict_kwds={})

df.auto_model.unique()

fig, axes, summary_df = info_plots.target_plot(\
                                               df=data, feature='auto_model', 
                                               feature_name='auto_model', target='fraud_reported', 
                                               show_percentile=True)

fig, axes, summary_df = info_plots.target_plot(\
                                               df=data, feature='auto_make', 
                                               feature_name='auto_make', target='fraud_reported', 
                                               show_percentile=True)

fig, axes, summary_df = info_plots.target_plot(\
                                               df=data, feature='vehicle_age', 
                                               feature_name='vehicle_age', target='fraud_reported', 
                                               show_percentile=True)

fig, axes, summary_df = info_plots.target_plot(\
                                               df=data, feature='age', 
                                               feature_name='age', target='fraud_reported', 
                                               show_percentile=True)

fig, axes, summary_df = info_plots.actual_plot(\
                                               model, X_test, feature='age', 
                                               feature_name='YearsAge',predict_kwds={})

fig, axes, summary_df = info_plots.target_plot(\
                                               df=data, feature='months_as_customer', 
                                               feature_name='months_as_customer', target='fraud_reported', 
                                               show_percentile=True)

fig, axes, summary_df = info_plots.actual_plot(\
                                               model, X_train, feature='months_as_customer', 
                                               feature_name='MonthsAsCustomer',predict_kwds={})

data.head(1)

df.insured_education_level.unique()

fig, axes, summary_df = info_plots.target_plot(\
                                               df=df, feature=['MD', 'PhD', 'Associate', 
                                                               'Masters', 'High School', 
                                                               'College','JD'], 
                                               feature_name='insured_education_level', 
                                               target='fraud_reported')

fig, axes, summary_df = info_plots.actual_plot(\
                                               model, X_test, feature='insured_education_level', 
                                               feature_name='InsuredEducation',predict_kwds={})

fig, axes, summary_df = info_plots.target_plot_interact(\
                                                        df=data, 
                                                        features=['insured_education_level', 'age'], 
                                                        feature_names=['insured_education_level', 'age'], 
                                                        target='fraud_reported')

fig, axes, summary_df = info_plots.target_plot_interact(\
                                                        df=data, 
                                                        features=['vehicle_age', 'months_as_customer'], 
                                                        feature_names=['vehicle_age', 'months_as_customer'], 
                                                        target='fraud_reported')

pdp_limit = pdp.pdp_isolate(\
                            model, dataset=X_test, 
                            model_features=X_test.columns, feature='months_as_customer')
fig, axes = pdp.pdp_plot(\
                         pdp_limit, 'months_as_customer', frac_to_plot=0.2, 
                         plot_lines=True, x_quantile=True, show_percentile=True, 
                         plot_pts_dist=True)
plt.tight_layout()

df['incident_severity'].unique()

pdp_limit = pdp.pdp_isolate(\
                            model, dataset=X_test, 
                            model_features=X_test.columns, 
                            feature='incident_severity')
fig, axes = pdp.pdp_plot(\
                         pdp_limit, 'incident_severity', frac_to_plot=0.2, 
                         plot_lines=True, x_quantile=True, show_percentile=True, 
                         plot_pts_dist=True)

data.head()

pip install lime

X_train.columns

pip install shap

# get the feature importances from each tree and then visualize the
# distributions as boxplots
all_feat_imp_df = pd.DataFrame(data=[tree.feature_importances_ for tree in clf],
                               columns=X_train.columns)
order_column = all_feat_imp_df.mean(axis=0).sort_values(ascending=False).index.tolist()
 
 
all_feat_imp_df[order_column[:25]].iplot(kind='box', xTitle = 'Features', yTitle='Mean Decease Impurity')

import shap
shap_values = shap.TreeExplainer(model).shap_values(X_test)
shap.summary_plot(shap_values, X_test, plot_type="bar")

X_test.iloc[1,:]

import shap

# Initialize your Jupyter notebook with initjs(), otherwise you will get an error message.
shap.initjs()
# j will be the record we explain
j = 1

explainerXGB = shap.TreeExplainer(model)
shap_values_XGB_test = explainerXGB.shap_values(X_test)
shap.force_plot(explainerXGB.expected_value, shap_values_XGB_test[j], X_test.iloc[[j]])

"""This plot shows a base value that is used to indicate the direction of the prediction. Seeing as most of the targets are 0, it isn’t strange to see that the base value is negative.

The red bar shows how much the probability that the target is 1. Higher education typically leads to
making more.
The blue bars show that these variables decrease the probability, with Agehaving the biggest effect. This makes sense as younger people typically make
less.

We predicted -3.26, whereas the base_value is -1.37. Feature values causing increased predictions are in pink, and their visual size shows the magnitude of the feature's effect. Feature values decreasing the prediction are in blue. The biggest impact comes from authorities contacted being 4. Though incident severity value has a meaningful effect decreasing the prediction.
"""

# visualize the training set predictions
# load JS visualization code to notebook
shap.initjs()
shap.force_plot(explainerXGB.expected_value, shap_values, X_test)

shap.summary_plot(shap_values, X_test)

clf.predict_proba(X_test)[-5:]

from pdpbox import pdp_plot_utils

# Override to fix matplotlib issue
def _pdp_contour_plot_override(X, Y, pdp_mx, inter_ax, cmap, norm, inter_fill_alpha, fontsize, plot_params):
    contour_color = plot_params.get('contour_color', 'white')
    level = np.min([X.shape[0], X.shape[1]])
    c1 = inter_ax.contourf(X, Y, pdp_mx, N=level, origin='lower', cmap=cmap, norm=norm, alpha=inter_fill_alpha)
    c2 = inter_ax.contour(c1, levels=c1.levels, colors=contour_color, origin='lower')
    inter_ax.clabel(c2, fontsize=fontsize, inline=1)
    inter_ax.set_aspect('auto')
    return c1

pdp_plot_utils._pdp_contour_plot = _pdp_contour_plot_override

pdp_inter = pdp.pdp_interact(
    model=model, dataset=X_train, model_features=X_train.columns, features=['mean concavity', 'mean radius']
)

fig, axes = pdp.pdp_interact_plot(
    pdp_interact_out=pdp_inter, feature_names=['mean concavity', 'mean radius'], plot_type='contour',
    x_quantile=True, plot_pdp=True
)