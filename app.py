from pandasql import sqldf 
import numpy as np
from matplotlib import pyplot as plt
import streamlit as st
import pandas as pd
import io
import re
from download import download_button

green = '#00FFB2'
yellow = '#F0E199'
red = '#EFB5B9'

multiple_files_1 = st.sidebar.file_uploader(
    "Upload Common Uptime/Downtime Data Here, this is a multiple file uploader.",
    accept_multiple_files=True,
    key = "I am number one"
)

multiple_files_2 = st.sidebar.file_uploader(
    "Upload DDNS Data Here, this is a multiple file uploader.",
    accept_multiple_files=True,
    key = "I am number two"
)

def amalgam(multiple_files):
    ita = pd.DataFrame(columns=["Date Time", "Downtime", "MC", "ISP"])
    for file in multiple_files:
        # file_container = st.expander(
        #     f"File name: {file.name} ({file.size}b)"
        # )

        # get the raw data in byte format
        data = io.BytesIO(file.getbuffer())

        # read the raw data as csv
        data_df = pd.read_csv(data)

        # delete empty columns with NaN as value
        data_df.dropna(how='all', axis=1, inplace=True)

        # delete last row of data in the DataFrame
        data_df.drop(data_df.tail(1).index,inplace=True)

        # get name of the file and split mc from isp name
        text = file.name.lower()

        split_text = re.split(r'\s',text)

        isp_name = split_text[-1].replace(".csv","").upper()
        del split_text[-1]

        file_name = ""
        if len(split_text) == 1:
            file_name = split_text[0]
            file_name = file_name.title()
        else:
            file_name = ' '.join(split_text)
            file_name = file_name.title()

        # # check for ddns data
        # if file_name == "DDNS":

        data_df['MC'] = file_name
        data_df['ISP'] = isp_name

        # append data to main DataFrame
        ita = ita.append(data_df)

    if "DDNS" in ita['ISP'].unique():
        del ita["ISP"]

    download_button_str = download_button(ita,"ita.csv",'Download CSV',pickle_it=False)
    st.markdown(download_button_str, unsafe_allow_html=True)
    return ita

st.header("This is the data to be used for common uptime/downtime")
common_uptime = amalgam(multiple_files_1)
common_uptime

st.header("This is the data to be used for DDNS")
ddns = amalgam(multiple_files_2)
ddns

# introduce exclude data
exclude = pd.read_json('exclude.json')
st.write(exclude)

# date and time splitting to individual columns for common_uptime
common_uptime['Date Time'] = common_uptime['Date Time'].astype('string')
common_uptime['Date Time'] = [re.split(r' ',i) for i in common_uptime['Date Time']]
common_uptime['Time'] = [' '.join(i[1:]) for i in common_uptime['Date Time']]
common_uptime['Date'] = [i[0] for i in common_uptime['Date Time']]

# type conversion
common_uptime['MC'] = common_uptime['MC'].astype('string')

del common_uptime['Date Time']

# merge with exclude dataframe
common_uptime = pd.merge(
    common_uptime,
    exclude,
    how = 'left',
    left_on = 'Time',
    right_on = 'Exclude Time'
)

common_uptime['Check'] = common_uptime['Check'].fillna('0')
common_uptime = common_uptime[common_uptime['Check'] == '0']

del common_uptime['Check']
del common_uptime['Exclude Time']

# cleaning Downtime column in common_uptime dataframe
common_uptime['Downtime'] = common_uptime['Downtime'].astype('string')
common_uptime['Downtime'] = common_uptime['Downtime'].fillna('0')
common_uptime['Downtime'] = common_uptime['Downtime'].replace({" ":"","<":"",">":""})
common_uptime['Downtime'] = common_uptime['Downtime'].str.replace('%','')
common_uptime['Downtime'] = common_uptime['Downtime'].str.replace('>','')
common_uptime['Downtime'] = common_uptime['Downtime'].replace({"":0})
common_uptime['Downtime'] = common_uptime['Downtime'].astype('int')/100

# add conditional columns to common uptime dataframe (ITA)
common_uptime['uptime'] = 1 - common_uptime['Downtime']
common_uptime['Uptime (Minutes)'] = common_uptime['uptime'] * 15
common_uptime['Max_Uptime'] = 15
common_uptime['Downtime (Minutes)'] = common_uptime['Downtime'] * 15
common_uptime.rename(columns={"Uptime (Minutes)":"Uptime_(Minutes)"}, inplace=True)
common_uptime['common_downtime'] = common_uptime['uptime'].apply(lambda x: 0.25 if x == 0 else 0)

common_downtime = common_uptime.groupby(['MC'], as_index=False)['common_downtime'].sum()
st.write(common_downtime)
download_button_str = download_button(common_downtime,"common_downtime.csv",'Download CSV',pickle_it=False)
st.markdown(download_button_str, unsafe_allow_html=True)

