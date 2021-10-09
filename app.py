from pandasql import sqldf 
import numpy as np
from matplotlib import pyplot as plt
import streamlit as st
import pandas as pd
import io
import re
from download import download_button

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
common_uptime['Downtime'] = common_uptime['Downtime'].astype('int')/100

# add conditional columns to common uptime dataframe
common_uptime['uptime'] = 1 - common_uptime['Downtime']
common_uptime['Uptime (Minutes)'] = common_uptime['uptime'] * 15
common_uptime['Max_Uptime'] = 15
common_uptime['Downtime (Minutes)'] = common_uptime['Downtime'] * 15
common_uptime.rename(columns={"Uptime (Minutes)":"Uptime_(Minutes)"}, inplace=True)

common_copy = common_uptime[['MC','Uptime_(Minutes)','Max_Uptime','ISP']]
mysql = lambda q: sqldf(q, globals())
IS = '''
    SELECT MC, (SUM("Uptime_(Minutes)") / SUM(Max_Uptime))*100 as Availability
    FROM common_copy
    WHERE ISP = 'IS'
    GROUP BY MC
    ORDER BY Availability;
''' 

LTK = '''
    SELECT MC, (SUM("Uptime_(Minutes)") / SUM(Max_Uptime))*100 as Availability
    FROM common_copy
    WHERE ISP = 'LTK'
    GROUP BY MC
    ORDER BY Availability;
''' 

JTL = '''
    SELECT MC, (SUM("Uptime_(Minutes)") / SUM(Max_Uptime))*100 as Availability
    FROM common_copy
    WHERE ISP = 'JTL'
    GROUP BY MC
    ORDER BY Availability;
''' 

SAF = '''
    SELECT MC, (SUM("Uptime_(Minutes)") / SUM(Max_Uptime))*100 as Availability
    FROM common_copy
    WHERE ISP = 'SAF'
    GROUP BY MC
    ORDER BY Availability;
'''

ZUKU = '''
    SELECT MC, (SUM("Uptime_(Minutes)") / SUM(Max_Uptime))*100 as Availability
    FROM common_copy
    WHERE ISP = 'ZUKU'
    GROUP BY MC
    ORDER BY Availability;
''' 

IS = mysql(IS).set_index('MC')
LTK = mysql(LTK).set_index('MC')
JTL = mysql(JTL).set_index('MC')
SAF = mysql(SAF).set_index('MC')
ZUKU = mysql(ZUKU).set_index('MC')

IS = IS['Availability'].astype(int)
LTK = LTK['Availability'].astype(int)
JTL = JTL['Availability'].astype(int)
SAF = SAF['Availability'].astype(int)
ZUKU = ZUKU['Availability'].astype(int)

st.subheader("IS Availability")
st.bar_chart(IS)

st.subheader("LTK Availability")
st.bar_chart(LTK)

st.subheader("JTL Availability")
st.bar_chart(JTL)

st.subheader("SAF Availability")
st.bar_chart(SAF)

st.subheader("ZUKU Common Uptime/Downtime")
st.bar_chart(ZUKU)







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


