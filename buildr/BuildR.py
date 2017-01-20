import sys, os, logging, coloredlogs
import pkg_resources
from Options import Options
from Definition import Definition

__version__ = '0.0.1a1'


class BuildR(object):
    def __init__(self, options):
        self.options = options

        if self.options.directory() is None:
            self.definition = Definition(self.options)
        else:
            self.definition = Definition(self.options, path=self.options.directory())

    def build(self):
        self.definition.build()
        return self.definition


def print_ascii_art(path):
    ascii_file = pkg_resources.resource_filename('BuildR', 'ascii.txt')
    f = open(ascii_file, 'r')  # open file in read mode
    data = f.read()  # copy to a string
    f.close()  # close the file
    print data


def main():
    print_ascii_art(os.path.dirname(sys.argv[0]))
    options = Options(sys.argv[1:])

    if options.version():
        print "Version " + __version__
        sys.exit(0)

    logging.basicConfig(stream=sys.stdout, level=options.loglevel())
    coloredlogs.install(level=options.loglevel())
    logging.getLogger('BuildR')
    logging.info("Running BuildR")

    buildR = BuildR(options)
    definition = buildR.build()
    logging.info("[metadata] %s", definition.metadata.dependencies)
    logging.info("BuildR done !")


if __name__ == '__main__':
    main()