# dataframe checker
st.write("ITA")
st.write(common_uptime)
download_button_str = download_button(common_uptime,"ita.csv",'Download CSV',pickle_it=False)
st.markdown(download_button_str, unsafe_allow_html=True)

common_copy = common_uptime[['MC','Uptime_(Minutes)','Max_Uptime','ISP']]
mysql = lambda q: sqldf(q, globals())

uptime_common = '''
    SELECT MC, (SUM("Uptime_(Minutes)") / SUM(Max_Uptime))*100 as Availability
    FROM common_copy
    GROUP BY MC
    ORDER BY Availability DESC;
''' 

IS = '''
    SELECT MC, (SUM("Uptime_(Minutes)") / SUM(Max_Uptime))*100 as Availability
    FROM common_copy
    WHERE ISP = 'IS'
    GROUP BY MC
    ORDER BY Availability DESC;
''' 

LTK = '''
    SELECT MC, (SUM("Uptime_(Minutes)") / SUM(Max_Uptime))*100 as Availability
    FROM common_copy
    WHERE ISP = 'LTK'
    GROUP BY MC
    ORDER BY Availability DESC;
''' 

JTL = '''
    SELECT MC, (SUM("Uptime_(Minutes)") / SUM(Max_Uptime))*100 as Availability
    FROM common_copy
    WHERE ISP = 'JTL'
    GROUP BY MC
    ORDER BY Availability DESC;
''' 

SAF = '''
    SELECT MC, (SUM("Uptime_(Minutes)") / SUM(Max_Uptime))*100 as Availability
    FROM common_copy
    WHERE ISP like 'SAF' or ISP like 'SAFARICOM'
    GROUP BY MC
    ORDER BY Availability DESC;
'''

ZUKU = '''
    SELECT MC, (SUM("Uptime_(Minutes)") / SUM(Max_Uptime))*100 as Availability
    FROM common_copy
    WHERE ISP = 'ZUKU'
    GROUP BY MC
    ORDER BY Availability DESC;
''' 


uptime_common = mysql(uptime_common)
IS = mysql(IS)
LTK = mysql(LTK)
JTL = mysql(JTL)
SAF = mysql(SAF)
ZUKU = mysql(ZUKU)

IS['Availability'] = IS['Availability'].astype(float).round(decimals=2)
LTK['Availability'] = LTK['Availability'].astype(float).round(decimals=2)
JTL['Availability'] = JTL['Availability'].astype(float).round(decimals=2)
SAF['Availability'] = SAF['Availability'].astype(float).round(decimals=2)
ZUKU['Availability'] = ZUKU['Availability'].astype(float).round(decimals=2)
uptime_common['Availability'] = uptime_common['Availability'].astype(float).round(decimals=2)

# IS Availability Bar Chart
st.subheader("IS Availability")
IS_avail_x = IS['MC'].to_list()
IS_avail_y = IS['Availability'].to_list()

col = []
for val in IS_avail_y:
    if val >= 99:
        col.append(green)
    elif val == 98:
        col.append(yellow)
    else:
        col.append(red)

fig = plt.figure()

plt.bar(IS_avail_x,IS_avail_y, color = col)
plt.xticks(rotation=80)
for index,data in enumerate(IS_avail_y):
    plt.text(x=index , y =data+1 , s=f"{data}%" , fontdict=dict(fontsize=6), ha='center')
plt.tight_layout()
st.pyplot(fig)

# LTK Availability Bar Chart
st.subheader("LTK Availability")
IS_avail_x = LTK['MC'].to_list()
IS_avail_y = LTK['Availability'].to_list()

col = []
for val in IS_avail_y:
    if val >= 99:
        col.append(green)
    elif val == 98:
        col.append(yellow)
    else:
        col.append(red)

fig = plt.figure()

plt.bar(IS_avail_x,IS_avail_y, color = col)
plt.xticks(rotation=80)
for index,data in enumerate(IS_avail_y):
    plt.text(x=index , y =data+1 , s=f"{data}%" , fontdict=dict(fontsize=6), ha='center')
plt.tight_layout()
st.pyplot(fig)


# JTL Availability Bar Chart
st.subheader("JTL Availability")
IS_avail_x = JTL['MC'].to_list()
IS_avail_y = JTL['Availability'].to_list()

col = []
for val in IS_avail_y:
    if val >= 99:
        col.append(green)
    elif val == 98:
        col.append(yellow)
    else:
        col.append(red)

fig = plt.figure()

plt.bar(IS_avail_x,IS_avail_y, color = col)
plt.xticks(rotation=80)
for index,data in enumerate(IS_avail_y):
    plt.text(x=index , y =data+1 , s=f"{data}%" , fontdict=dict(fontsize=6), ha='center')
plt.tight_layout()
st.pyplot(fig)


# SAF Availability Bar Chart
st.subheader("SAF Availability")
IS_avail_x = SAF['MC'].to_list()
IS_avail_y = SAF['Availability'].to_list()

