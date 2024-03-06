from src.common.config import config_init
import argparse


def usage():
    print('Usage: python3 startup.py -c config_file')


def argsParse():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', metavar='')
    return parser.parse_args()


if __name__ == "__main__":
    args = argsParse()
    config_init(args.config)
    from src.app import main
    if args.config:
        try:
            main()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            raise e
    else:
        usage()
