import sys, logging, coloredlogs
from Options import Options
from Definition import Definition


class BuildR(object):
    def __init__(self, argv):
        self.options = Options(argv)

        if self.options.directory() is None:
            self.definition = Definition(self.options)
        else:
            self.definition = Definition(self.options, self.options.directory())

    def build(self):
        self.definition.build()
        return self.definition


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    logging.getLogger('BuildR')
    coloredlogs.install(level=logging.DEBUG)

    logging.info("Running BuildR")
    buildR = BuildR(sys.argv[1:])
    definition = buildR.build()
    logging.info(definition.metadata.dependencies)
