import argparse
import sys
import cloud_photo


def main():
    parser = argparse.ArgumentParser(description='Cloud photo gallery.')
    parser.add_argument('command')
    parser.add_argument('--album', default=None)
    parser.add_argument('--photo')
    parser.add_argument('--path', default='.')
    args = parser.parse_args()
    if args.command == 'init':
        cloud_photo.init()
    elif args.command == 'upload':
        cloud_photo.upload(args.album, args.path)
    elif args.command == 'download':
        cloud_photo.download(args.album, args.path)
    elif args.command == 'list':
        cloud_photo.list_albums(args.album)
    elif args.command == 'delete':
        cloud_photo.delete(args.album, args.photo)
    elif args.command == 'mksite':
        cloud_photo.make_site()
    else:
        print('Unknown command', file=sys.stderr)
        exit(1)


if __name__ == '__main__':
    main()