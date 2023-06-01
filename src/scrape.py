import yaml
import requests
import urllib3
import os

gotenberg_url = 'http://gotenberg:3000'


def download_as_pdf(url, file):
    data, header = urllib3.encode_multipart_formdata({
        "url": url,
    })
    request = requests.post(
        gotenberg_url + '/forms/chromium/convert/url',
        data=data,
        headers={'Content-Type': header}
    )

    if request.status_code == 200:
        with open(file, 'wb') as f:
            f.write(request.content)
    else:
        print(request.content)


def sanitize_path(file):
    # replace space with _ and lower case
    return file.replace(' ', '_').lower()


def scrape():
    # load yaml file
    file = open("database.yml")
    database = yaml.load(file, Loader=yaml.FullLoader)
    for row in database['products']:
        for i, website in enumerate(row['websites']):
            filename = sanitize_path(row['name'] + '_' + str(i + 1) + '.pdf')
            if not os.path.exists('data/' + filename):
                print('Downloading PDFs for' + row['name'] + ' ...')
                download_as_pdf(website, 'data/' + filename)
                print('Finished downloading PDF to: ' + filename)
            else:
                print('PDF ' + filename + ' already exists')
