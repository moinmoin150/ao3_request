import streamlit as st
import re
from bs4 import BeautifulSoup, NavigableString
import urllib.request
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode
import pandas as pd

data= pd.read_csv('GGAD_test.csv', index_col=0) 

gb = GridOptionsBuilder.from_dataframe(data)
gb.configure_pagination(paginationAutoPageSize=True) #Add pagination
gb.configure_side_bar() #Add a sidebar
gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children") #Enable multi-row selection
gridOptions = gb.build()

grid_response = AgGrid(
    data,
    gridOptions=gridOptions,
    data_return_mode='AS_INPUT', 
    update_mode='MODEL_CHANGED', 
    fit_columns_on_grid_load=False,
    theme='blue', #Add theme color to the table
    enable_enterprise_modules=True,
    height=350, 
    width='100%',
    reload_data=True
)

data = grid_response['data']
selected = grid_response['selected_rows'] 
df = pd.DataFrame(selected)

def navigate_chapters(work_id):
    url = 'https://archiveofourown.org/works/' + str(work_id) + '/navigate?view_adult=true'
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req)
    bs = BeautifulSoup(resp, 'lxml')
    chapters = bs.find('ol', {'class':'chapter index group'}).find_all('li')
    links = [i.find('a').get('href') for i in chapters]
    return links

def get_content(id):
    url = 'https://archiveofourown.org' + str(id) + '?view_adult=true'
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req)
    bs = BeautifulSoup(resp, 'lxml')
    for br in bs.find_all("br"):
        br.replace_with("nnnnn")
    chapters = bs.find('div', {'class':'userstuff'})
    title = bs.find('h2', {'class':'title heading'})
    author = bs.find('a',{'rel':'author'})
    st.markdown(f"<h2 style='text-align: center;'>{title.text}</h2>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center;'>by {author.text}</h4>", unsafe_allow_html=True)
    try:
        chapter_headline = bs.find('h3',{'class':'title'}).text.strip()
        st.markdown(f"<h3 style='text-align: center;'>{chapter_headline}</h3>", unsafe_allow_html=True)
    except:
        pass
    texts = chapters.find_all('p')
    para = []
    for t in texts:
        para.append(' '.join(['\n' if (i == 'nnnnn') else i for i in list(t.stripped_strings) ]))
        if t.find('img'):
            source = t.find('img').get('src')
            st.image(source)
    content = '\n'.join(para)
    content = content.replace('\n', ' \n\n\n ') #.replace('\xa0', ' \n\n\n ') #.replace('\u3000', ' \n\n\n ')
    st.write(re.sub("~+", " \* ", str(content)))

def text_field(label, columns=None, **input_params):
    c1, c2, _ = st.columns([3, 2, 4])
    c1.markdown("##")
    c1.markdown(label)
    input_params.setdefault("key", label)
    return c2.text_input("", **input_params)



st.markdown("# 给我一篇FanFic！")
st.markdown("### 给我一个数字ID:")
work_id = text_field("archiveofourown.org/works/")
if len(work_id) > 1:
    try:
        links = navigate_chapters(work_id)
        options = [f'Chapter {i+1}' for i in range(len(links))]
        if len(links) == 1:
            get_content(f'/works/{work_id}')
        else:
            option = st.selectbox('选择章节', options)
            get_content(links[options.index(option)])
    except:
        st.write("请输入一个有效的ID！")
        
