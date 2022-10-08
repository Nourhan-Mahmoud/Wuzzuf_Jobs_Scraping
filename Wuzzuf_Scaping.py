import streamlit as st
from streamlit_lottie import st_lottie
st.set_page_config(page_title = 'Wuzzuf Jobs' , page_icon = ':star:')

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

import requests
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time
import math

# Wuzzuf Scraping

main_url = 'https://wuzzuf.net/search/jobs/?a=hpb%7Cspbg&q='
browser = webdriver.Chrome('C:\\Users\\User\\Downloads\\chromedriver.exe')

def get_first_pageLink_for_that_job(job_title):
    job_title_words = job_title.split(" ")
    if len(job_title_words)==1:
        page_link = main_url + job_title_words[0]
    else :
        page_link = main_url
        for i in job_title_words:
            page_link = page_link + i
            page_link = page_link + '%20'
    
    page_link = page_link + '&start='
    return page_link

def get_urls_wuzzuf(urlPerPage):
    
    request = requests.get(urlPerPage).text
    soup = BeautifulSoup(request)
    
    links = []
    for a in soup.find_all('a',attrs={'class':'css-o171kl'}):
        links.append(a['href'])
        
    linksPerPage = []
    wuzzuf_path = 'https://wuzzuf.net'
    for i in links:
        if i[:5] == '/jobs':
            linksPerPage.append((wuzzuf_path+i))
            
    return linksPerPage

def get_job_detailed(urlPerPage,n_jobs):

    request = requests.get(urlPerPage).text
    soup = BeautifulSoup(request)

    job_titles = []
    for a in soup.find_all('h2',attrs={'class':'css-m604qf'}):
        job_titles.append(a.text)

    company_name = [] 
    for a in soup.find_all('a',attrs={'class':'css-17s97q8'}):
        company_name.append(a.text)

    location = [] 
    for a in soup.find_all('span',attrs={'class':'css-5wys0k'}):
        location.append(a.text)

    job_type = [] 
    for a in soup.find_all('span',attrs={'class':'css-1ve4b75 eoyjyou0'}):
        job_type.append(a.text)

    job_level = [] 
    for a in soup.find_all('div',attrs={'class':'css-o171kl'}):
        job_level.append(a.text)

    details = [] 
    for a in soup.find_all('div', attrs = {'class','css-y4udm8'}):
        details.append(a.text)

    yrs_exp = []
    skills = []
    for i in details:
        li = i.split('·')
        yrs_exp.append(li[1])
        x = "*".join(li[2:])
        skills.append(x)

    return job_titles[:int(n_jobs)],company_name[:int(n_jobs)],location[:int(n_jobs)],job_type[:int(n_jobs)],yrs_exp[:int(n_jobs)],skills[:int(n_jobs)]



def get_all_links_for_that_job(job_title,n_jobs):
    page_url = get_first_pageLink_for_that_job(job_title)
    n = math.ceil(int(n_jobs) / 15)
    links = []
    for i in range(n):
        url = page_url+str(i)
        u = get_urls_wuzzuf(url)
        links.extend(u)

    org_links = links[:int(n_jobs)].copy()
    return org_links

def get_job_descrip_Req(link):
    
    browser.get(link)
    
    des = browser.find_elements(By.XPATH,'//*[@id="app"]/div/main')
    job = des[0].text
        
    return job



def get_description_requirments(links):
    
    descriptions = []
    requirments = []

    for i in links:
        jd = get_job_descrip_Req(i)
        job = jd
        #Clean as i can
        x = job.split('\nFeatured Jobs\n')

        w = x[0].split('\nJob Description\n')

        desc_req = w[1].split('\nJob Requirements\n')

        job_des = desc_req[0].split('\n')

        try:
            job_req = desc_req[1].split('\n')
        except:
            job_req = job_des

        des = "*".join(job_des)
        req = "*".join(job_req)

        descriptions.append(des)
        requirments.append(req)
    return descriptions,requirments

