from django.shortcuts import render
from django.core.paginator import Paginator
import requests
import difflib
from bs4 import BeautifulSoup

# Fonction de scraping pour Jumia
def get_content_jumia(product):
    USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 "
                  "Safari/537.36")
    LANGUAGE = "en-US,en;q=0.5"
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT
    session.headers['Accept-Language'] = LANGUAGE
    session.headers['Content-Language'] = LANGUAGE
    html_content = session.get(f'https://www.jumia.ci/catalog/?q={product}').text
    return html_content

# Fonction de scraping pour BCCShop
def get_content_bccshop(product):
    USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 "
                  "Safari/537.36")
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT
    html_content = session.get(f'https://bccshop.ci/?s={product}').text
    return html_content

# Fonction de scraping pour MrGadget
def get_content_mrgadget(product):
    USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 "
                  "Safari/537.36")
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT
    html_content = session.get(f'https://www.mrgadget.ci/public/index.php/catalogue?q={product}').text
    return html_content

# Extraction des produits de Jumia
def extract_jumia_products(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    product_info_list = []

    product_items = soup.find_all('article', class_='prd _fb col c-prd')
    for item in product_items:
        name_tag = item.find('h3', class_='name')
        price_tag = item.find('div', class_='prc')
        img_c_div = item.find('div', class_='img-c')
        img_tag = img_c_div.find('img', class_='img') if img_c_div else None
        stars_div = item.find('div', class_='stars _s')
        rating_div = stars_div.find('div', class_='in') if stars_div else None
        link_tag = item.find('a', class_='core')

        if name_tag and price_tag and img_tag and rating_div and link_tag:
            name = name_tag.text.strip()
            price = float(''.join(filter(str.isdigit, price_tag.text.strip())))
            img_url = img_tag.get('data-src', '')
            product_url = f"https://www.jumia.ci{link_tag['href']}"
            style_attribute = rating_div.get('style', '')
            width_value = style_attribute.split(':')[1].replace('%', '').strip()
            rating = f'{float(width_value) / 20:.1f}'

            product_info_list.append({
                'name': name,
                'price': price,
                'image_url': img_url,
                'rating': rating,
                'product_url': product_url,
                'source': 'Jumia'
            })

    return product_info_list

# Extraction des produits de BCCShop
def extract_bccshop_products(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    product_info_list = []

    product_items = soup.find_all('div', class_='product')
    for item in product_items:
        name_tag = item.find('h3', class_='auxshp-title-heading')
        price_tag = item.find('span', class_='woocommerce-Price-amount amount')
        img_tag = item.find('img', class_='auxshp-product-image')
        link_tag = item.find('a', class_='woocommerce-LoopProduct-link')

        if name_tag and price_tag and img_tag and link_tag:
            name = name_tag.text.strip()
            price = float(''.join(filter(str.isdigit, price_tag.text.strip())))
            img_url = img_tag.get('src', '')
            product_url = link_tag['href']
            rating = 'N/A'  # BCCShop doesn't display ratings in this structure

            product_info_list.append({
                'name': name,
                'price': price,
                'image_url': img_url,
                'rating': rating,
                'product_url': product_url,
                'source': 'BCCShop'
            })

    return product_info_list

# Extraction des produits de MrGadget
def extract_mrgadget_products(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    product_info_list = []

    product_items = soup.find_all('li', class_='product-item')
    for item in product_items:
        name_tag = item.find('h5', class_='product-item__title')
        price_tag = item.find('ins', class_='font-size-20 text-red text-decoration-none')
        img_tag = item.find('img', class_='img-fluid')
        link_tag = item.find('a', class_='d-block text-center')

        if name_tag and price_tag and img_tag and link_tag:
            name = name_tag.text.strip()
            price = float(''.join(filter(str.isdigit, price_tag.text.strip())))
            img_url = img_tag.get('src', '')
            product_url = link_tag['href']
            rating = 'N/A'  # Ratings are not available on MrGadget

            product_info_list.append({
                'name': name,
                'price': price,
                'image_url': img_url,
                'rating': rating,
                'product_url': product_url,
                'source': 'MrGadget'
            })

    return product_info_list


# Fonction pour la recherche floue avec correction d'orthographe
def search_products(products, query, threshold=0.7):
    """
    Recherche floue dans la liste des produits, avec tolérance aux erreurs d'orthographe.

    Args:
        products (list): Liste des produits avec leurs informations (nom, prix, etc.).
        query (str): Le terme de recherche.
        threshold (float): Niveau de correspondance minimum (de 0 à 1).

    Returns:
        list: Produits correspondant à la recherche, même avec des erreurs typographiques.
    """
    query_words = query.lower().split()  # Conversion du terme de recherche en minuscules et séparation des mots-clés
    filtered_products = []

    for product in products:
        product_name_words = product['name'].lower().split()  # Nom du produit en minuscules et séparation en mots

        # Vérifier chaque mot du terme de recherche pour voir s'il y a une correspondance proche
        match = all(
            any(difflib.SequenceMatcher(None, query_word, product_word).ratio() >= threshold
                for product_word in product_name_words)
            for query_word in query_words
        )

        # Ajouter le produit s'il y a correspondance
        if match:
            filtered_products.append(product)

    return filtered_products

# Vue principale pour afficher les produits avec pagination
def home(request):
    product_info_list = []

    if 'product' in request.GET:
        product = request.GET.get('product')

        # Scraping de Jumia
        jumia_html_content = get_content_jumia(product)
        product_info_list.extend(extract_jumia_products(jumia_html_content))

        # Scraping de BCCShop
        bccshop_html_content = get_content_bccshop(product)
        product_info_list.extend(extract_bccshop_products(bccshop_html_content))

        # Scraping de MrGadget
        mrgadget_html_content = get_content_mrgadget(product)
        product_info_list.extend(extract_mrgadget_products(mrgadget_html_content))

        # Trier tous les produits combinés par prix croissant
        product_info_list.sort(key=lambda x: x['price'])

    # Pagination : 12 produits par page
    paginator = Paginator(product_info_list, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/home.html', {'page_obj': page_obj})
