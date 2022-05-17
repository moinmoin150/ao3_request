import streamlit as st
import re
from bs4 import BeautifulSoup, NavigableString
import urllib.request

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
    chapters = bs.find('div', {'id':'chapters'})
    title = bs.find('h2', {'class':'title heading'})
    st.markdown(f"### {{title.text}}")
    texts = chapters.find_all('p')
    para = []
    for t in texts:
        para.append(' '.join(list(t.stripped_strings)))
    content = '\n'.join(para)
    content = content.replace('\n', ' \n\n\n ') #.replace('\xa0', ' \n\n\n ').replace('\u3000', ' \n\n\n ')
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
    links = navigate_chapters(work_id)
    options = [f'Chapter {i+1}' for i in range(len(links))]
    if len(links) == 1:
        get_content(f'/works/{work_id}')
    else:
        option = st.selectbox('How would you like to be contacted?', options)
        get_content(links[options.index(option)])
