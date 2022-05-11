import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import time
import streamlit as st

st.set_option('deprecation.showPyplotGlobalUse', False)
path = 'data.xlsx'

@st.cache
def load_dataset(path):
    df = pd.read_excel(path)
    df.dropna(inplace=True)
    df.drop(columns='opraTradeType', inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df
#print(len(df)-len(df.dropna()),'rows with na values')
df = load_dataset(path)

st.header('Daily Trends', anchor=None)
date = st.selectbox('Select date',    ('2022-01-18','2022-01-19','2022-01-20','2022-01-21','2022-01-24', '2022-01-25', '2022-01-26')) 

#create data object for specific date
df_specific_date = df[df['tradeDate']==date]
df_specific_date.drop(columns='tradeDate', inplace=True)
df_specific_date.sort_values(by='tradeTime', inplace=True)
df_specific_date.reset_index(inplace=True, drop=True)
df_specific_date['rollingVolume'] = df_specific_date.tradeSize.cumsum()
daily_median = df.groupby('tradeDate').agg({'tradeSize': sum}).tradeSize.median()
daily_mean = df.groupby('tradeDate').agg({'tradeSize': sum}).tradeSize.mean()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric('First Trade', df_specific_date.tradeTime.min().strftime("%H:%M:%S"))
col2.metric('Mean Trade Size', round(df_specific_date.tradeSize.mean(),2))
col3.metric('Median Trade Size', df_specific_date.tradeSize.median())
col4.metric('Total Volume', int(df_specific_date.tradeSize.sum()))
col5.metric('Last Trade', df_specific_date.tradeTime.max().strftime("%H:%M:%S"))
#create visualization for specific date
def plot_trades(df):
    fig, (ax1, ax2) = plt.subplots(1, 2)
    df_specific_date.plot(x='tradeTime', y='tradeSize', legend=False, ylabel='Trade Size', xlabel='Time', ax=ax1, title=f'Trading Throughout {date}')
    df_specific_date.plot(x='tradeTime', y='rollingVolume', legend=False, ylabel='Trade Volume', xlabel='Time', ax=ax2, title=f'Cumulative Trading Volume on {date}', label='')
    ax2.hlines(y=daily_median, xmin=df_specific_date.tradeTime.min(), xmax=df_specific_date.tradeTime.max(), colors='r', label='Sample median', linestyle='dashed')
    ax2.hlines(y=daily_mean, xmin=df_specific_date.tradeTime.min(), xmax=df_specific_date.tradeTime.max(), colors='b', label='Sample mean', linestyle='dashed')
    ax2.legend(loc=4)
    return fig.set_size_inches(12, 5)
st.pyplot(fig=plot_trades(df_specific_date))

#create top ten trades and display
top_10 = df_specific_date.sort_values(by='tradeSize', ascending=False).head(n=10)
top_10.reset_index(inplace=True, drop=True)
top_10['percTotal'] = round((top_10['tradeSize'] / df_specific_date.tradeSize.sum())*100,4)
top_10.drop(columns='rollingVolume', inplace=True)
st.subheader(f'Top 10 Trades by Size on {date}')
st.table(data=top_10.style.format({"tradeTime": lambda t: t.strftime("%H:%M:%S")}))

st.subheader(f'Trade Volume by Product on {date}')
df_vol_prod = df_specific_date.groupby('undsym').agg({
    'tradeSize': sum
}).sort_values(by='tradeSize', ascending=False)
df_vol_prod['percTotal'] = round((df_vol_prod.tradeSize / df_vol_prod.tradeSize.sum())*100,4)
df_vol_prod

st.subheader(f'Trade Volume by Expiration Date on {date}')
df_vol_exp = df_specific_date.groupby('expdate').agg({
    'tradeSize': sum
}).sort_values(by='tradeSize', ascending=False)
df_vol_exp['percTotal'] = round((df_vol_exp['tradeSize'] / df_vol_exp.tradeSize.sum())*100,4)
df_vol_exp

st.header('Positions')
prod = st.selectbox('Select product',    ('FB','AMD','TSLA','AMZN','NVDA', 'INTC', 'AAPL', 'JPM', 'GS', 'GOOG')) 
exp = st.selectbox('Select expiration date',    ('2022-01-21','2022-01-28','2022-02-04','2022-02-11','2022-02-18', '2022-02-25', '2022-03-04', '2022-03-18', '2022-04-14', '2022-05-20', '2022-06-17', '2022-07-15', '2022-08-19', '2022-09-16', '2022-10-21', '2022-11-18', '2022-12-16', '2023-01-20', '2023-03-17', '2023-04-21', '2023-06-16', '2023-09-15', '2024-01-19')) 

#create specific product dataframe
specific_prod_exp = df[(df['expdate']==exp)&(df['undsym']==prod)]
specific_prod_exp.reset_index(inplace=True, drop=True)
specific_prod_exp.drop(columns=['tradeDate', 'tradeTime'], inplace=True)

long_call = specific_prod_exp[(specific_prod_exp['callPut']=='C')&(specific_prod_exp['side']=='B')]['tradeSize'].sum()
short_call = specific_prod_exp[(specific_prod_exp['callPut']=='C')&(specific_prod_exp['side']=='S')]['tradeSize'].sum()
long_put = specific_prod_exp[(specific_prod_exp['callPut']=='P')&(specific_prod_exp['side']=='B')]['tradeSize'].sum()
short_put = specific_prod_exp[(specific_prod_exp['callPut']=='P')&(specific_prod_exp['side']=='S')]['tradeSize'].sum()
values = [long_call, short_call, long_put, short_put]

def autopct_format(values):
    def my_format(pct):
        total = sum(values)
        val = int(round(pct*total/100.0))
        return '{:.2f}%\n({v:d})'.format(pct, v=val)
    return my_format

mycolors = ["#66c75d", "#c4f5bf", "#d16666", "#f5bfbf"]

def plot_position(vals):
    plt.pie(vals, labels=['Bought calls', 'Sold calls', 'Bought puts', 'Sold puts'], autopct=autopct_format(values), colors=mycolors)
    plt.title(f"Overall Position for {prod} Expiring on {exp}")
    return plt
st.pyplot(fig=plot_position(values))

df_exp_date = df[df['expdate']==exp]
labels = df_exp_date.undsym.unique()

long_calls = []
short_calls = []
long_puts = []
short_puts = []
for x in labels:
    pl = df_exp_date[df_exp_date['undsym']==x]
    lc = pl[(pl['callPut']=='C')&(pl['side']=='B')]['tradeSize'].sum()
    print(lc, x)
    long_calls.append(lc)
    sc = pl[(pl['callPut']=='C')&(pl['side']=='S')]['tradeSize'].sum()
    print(sc, x)
    short_calls.append(sc)
    lp = pl[(pl['callPut']=='P')&(pl['side']=='B')]['tradeSize'].sum()
    long_puts.append(lp)
    sp = pl[(pl['callPut']=='P')&(pl['side']=='S')]['tradeSize'].sum()
    short_puts.append(sp)
def plot_overall(exp):
    width = 0.35       # the width of the bars: can also be len(x) sequence

    fig, ax = plt.subplots()

    ax.bar(labels, long_calls, width, label='Bought calls', color="#66c75d")
    ax.bar(labels, short_calls, width, label='Sold calls', bottom = long_calls, color="#c4f5bf")
    ax.bar(labels, long_puts, width,  label='Bought puts', bottom= np.array(long_calls)+np.array(short_calls), color="#d16666")
    ax.bar(labels, short_puts, width, label='Sold puts', bottom=np.array(long_calls)+np.array(short_calls)+np.array(long_puts), color="#f5bfbf")



    ax.set_ylabel('Trade Size')
    ax.set_xlabel('Product')
    ax.set_title(f'Position by Product Expiring on {exp}')
    ax.legend()

    return plt.show()
st.pyplot(fig=plot_overall(exp))