col = []
for val in IS_avail_y:
    if val >= 99:
        col.append(green)
    elif val == 98:
        col.append(yellow)
    else:
        col.append(red)

fig = plt.figure()

plt.bar(IS_avail_x,IS_avail_y, color = col)
plt.xticks(rotation=80)
for index,data in enumerate(IS_avail_y):
    plt.text(x=index , y =data+1 , s=f"{data}%" , fontdict=dict(fontsize=5), ha='center')
plt.tight_layout()
st.pyplot(fig)

# ZUKU Availability Bar Chart
st.subheader("ZUKU Common Uptime/Downtime")
IS_avail_x = ZUKU['MC'].to_list()
IS_avail_y = ZUKU['Availability'].to_list()

col = []
for val in IS_avail_y:
    if val >= 99:
        col.append(green)
    elif val == 98:
        col.append(yellow)
    else:
        col.append(red)

fig = plt.figure()

plt.bar(IS_avail_x,IS_avail_y, color = col)
plt.xticks(rotation=80)
for index,data in enumerate(IS_avail_y):
    plt.text(x=index , y =data+1 , s=f"{data}%" , fontdict=dict(fontsize=6), ha='center')
plt.tight_layout()
st.pyplot(fig)

# Common Uptime Bar Chart
st.subheader("Common Uptime by MC")
avail_x = uptime_common['MC'].to_list()
avail_y = uptime_common['Availability'].to_list()

col = []
for val in avail_y:
    if val >= 99:
        col.append(green)
    elif val == 98:
        col.append(yellow)
    else:
        col.append(red)

fig = plt.figure()

plt.bar(avail_x,avail_y, color = col)
plt.xticks(rotation=80)
for index,data in enumerate(avail_y):
    plt.text(x=index , y =data+1 , s=f"{data}%" , fontdict=dict(fontsize=4.6), ha='center')
plt.tight_layout()
st.pyplot(fig)



# date and time splitting to individual columns for ddns
ddns['Date Time'] = ddns['Date Time'].astype('string')
ddns['Date Time'] = [re.split(r' ',i) for i in ddns['Date Time']]
ddns['Time'] = [' '.join(i[1:]) for i in ddns['Date Time']]
ddns['Date'] = [i[0] for i in ddns['Date Time']]

del ddns['Date Time']

# merge with exclude dataframe
ddns = pd.merge(
    ddns,
    exclude,
    how = 'left',
    left_on = 'Time',
    right_on = 'Exclude Time'
)

ddns['Check'] = ddns['Check'].fillna('0')
ddns = ddns[ddns['Check'] == '0']

del ddns['Check']
del ddns['Exclude Time']


# cleaning Downtime column in ddns dataframe
ddns['Downtime'] = ddns['Downtime'].astype('string')
ddns['Downtime'] = ddns['Downtime'].fillna('0')
ddns['Downtime'] = ddns['Downtime'].replace({" ":"","<":"",">":""})
ddns['Downtime'] = ddns['Downtime'].str.replace('%','')
ddns['Downtime'] = ddns['Downtime'].str.replace('>','')
ddns['Downtime'] = ddns['Downtime'].astype('int')/100


# add conditional columns to common uptime dataframe
ddns['uptime'] = 1 - ddns['Downtime']
ddns['Uptime (Minutes)'] = ddns['uptime'] * 15
ddns['Max_Uptime'] = 15
ddns['Downtime (Minutes)'] = ddns['Downtime'] * 15
ddns.rename(columns={"Uptime (Minutes)":"Uptime_(Minutes)"}, inplace=True)

ddns_common_copy = ddns[['MC','Uptime_(Minutes)','Max_Uptime']]
mysql = lambda q: sqldf(q, globals())
ddns_grouping = '''
    SELECT MC, (SUM("Uptime_(Minutes)") / SUM(Max_Uptime))*100 as Availability
    FROM ddns_common_copy
    GROUP BY MC
    ORDER BY Availability DESC;
''' 

ddns_grouping = mysql(ddns_grouping)
ddns_grouping['Availability'] = ddns_grouping['Availability'].astype(float).round(decimals=2)

# DDNS Common Uptime/Downtime Bar Chart
st.subheader("DDNS Common Uptime/Downtime")
avail_x = ddns_grouping['MC'].to_list()
avail_y = ddns_grouping['Availability'].to_list()

col = []
for val in avail_y:
    if val >= 99:
        col.append(green)
    elif val == 98:
        col.append(yellow)
    else:
        col.append(red)

fig = plt.figure()

plt.bar(avail_x,avail_y, color = col)
plt.xticks(rotation=80)
for index,data in enumerate(avail_y):
    plt.text(x=index , y =data+1 , s=f"{data}%" , fontdict=dict(fontsize=4.8), ha='center')
plt.tight_layout()
st.pyplot(fig)