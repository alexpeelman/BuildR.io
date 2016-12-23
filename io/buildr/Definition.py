import os, subprocess, json, logging
import Util
from jinja2 import Environment, FileSystemLoader


class Definition(object):
    FILE_NAME = "buildr.json"
    BUILD = "build"
    COMMAND = "command"
    PROJECT = "project"
    NAME = "name"
    VERSION = "version"
    REPOSITORIES = "repositories"
    RESOLVE = "resolve"
    REVISION = "revision"
    RESULT = "result"
    DEPENDENCIES = "dependencies"
    FOLDER = "folder"

    def __init__(self, path=os.getcwd()):
        os.chdir(path)
        logging.info("[cwd] %s", os.getcwd())

        self.path = path
        self.file = path + "/" + Definition.FILE_NAME
        self.properties = self.__readFile__(self.file)
        self.__version__()
        self.__generateProperties__()

    def __readFile__(self, path):
        logging.debug("[load definition] %s", path)

        try:
            with open(path) as data_file:
                return json.load(data_file)
        except IOError as e:
            logging.error("Error while loading %s : %s", path, e.strerror)
            raise e

    def __generateProperties__(self):
        env = Environment(loader=FileSystemLoader(self.path))
        template = env.get_template(Definition.FILE_NAME)
        rendered_template = template.render(self.properties)

        try:
            new_properties = json.loads(rendered_template)
            self.properties = Util.merge_dicts(self.properties, new_properties)
            logging.debug("[properties] : %s", self.properties)
        except ValueError as e:
            logging.error("Failed to parse JSON %s from template content\n %s", e, rendered_template)

    def __version__(self):
        version = self.__run_command__(
            self.properties[Definition.PROJECT][Definition.VERSION][Definition.COMMAND],
        )

        self.properties[Definition.PROJECT][Definition.VERSION][Definition.RESULT] = version
        logging.info("[version] %s", version)

    def __revision__(self):
        revision = self.__run_command__(
            self.properties[Definition.PROJECT][Definition.REVISION][Definition.COMMAND],
        )

        self.properties[Definition.PROJECT][Definition.REVISION][Definition.RESULT] = revision
        logging.info("[revision] %s", revision)

    def __resolveOrBuild__(self):
        resolved = True

        for repository in self.properties[Definition.REPOSITORIES]:
            logging.info("[resolve] %s", repository[Definition.NAME])
            command = repository[Definition.RESOLVE]
            try:
                self.__run_command__(command)
            except Exception as e:
                logging.error("Error while resolving %s via %s : %s", self.get_project_name(), command, e)
                resolved = False

        if not resolved:
            self.__build__()

    def __build__(self):
        self.__handle_dependencies__();

        logging.info("[build] %s", self.get_project_name())
        self.__run_command__(self.properties[Definition.BUILD][Definition.COMMAND])

    def __run_command__(self, command):
        return Util.run_command(command)

    def __handle_dependencies__(self):
        if not self.properties.has_key(Definition.DEPENDENCIES):
            logging.info("[dependency management] %s has no dependencies", self.get_project_name())
            return

        logging.info("[dependency management] %s", self.get_project_name())
        for dependency in self.properties[Definition.DEPENDENCIES]:
            self.__handle_dependency__(dependency)

    def __handle_dependency__(self, dependency):
        command = dependency[Definition.RESOLVE]
        folder = dependency[Definition.FOLDER]
        buildr = dependency[Definition.FOLDER] + "/" + Definition.FILE_NAME
        cwd = os.getcwd()

        try:
            logging.info("[verify] %s", folder)
            if os.path.isdir(folder):
                logging.info("[exists] %s", folder)
            else:
                logging.info("[resolve] %s", folder)
                self.__run_command__(command)

            logging.info("[verify] %s", buildr)
            if os.path.isfile(buildr):
                logging.info("[build node] %s", buildr)
                Definition(folder).build()
            else:
                logging.warning("[leave node] %s", folder)

        except Exception as e:
            logging.error("[error %s] could not resolve %s %s", self.get_project_name(), command, e)
            raise e
        finally:
            os.chdir(cwd)

    def get_project_name(self):
        return self.properties[Definition.PROJECT][Definition.NAME] + " " + \
               self.properties[Definition.PROJECT][Definition.VERSION][Definition.RESULT]

    def build(self):
        logging.info("[project] %s", self.get_project_name())
        self.__revision__()
        self.__resolveOrBuild__()

    def properties(self):
        return self.properties
