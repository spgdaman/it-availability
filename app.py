import streamlit as st
import pandas as pd
import io
import re
from download import download_button

def amalgam():
    multiple_files = st.sidebar.file_uploader(
    "Multiple File Uploader",
    accept_multiple_files=True
    )
    ita = pd.DataFrame(columns=["Date Time", "Downtime", "MC", "ISP"])
    for file in multiple_files:
        file_container = st.expander(
            f"File name: {file.name} ({file.size}b)"
        )

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

        data_df['MC'] = file_name
        data_df['ISP'] = isp_name

        # append data to main DataFrame
        ita = ita.append(data_df)

        file_container.write(data_df)

    download_button_str = download_button(ita,"ita.csv",'Download CSV',pickle_it=False)
    st.sidebar.markdown(download_button_str, unsafe_allow_html=True)
    st.write(ita)

amalgam()