def jobs_data_frame(job_titles,company_name,location,job_type,yrs_exp,skills,descriptions,requirments,n_jobs):
    cnt = int(n_jobs)
    df = pd.DataFrame({'job_title':job_titles[:cnt],
                       'Company_name':company_name[:cnt] , 
                       'Location':location[:cnt]  , 
                       'Job_Type':job_type[:cnt],
                       'Years_Of_Experience':yrs_exp[:cnt],
                       'Skills':skills[:cnt] ,
                       'Job_Description':descriptions[:cnt]
                       ,'Job_Requirment':requirments[:cnt]})
    return df


def clean_df(df):
    jobs_df['Company_name'] = jobs_df['Company_name'].apply(lambda x : x.strip('-'))
    country = []
    state = []
    city = []
    import numpy as np
    for i in jobs_df['Location']:
        l = i.split(',')
        if len(l) >= 3:
            country.append(l[-1])
            state.append(l[-2])
            city.append(l[-3])
        elif len(l)==2:
            country.append(l[-1])
            state.append(l[-2])
            city.append(np.nan)
        else:
            country.append(l[-1])
            state.append(np.nan)
            city.append(np.nan)

    jobs_df['Country'] = country
    jobs_df['State'] = state
    jobs_df['City'] = city

    jobs_df.drop(columns = ['Location'],inplace = True)
    
    jobs_df['Years_Of_Experience'] = jobs_df['Years_Of_Experience'].apply(lambda x: x.replace('Yrs of Exp', ''))
    jobs_df['Skills'] = jobs_df['Skills'].apply(lambda x: x.replace(' * ',','))
    
    for i in range(jobs_df.shape[0]):
        if jobs_df['Job_Description'][i] == jobs_df['Job_Requirment'][i]:
            x = jobs_df['Job_Description'][i].split('*Similar Jobs*')[0]
            l = x.split('** Job Requirements*')
            l1 = l[0].replace('*','\n')
            l2 = l[1].replace('*','\n')
            jobs_df['Job_Description'][i] = l1
            jobs_df['Job_Requirment'][i] = l2
    return jobs_df


def get_lat_long_from_country(jobs_df):
    # Import the required library
    from geopy.geocoders import Nominatim

    # Initialize Nominatim API
    geolocator = Nominatim(user_agent="MyApp")

    lat = []
    long = []
    for i in range(jobs_df.shape[0]):
        location = geolocator.geocode(jobs_df['Country'][i])
        lat.append(location.latitude)
        long.append(location.longitude)

    jobs_df['latitude'] = lat
    jobs_df['longitude'] = long
    return jobs_df

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------







def load_lottie(url):
    r = requests.get(url)
    if r.status_code != 200:
       return None
    return r.json()


lotti_coding = load_lottie('https://assets9.lottiefiles.com/packages/lf20_8DJAlf.json')  

with st.container():
    st.write('Scraping Jobs From Wuzzuf For Learning Purpose :blush:')
    st.write('---')

job_title = None
n_jobs = None


page_link = None
links_per_page = None
job_links = None
jobs_df = None

with st.container():
    left_col,right_col = st.columns(2)
    with left_col:
        st.header('Wuzzuf Jobs')
        st.write('#')
        job_title = st.text_input('Job Title: ')
        n_jobs = st.text_input('Number Of Jobs ')

    with right_col:
        st_lottie(lotti_coding, height=300,width=300,key = 'coding')

final_df = None
df = None


with st.container():
    if st.button('Display Jobs'):
        page_link = get_first_pageLink_for_that_job(job_title)
        links_per_page = get_urls_wuzzuf(page_link)
        job_links = get_all_links_for_that_job(job_title, n_jobs)
        job_titles,company_name,location,job_type,yrs_exp,skills = get_job_detailed(page_link,n_jobs)
        descriptions,requirments = get_description_requirments(job_links)
        jobs_df = jobs_data_frame(job_titles,company_name,location,job_type,yrs_exp,skills,descriptions,requirments,n_jobs)
        final_df = clean_df(jobs_df)
        df = get_lat_long_from_country(final_df)
        st.dataframe(df)

    
st.write('---')

    
            
    
    