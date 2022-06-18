import logging

from mm2.controller import Controller

if __name__ == "__main__":
    logging.basicConfig(filename='error.log',
                        level=logging.DEBUG,
                        format='(%(asctime)s %(levelname)s %(name)s %(message)s')

    try:
        counter = Controller()
    except Exception:
        logging.getLogger(__name__).exception('')