import argparse
import logging


class Options(object):
    def __init__(self, args):
        self.parser = argparse.ArgumentParser()
        build_group = self.parser.add_mutually_exclusive_group()

        self.parser.add_argument("-d", "--directory",
                                 help="Build directory to start from. The directory must contain a buildr.json file",
                                 default=".")
        self.parser.add_argument("-c", "--config",
                                 help="A JSON config file that will be used for variable substitution during buildr.json processing. "
                                      "This file overrides environment variables.",
                                 default=None)
        self.parser.add_argument("-p", "--publish",
                                 help="Publish the build results to the repositories.",
                                 action="store_true")
        self.parser.add_argument('-v', '--verbose',
                                 help="Print lots of debugging statements ",
                                 action="store_const", dest="loglevel", const=logging.DEBUG, default=logging.INFO,
                                 )
        self.parser.add_argument("-n", "--skip-build",
                                 help="Skip builds but generate metadata.",
                                 action="store_true")
        self.parser.add_argument("-Y", "--YOLO", "--skip-dependency-checking",
                                 help="Skip dependency checks. Otherwise it is assured that occurrences of different versions "
                                      "of the same project will raise an exception. ",
                                 action="store_true", dest="skip_dependency_checking")
        # self.parser.add_argument("-ar", "--allowed-repositories",
        #                          help="A comma separated list of repository names to resolve binaries from eg. repo-x, repo-y. "
        #                               "Fails when no match exists in the repositories section of buildr.json")
        build_group.add_argument("-s", "--source-build",
                                 help="Force builds from source code. Skips binary resolving",
                                 action="store_true")
        build_group.add_argument("-b", "--binary-build",
                                 help="Force builds from binaries. Skips source builds and fails when binaries are missing. "
                                      "Applies only to dependencies, the root project is build from source after all "
                                      "binaries are resolved",
                                 action="store_true")
        build_group.add_argument("-r", "--skip-source-resolving",
                                 help="Skip source resolving. Fetches buildr.json files but does not resolve sources. Useful for exploring "
                                      "definitions and building metadata without getting distracted.",
                                 action="store_true")
        build_group.add_argument("--version",
                                 help="Show the version number and exit",
                                 action="store_true")

        self.values = self.parser.parse_args(args)
        logging.info("[options] %s", self.values)

    """
    Returns the directory to build from, defaults to '.'
    """

    def directory(self):
        return self.values.directory

    """
    Returns True when build results must be published to the defined repositories otherwise False
    """
    def publish(self):
        return self.values.publish

    """
    Returns True if source builds are requested, otherwise False
    """

    def source_build(self):
        return self.values.source_build

    """
    Returns True if binary builds are requested, otherwise False
    """

    def binary_build(self):
        return self.values.binary_build

    """
    Returns True if metadata should be generated but no builds should be executed, otherwise False
    """

    def skip_build(self):
        return self.values.skip_build

    """
    Returns true if no dependency checking must be performed, otherwise false.
    """

    def skip_dependency_checking(self):
        return self.values.skip_build

    """
    Returns an array of 'allowed' repository names to use when resolving binaries.
    When empty all repositories should be allowed.
    """

    def resolve_binaries_from(self):
        return self.values.skip_build

    def loglevel(self):
        return self.values.loglevel

    def version(self):
        return self.values.version

    def skip_source_resolving(self):
        return self.values.skip_source_resolving or self.values.binary_build

    def config_file(self):
        return self.values.config
