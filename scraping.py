from bs4 import BeautifulSoup
import requests
import pandas as pd

def main():

    data_dic = {'sector':[],'n_jobs':[]}

    page = requests.get('https://es.wikipedia.org/wiki/Cristiano_Ronaldo')
    html_soup = BeautifulSoup(page.content, 'html.parser')

    panel = html_soup.find('div',{'id' : 'mw-content-text'})
    parrafo = panel.find('p').text
    print(parrafo,'\n')
'''
    for li in panel.find_all('p'):
        link = li.find('a')['href']
        sector = li.find('a').text
        print(li)
        print("Sector: ", sector)
        print("Link: ", link)

        page_inner = requests.get('https://www.michaelpage.es'+link)
        html_soup_inner = BeautifulSoup(page_inner.content, 'html.parser')

        n_offers = html_soup_inner.find('span',{'class':'total-search no-of-jobs'}).text
        print('Nº offers: ',n_offers,'\n')

        data_dic['sector'].append(sector)
        data_dic['n_jobs'].append(int(n_offers))

    df = pd.DataFrame().from_dict(data_dic)
    print(df)
'''
if __name__ == '__main__':
    main()