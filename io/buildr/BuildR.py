import sys, getopt, logging, coloredlogs
from Definition import Definition


class BuildR(object):
    def __init__(self, argv):
        self.__parseOptions__(argv)

        try:
            self.definition
        except AttributeError:
            self.definition = Definition()

    def __parseOptions__(self, argv):
        try:
            opts, args = getopt.getopt(argv, "d:", ["directory="])
        except getopt.GetoptError:
            logging.error("Option parsing failed")
            sys.exit(-1)

        for opt, arg in opts:
            logging.debug("Handling option %s %s", opt, arg)
            if opt in ('-d', "--directory"):
                self.definition = Definition(arg)

    def build(self):
        self.definition.build()


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    logging.getLogger('BuildR')
    coloredlogs.install(level=logging.DEBUG)
    logging.info("Running BuildR")
    buildR = BuildR(sys.argv[1:])
    buildR.build()
