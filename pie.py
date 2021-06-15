import json
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from numpy import byte_bounds
import requests 
import os.path
import pathlib

def get_image_location(card_name: str):
    image_name = card_name.lower().replace(' ', '_') + '.jpg'
    return f'deck_images/{image_name}'

def download_card_image(card_name: str, download_location: str):
    print(f'INFO: searching for card images for {card_name}')
    r = requests.get("https://db.ygoprodeck.com/api/v7/cardinfo.php", 
    params={'fname': card_name})
    try:
        data = r.json()['data']
        img_url = data[0]['card_images'][0]['image_url']
    except:
        raise Exception(f'ERROR: Unable to find a card image for {card_name}')

    print(f'INFO: found image for {card_name}')
    
    print(f'INFO: downloading image {card_name}')
    img_request = requests.get(img_url)

    with open(download_location, 'wb') as file:
        file.write(img_request.content)
    img_request.close()
    print(f'INFO: downloaded to {download_location}')

def get_image(card_name: str):
    image_location = get_image_location(card_name)
    if not os.path.exists(image_location):
        download_card_image(card_name, image_location)
    image= plt.imread(image_location, format='jpg')
    image = image[110:400,45:375] # crops to the image and not card text and stuff
    return image

# loading configs
with open('deck.json', 'r') as file:
    config = json.load(file)
pathlib.Path('deck_images').mkdir(exist_ok=True)

CHART_TITLE = config['title']
DECK_INFOS = config['decks']
PIE_OUTLINE_COLOR = config.get('pie_outline_color') or 'black'
BACKGROUND = config.get('background') or ''
ZOOM_LEVEL = config.get('zoom_level') or .72

# computing/formating data/labels
def compute_data(deck_infos):
    total = []
    labels = []
    pictures = []
    for deck_name, deck_stat in deck_infos.items():
        total.append(deck_stat['count'])
        labels.append(deck_name)
        pictures.append(deck_stat['card'])
    return [total, labels, pictures]

total, labels, pictures = compute_data(DECK_INFOS)
total_sum = sum(total)
percentages = [t/total_sum * 100 for t in total]
labels = ['{0} ({2}, {1:1.0f}%)'.format(label, percentage,t) for label, percentage,t in zip(labels, percentages, total)]


plt.title(CHART_TITLE)

plt.gca().axis("equal")
wedges,text = plt.pie(total, labels=labels, radius=1,
                        wedgeprops = { 
                            'linewidth': 4,
                            "edgecolor" :PIE_OUTLINE_COLOR,
                            "fill":False})


def img_to_pie( image, wedge, xy, zoom=1, ax = None):
    if ax==None: ax=plt.gca()
    path = wedge.get_path()
    patch = PathPatch(path, facecolor='none')
    ax.add_patch(patch)
    imagebox = OffsetImage(image, zoom=zoom, clip_path=patch, zorder=-10)
    ab = AnnotationBbox(imagebox, xy, xycoords='data', pad=0, frameon=False)
    ax.add_artist(ab)



for i in range(len(total)):
    image = get_image(pictures[i])
    img_to_pie(image, wedges[i], xy=(0,0), zoom=ZOOM_LEVEL)
    wedges[i].set_zorder(10)

plt.savefig('pie.png', bbox_inches='tight')