import streamlit as st
import re
from bs4 import BeautifulSoup, NavigableString
import urllib.request
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode
import pandas as pd
import urllib.request
from github import Github


st.set_page_config(layout="wide")
headers = {'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15'}

def scrape():
    url = 'https://archiveofourown.org/tags/Albus%20Dumbledore*s*Gellert%20Grindelwald/works?commit=Sort+and+Filter&page=1&work_search%5Blanguage_id%5D=zh'
    req = urllib.request.Request(url,headers=headers)
    resp = urllib.request.urlopen(req)
    bs = BeautifulSoup(resp, 'lxml')
    pages = bs.find('ol', {'class':'pagination actions'}).find_all('li')
    final_pg = int(pages[-2].text)
    titles = []
    authors = []
    ids = []
    date_updated = []
    ratings = []
    tags = []
    complete = []
    languages = []
    word_count = []
    chapters = []
    summaries = []
    comments = []
    kudos = []
    bookmarks = []
    hits = []
    for i in range(1,final_pg+1):
        url = f'https://archiveofourown.org/tags/Albus%20Dumbledore*s*Gellert%20Grindelwald/works?commit=Sort+and+Filter&page={i}&work_search%5Blanguage_id%5D=zh'
        req = urllib.request.Request(url,headers=headers)
        resp = urllib.request.urlopen(req)
        bs = BeautifulSoup(resp, 'lxml')

        for article in bs.find_all('li', {'role':'article'}):
            titles.append(article.find('h4', {'class':'heading'}).find('a').text)
            try:
                authors.append(article.find('a', {'rel':'author'}).text)
            except:
                authors.append('Anonymous')
            ids.append(article.find('h4', {'class':'heading'}).find('a').get('href')[7:])
            date_updated.append(article.find('p', {'class':'datetime'}).text)
            ratings.append(article.find('span', {'class':re.compile(r'rating\-.*rating')}).text)
            tags.append('; '.join([i.text for i in article.find('ul',{'class':'tags commas'}).find_all('a', {'class':'tag'})]))
            complete.append(article.find('span', {'class':re.compile(r'complete\-.*iswip')}).text)
            languages.append(article.find('dd', {'class':'language'}).text)
            try:
                summaries.append(article.find('blockquote', {'class':'userstuff summary'}).text.strip())
            except:
                summaries.append('No Summary')
            count = article.find('dd', {'class':'words'}).text
            if len(count) > 0:
                word_count.append(int(count.replace(',','')))
            else:
                word_count.append(0)
            chapters.append(int(article.find('dd', {'class':'chapters'}).text.split('/')[0].replace(',','')))
            try:
                comments.append(int(article.find('dd', {'class':'comments'}).text.replace(',','')))
            except:
                comments.append(0)
            try:
                kudos.append(int(article.find('dd', {'class':'kudos'}).text.replace(',','')))
            except:
                kudos.append(0)
            try:
                bookmarks.append(int(article.find('dd', {'class':'bookmarks'}).text.replace(',','')))
            except:
                bookmarks.append(0)
            try:
                hits.append(int(article.find('dd', {'class':'hits'}).text.replace(',','')))
            except:
                hits.append(0)
                
    df = pd.DataFrame(list(zip(titles, authors, ids, date_updated, ratings, tags, summaries, \
                              complete, languages, word_count, chapters,\
                               comments, kudos, bookmarks, hits)))
    df.columns = ['标题', '作者', 'ID', '更新日期', '评级', '标签', '简介',\
                                  '完成与否', '语言', '字数', '章节数',\
                                   '评论数', 'Kudo数', '书签数', '点击数']
    df['Kudo点击比'] = df['Kudo数']/df['点击数']
    df = df.fillna(0)
    df['Kudo点击比'] = df['Kudo点击比'].apply(lambda x: round(x,3))
    df['更新日期'] = pd.to_datetime(df['更新日期'])
    return df

def display(data):
    gb = GridOptionsBuilder.from_dataframe(data)
    gb.configure_pagination(paginationAutoPageSize=True) #Add pagination
    gb.configure_side_bar() #Add a sidebar
#     gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children") #Enable multi-row selection
    gridOptions = gb.build()

    grid_response = AgGrid(
        data,
        gridOptions=gridOptions,
        data_return_mode='AS_INPUT', 
        update_mode='MODEL_CHANGED', 
        fit_columns_on_grid_load=True,
        theme='blue', #Add theme color to the table
        enable_enterprise_modules=True,
        autoHeight=True,
        width='100%',
        reload_data=True
    )

    data = grid_response['data']
    selected = grid_response['selected_rows'] 
    df = pd.DataFrame(selected)
    if len(df) == 1:
        selected_id = df.loc[0,'ID']
#     if len(df) > 1:
#         st.markdown('<p style="color:Red;">如需搜索选中ID，请勿多选</p>', unsafe_allow_html=True)

def update_file(content):
    g = Github(st.secrets["github"])
    repo = g.get_user().get_repo("ao3_request")
    all_files = []
    contents = repo.get_contents("")
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        else:
            file = file_content
            all_files.append(str(file).replace('ContentFile(path="','').replace('")',''))
    git_prefix = ''
    git_file = git_prefix + 'GGAD_test.csv'
    if git_file in all_files:
        contents = repo.get_contents(git_file)
        repo.update_file(contents.path, "committing files", content, contents.sha, branch="main")
    else:
        repo.create_file(git_file, "committing files", content, branch="main")
    
    
st.markdown('### 默认数据（更新于2022年五月）')
data= pd.read_csv('GGAD_test.csv', index_col=0) 

st.write("*注意：实时更新会耗费大约1分钟时间*")
if st.button('实时更新'):
    with st.spinner("Processing..."):
        data = scrape()
    st.success("更新完成！")
    display(data)
    data.to_csv('GGAD_test.csv')
    with open('GGAD_test.csv', 'r') as file:
        content = file.read()
    update_file(content)
else:
    display(data)

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
try: 
    selected_id
    work_id = text_field("archiveofourown.org/works/",selected_id)
except:
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
        
