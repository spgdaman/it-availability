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

    st.write(ita)
    download_button_str = download_button(ita,"ita.csv",'Download CSV',pickle_it=False)
    st.markdown(download_button_str, unsafe_allow_html=True)

st.header("This is the data to be used for common uptime/downtime")
amalgam(multiple_files_1)

st.header("This is the data to be used for DDNS")
amalgam(multiple_files_2)