import os
import json
import logging
import Util
from Metadata import Metadata
from ProjectDefinition import ProjectDefinition
from jinja2 import Environment, FileSystemLoader, DictLoader, Template, StrictUndefined, UndefinedError


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

    def __init__(self, options, metadata=Metadata(), path=os.getcwd()):
        os.chdir(path)
        logging.info("[cwd] %s", os.getcwd())

        self.options = options
        self.project_definition = None
        self.metadata = metadata
        self.path = os.getcwd()
        # self.file = path + "/" + Definition.FILE_NAME
        self.properties = self.__readFile__(Definition.FILE_NAME)
        self.__version__()
        self.__revision__()
        self.__generateProperties__()
        self.__verify_project__versioning__()

    def __verify_project__versioning__(self):
        other_versions = self.metadata.get_dependencies_with_different_version(self.get_project_definition())

        if not self.options.skip_dependency_checking() and other_versions:
            logging.error("[version mismatch] The same project with another version has been encountered %s", other_versions)
            raise ValueError("Version mismatch encountered for %s, other versions %s. Please verify build dependencies.",
                             self.get_project_definition(),
                             other_versions)

    def __readFile__(self, path):
        logging.debug("[load definition] %s", path)

        try:
            with open(path) as data_file:
                return json.load(data_file)
        except ValueError as e:
            logging.error("[error] Invalid JSON %s/%s : %s", self.path, path, e)
            raise e
        except IOError as e:
            logging.error("[error] Problem while loading %s : %s", path, e.strerror)
            raise e

    def __generateProperties__(self):
        logging.debug(os.getcwd())

        try:
            env = Environment(loader=FileSystemLoader(self.path), undefined=StrictUndefined)
            template = env.get_template(Definition.FILE_NAME)
            rendered_template = template.render(self.properties)
        except UndefinedError as e:
            logging.error("Failed to resolve variable : %s", e.message)
            raise e

        number_of_variables = rendered_template.count("{{")

        while number_of_variables > 0:
            try:
                new_properties = json.loads(rendered_template)
                self.properties = Util.merge_dicts(self.properties, new_properties)
                logging.debug("[properties] : %s", self.properties)

                # keep resolving until all variables are gone
                properties_as_json = json.dumps(self.properties)
                rendered_template = Template(properties_as_json).render(self.properties)
                left_over_number_of_variables = rendered_template.count("{{")

                if left_over_number_of_variables >= number_of_variables:
                    raise ValueError("Unable to resolve all properties, please check your %s file: %s",
                                     Definition.FILE_NAME,
                                     rendered_template)

                number_of_variables = left_over_number_of_variables
                self.properties = json.loads(rendered_template)
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

    def __resolve_or_build__(self):
        source_build_requested = self.options.source_build()
        binary_build_requested = self.options.binary_build()

        if binary_build_requested:
            for repository in self.properties[Definition.REPOSITORIES]:
                logging.info("[resolve] %s", repository[Definition.NAME])
                command = repository[Definition.RESOLVE]
                try:
                    self.__run_command__(command)
                except ValueError as e:
                    logging.error("Error while resolving %s via %s : %s", self.get_project_definition(), command, e)
                    if binary_build_requested:
                        logging.debug("[resolve] binary build requested, raising error and aborting build %s",
                                      self.get_project_definition())
                        raise e
                    else:
                        logging.debug("[resolve] forcing source build of %s", self.get_project_definition())
                        source_build_requested = True

        elif source_build_requested or not binary_build_requested:
            self.__build__()

    def __build__(self):
        self.__handle_dependencies__()

        skip_build = self.options.skip_build()
        if not skip_build:
            logging.info("[build] %s", self.get_project_definition())
            self.__run_command__(self.properties[Definition.BUILD][Definition.COMMAND])
        else:
            logging.info("[build] skipping build %s", self.get_project_definition())

    def __run_command__(self, command):
        return Util.run_command(command)

    def __handle_dependencies__(self):
        if not self.properties.has_key(Definition.DEPENDENCIES):
            logging.info("[dependency management] %s has no dependencies", self.get_project_definition())
            return

        logging.info("[dependency management] %s", self.get_project_definition())
        for dependency in self.properties[Definition.DEPENDENCIES]:
            self.__handle_dependency__(dependency)

    def __handle_dependency__(self, dependency):
        command = dependency[Definition.RESOLVE]
        folder = dependency[Definition.FOLDER]
        buildr = dependency[Definition.FOLDER] + "/" + Definition.FILE_NAME
        cwd = os.getcwd()

        try:
            logging.info("[verify] %s", folder)
            if os.path.isdir(folder) and os.listdir(folder):
                logging.info("[exists] %s", folder)
            else:
                logging.info("[resolve] %s", folder)
                self.__run_command__(command)

            logging.info("[verify] %s", buildr)
            if os.path.isfile(buildr):
                logging.info("[build node] %s", buildr)
                definition = Definition(self.options, path=folder, metadata=self.metadata)
                definition.build()
                self.metadata.add_dependency(definition.get_project_definition())
            else:
                logging.warning("[dependency node] %s", folder)

        except Exception as e:
            logging.error("[error %s] could not resolve %s %s", self.get_project_definition(), command, e)
            raise e
        finally:
            os.chdir(cwd)

    def __generate_metadata__(self):
        # todo write to metadata file
        for project in self.metadata.dependencies:
            logging.debug("%s", project)

    def get_project_definition(self):
        if not self.project_definition:
            self.project_definition = ProjectDefinition(
                self.properties[Definition.PROJECT][Definition.NAME],
                self.properties[Definition.PROJECT][Definition.VERSION][Definition.RESULT],
                self.properties[Definition.PROJECT][Definition.REVISION][Definition.RESULT],
            )

        return self.project_definition

    def build(self):
        logging.info("[project] %s", self.get_project_definition())
        self.__resolve_or_build__()
        self.__generate_metadata__()

    def properties(self):
        return self.properties
