import boto3
import configparser
import os
import sys
import botocore
import templates


def init_config():
    config = configparser.ConfigParser()
    config.read(os.path.expanduser('./cloudphotorc.ini'))
    return config['DEFAULT']


session = boto3.session.Session()
bucket_name = 'vvot14'
s3 = session.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net'
)

s3_client = session.client(
    service_name='s3',
    endpoint_url=init_config()['endpoint_url'],
    aws_access_key_id=init_config()['aws_access_key_id'],
    aws_secret_access_key=init_config()['aws_secret_access_key'],
)
s3_resource = session.resource(
    service_name='s3',
    endpoint_url=init_config()['endpoint_url'],
    aws_access_key_id=init_config()['aws_access_key_id'],
    aws_secret_access_key=init_config()['aws_secret_access_key'],
)


def init():
    print('Input aws_access_key_id: ', end='')
    aws_access_key_id = input()
    print('Input aws_secret_access_key: ', end='')
    aws_secret_access_key = input()
    print('Input bucket: ', end='')
    bucket = input()
    config = configparser.ConfigParser()
    config['DEFAULT'] = {
        'bucket': bucket,
        'aws_access_key_id': aws_access_key_id,
        'aws_secret_access_key': aws_secret_access_key,
        'endpoint_url': 'https://storage.yandexcloud.net',
        'region': 'ru-central1'
    }
    with open(os.path.expanduser('./cloudphotorc.ini'), mode='w') as f:
        config.write(f)


def upload(album, path):
    if os.path.exists(path):
        if len(os.listdir(path)) == 0:
            for photo in os.listdir(path):
                if photo.endswith('.jpg') or photo.endswith('.jpng'):
                    try:
                        s3_client.upload_file(os.path.join(path, photo), bucket_name, album + '/' + photo)
                    except:
                        print('error')
        else:
            print('No files in album', file=sys.stderr)
    else:
        print('Directory does not exist', file=sys.stderr)


def download(album, path):
    photos = s3_resource.Bucket(bucket_name).objects.filter(Prefix=album + '/')
    if len([photo for photo in photos]) == 0:
        if os.path.exists(path):
            for photo in photos:
                s3_client.download_file(bucket_name, photo.key, os.path.join(path, photo.key.split('/')[1]))
        else:
            print('Directory does not exist', file=sys.stderr)
    else:
        print('No files in album', file=sys.stderr)


def list_albums(album):
    if album is None:
        albums = s3_resource.Bucket(bucket_name).objects.all()
        albums = [obj for obj in albums]
        albums = set(
            map(lambda name: name[0],
                filter(lambda arr: len(arr) > 1,
                       map(lambda o: o.key.split('/'), albums))
                )
        )
        if not len(albums) == 0:
            for alb in albums:
                print(alb)
        else:
            print('No albums', file=sys.stderr)
    else:
        photos = s3_resource.Bucket(bucket_name).objects.filter(Prefix=album + '/')
        photos = [photo for photo in photos]
        if not len(photos) == 0:
            for photo in photos:
                print(photo)
        else:
            print('No photos in this album', file=sys.stderr)


def delete(album, photo):
    ph = s3_resource.Object(bucket_name, album + '/' + photo)
    try:
        ph.load()
        ph.delete()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print('Photo not found', file=sys.stderr)


def make_site():
    photos = s3_resource.Bucket(bucket_name).objects.all()
    photos = [photo for photo in photos]
    photos = set(map(lambda name: name[0], filter(lambda arr: len(arr) > 1, map(lambda o: o.key.split('/'), photos))))

    res_str = ''
    for i, a in enumerate(photos):
        res_str += templates.album_list_e.format(n=i, name=a)
    index = templates.index_template.format(album_list=res_str)
    s3_client.put_object(Bucket=bucket_name, Key='index.html', Body=index)

    s3_client.put_object(Bucket=bucket_name, Key='error.html', Body=templates.error_template)

    for i, album in enumerate(photos):
        photos_ = s3_resource.Bucket(bucket_name).objects.filter(Prefix=album + '/')
        photos_ = list(photos_)
        photo_list = ''
        for photo in photos_:
            photo_list += templates.photo_list_e.format(url=photo.key, name=photo.key)
        album_page = templates.album_template.format(photo_list=photo_list)
        s3_client.put_object(Bucket=bucket_name, Key=f'album{i}.html', Body=album_page)

    website_configuration = {
        'ErrorDocument': {'Key': 'error.html'},
        'IndexDocument': {'Suffix': 'index.html'},
    }
    s3_client.put_bucket_website(Bucket=bucket_name, WebsiteConfiguration=website_configuration)
    s3_resource.BucketAcl(bucket_name).put(ACL='public-read')