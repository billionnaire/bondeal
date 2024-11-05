from django.shortcuts import render
import requests
from bs4 import BeautifulSoup


def get_content(product):
    USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 "
                  "Safari/537.36")
    LANGUAGE = "en-US,en;q=0.5"
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT
    session.headers['Accept-Language'] = LANGUAGE
    session.headers['Content-Language'] = LANGUAGE
    html_content = session.get(f'https://www.jumia.ci/catalog/?q={product}').text
    return html_content


def home(request):
    product_info_list = []

    if 'product' in request.GET:
        product = request.GET.get('product')
        html_content = get_content(product)
        soup = BeautifulSoup(html_content, 'html.parser')

        product_items = soup.find_all('article', class_='prd _fb col c-prd')

        for item in product_items:
            name_tag = item.find('h3', class_='name')
            price_tag = item.find('div', class_='prc')
            img_c_div = item.find('div', class_='img-c')
            img_tag = img_c_div.find('img', class_='img') if img_c_div else None
            stars_div = item.find('div', class_='stars _s')
            rating_div = stars_div.find('div', class_='in') if stars_div else None
            link_tag = item.find('a', class_='core')  # Récupérer le lien d'achat

            if name_tag and price_tag and img_tag and rating_div and link_tag:
                name = name_tag.text
                price = price_tag.text
                img_url = img_tag.get('data-src', '') if img_tag else ''
                product_url = f"https://www.jumia.ci{link_tag['href']}"  # Construire l'URL complète

                style_attribute = rating_div.get('style', '')
                width_value = style_attribute.split(':')[1].replace('%', '').strip()
                rating = f'{float(width_value) / 20:.1f}'

                product_info = {
                    'name': name,
                    'price': price,
                    'image_url': img_url,
                    'rating': rating,
                    'product_url': product_url  # Ajouter l'URL d'achat
                }

                product_info_list.append(product_info)

    return render(request, 'core/home.html', {'product_info_list': product_info_list})
